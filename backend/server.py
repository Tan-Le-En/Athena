from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

SECRET_KEY = os.environ.get('SECRET_KEY', 'athena-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class BookMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    isbn: str
    title: str
    authors: List[str]
    cover_url: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    page_count: Optional[int] = None
    subjects: List[str] = []

class BookContent(BaseModel):
    isbn: str
    content: str
    source: str

class Progress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_email: str
    isbn: str
    position: float
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProgressCreate(BaseModel):
    isbn: str
    position: float

class Bookmark(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_email: str
    isbn: str
    position: float
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookmarkCreate(BaseModel):
    isbn: str
    position: float
    text: str

class Highlight(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_email: str
    isbn: str
    text: str
    color: str = "yellow"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HighlightCreate(BaseModel):
    isbn: str
    text: str
    color: str = "yellow"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email}, {"_id": 0, "password": 0})
    if user is None:
        raise credentials_exception
    
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return User(**user)

def validate_isbn(isbn: str) -> bool:
    isbn = isbn.replace("-", "").replace(" ", "")
    
    if len(isbn) == 10:
        if not isbn[:-1].isdigit():
            return False
        check = isbn[-1]
        if check == 'X':
            check = 10
        else:
            check = int(check)
        total = sum((10 - i) * int(digit) for i, digit in enumerate(isbn[:-1]))
        return (total + check) % 11 == 0
    
    elif len(isbn) == 13:
        if not isbn.isdigit():
            return False
        total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(isbn[:-1]))
        check = (10 - (total % 10)) % 10
        return check == int(isbn[-1])
    
    return False

async def fetch_book_from_openlibrary(isbn: str) -> Optional[Dict[str, Any]]:
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data")
            if response.status_code == 200:
                data = response.json()
                key = f"ISBN:{clean_isbn}"
                if key in data:
                    return data[key]
        except Exception as e:
            logging.error(f"Error fetching from Open Library: {e}")
    return None

async def fetch_book_text(isbn: str) -> Optional[str]:
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=details")
            if response.status_code == 200:
                data = response.json()
                key = f"ISBN:{clean_isbn}"
                if key in data and 'details' in data[key]:
                    details = data[key]['details']
                    if 'ocaid' in details:
                        ocaid = details['ocaid']
                        text_response = await client.get(f"https://archive.org/stream/{ocaid}/{ocaid}_djvu.txt")
                        if text_response.status_code == 200:
                            return text_response.text
        except Exception as e:
            logging.error(f"Error fetching book text: {e}")
    return None

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_dict)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    user = User(email=user_data.email, name=user_data.name)
    return TokenResponse(access_token=access_token, user=user)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    user_obj = User(email=user["email"], name=user["name"])
    return TokenResponse(access_token=access_token, user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/books/search/{isbn}", response_model=BookMetadata)
async def search_book(isbn: str):
    if not validate_isbn(isbn):
        raise HTTPException(status_code=400, detail="Invalid ISBN format")
    
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    cached_book = await db.books.find_one({"isbn": clean_isbn}, {"_id": 0})
    if cached_book:
        return BookMetadata(**cached_book)
    
    book_data = await fetch_book_from_openlibrary(clean_isbn)
    if not book_data:
        raise HTTPException(status_code=404, detail="Book not found")
    
    authors = [author['name'] for author in book_data.get('authors', [])]
    cover_url = None
    if 'cover' in book_data:
        cover_url = book_data['cover'].get('large') or book_data['cover'].get('medium') or book_data['cover'].get('small')
    
    metadata = {
        "isbn": clean_isbn,
        "title": book_data.get('title', 'Unknown'),
        "authors": authors,
        "cover_url": cover_url,
        "publisher": book_data.get('publishers', [{}])[0].get('name') if book_data.get('publishers') else None,
        "publish_date": book_data.get('publish_date'),
        "page_count": book_data.get('number_of_pages'),
        "subjects": [s['name'] for s in book_data.get('subjects', [])][:5]
    }
    
    await db.books.insert_one(metadata)
    return BookMetadata(**metadata)

@api_router.get("/books/content/{isbn}")
async def get_book_content(isbn: str, current_user: User = Depends(get_current_user)):
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    cached_content = await db.book_contents.find_one({"isbn": clean_isbn}, {"_id": 0})
    if cached_content:
        return {"isbn": clean_isbn, "content": cached_content['content'], "source": cached_content.get('source', 'cache')}
    
    text = await fetch_book_text(clean_isbn)
    if text:
        content_doc = {
            "isbn": clean_isbn,
            "content": text,
            "source": "archive.org"
        }
        await db.book_contents.insert_one(content_doc)
        return {"isbn": clean_isbn, "content": text, "source": "archive.org"}
    
    return {
        "isbn": clean_isbn,
        "content": "This book's full text is not available in our database. We currently support public domain books from Internet Archive. Please try another ISBN or check if this book is available in public domain.",
        "source": "unavailable"
    }

@api_router.post("/progress", response_model=Progress)
async def save_progress(progress_data: ProgressCreate, current_user: User = Depends(get_current_user)):
    progress_dict = {
        "user_email": current_user.email,
        "isbn": progress_data.isbn,
        "position": progress_data.position,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    await db.progress.update_one(
        {"user_email": current_user.email, "isbn": progress_data.isbn},
        {"$set": progress_dict},
        upsert=True
    )
    
    return Progress(**progress_dict)

@api_router.get("/progress/{isbn}", response_model=Optional[Progress])
async def get_progress(isbn: str, current_user: User = Depends(get_current_user)):
    progress = await db.progress.find_one(
        {"user_email": current_user.email, "isbn": isbn},
        {"_id": 0}
    )
    if progress:
        if isinstance(progress.get('last_updated'), str):
            progress['last_updated'] = datetime.fromisoformat(progress['last_updated'])
        return Progress(**progress)
    return None

@api_router.post("/bookmarks", response_model=Bookmark)
async def create_bookmark(bookmark_data: BookmarkCreate, current_user: User = Depends(get_current_user)):
    bookmark_dict = {
        "user_email": current_user.email,
        "isbn": bookmark_data.isbn,
        "position": bookmark_data.position,
        "text": bookmark_data.text,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bookmarks.insert_one(bookmark_dict)
    return Bookmark(**bookmark_dict)

@api_router.get("/bookmarks/{isbn}", response_model=List[Bookmark])
async def get_bookmarks(isbn: str, current_user: User = Depends(get_current_user)):
    bookmarks = await db.bookmarks.find(
        {"user_email": current_user.email, "isbn": isbn},
        {"_id": 0}
    ).to_list(100)
    
    for bookmark in bookmarks:
        if isinstance(bookmark.get('created_at'), str):
            bookmark['created_at'] = datetime.fromisoformat(bookmark['created_at'])
    
    return [Bookmark(**b) for b in bookmarks]

@api_router.delete("/bookmarks/{isbn}/{position}")
async def delete_bookmark(isbn: str, position: float, current_user: User = Depends(get_current_user)):
    result = await db.bookmarks.delete_one(
        {"user_email": current_user.email, "isbn": isbn, "position": position}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"message": "Bookmark deleted"}

@api_router.post("/highlights", response_model=Highlight)
async def create_highlight(highlight_data: HighlightCreate, current_user: User = Depends(get_current_user)):
    highlight_dict = {
        "user_email": current_user.email,
        "isbn": highlight_data.isbn,
        "text": highlight_data.text,
        "color": highlight_data.color,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.highlights.insert_one(highlight_dict)
    return Highlight(**highlight_dict)

@api_router.get("/highlights/{isbn}", response_model=List[Highlight])
async def get_highlights(isbn: str, current_user: User = Depends(get_current_user)):
    highlights = await db.highlights.find(
        {"user_email": current_user.email, "isbn": isbn},
        {"_id": 0}
    ).to_list(100)
    
    for highlight in highlights:
        if isinstance(highlight.get('created_at'), str):
            highlight['created_at'] = datetime.fromisoformat(highlight['created_at'])
    
    return [Highlight(**h) for h in highlights]

@api_router.get("/library")
async def get_user_library(current_user: User = Depends(get_current_user)):
    progress_list = await db.progress.find(
        {"user_email": current_user.email},
        {"_id": 0}
    ).to_list(100)
    
    library = []
    for prog in progress_list:
        book = await db.books.find_one({"isbn": prog['isbn']}, {"_id": 0})
        if book:
            library.append({
                "book": book,
                "progress": prog['position'],
                "last_read": prog['last_updated']
            })
    
    return library

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()