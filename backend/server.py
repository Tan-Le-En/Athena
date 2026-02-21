from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'athena_db')

# These are initialized in lifespan
client = None
db = None

@asynccontextmanager
async def lifespan(app):
    # Startup
    global client, db
    logger.info("Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    logger.info("MongoDB connected.")
    yield
    # Shutdown
    logger.info("Closing MongoDB connection...")
    client.close()
    logger.info("MongoDB connection closed.")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Athena API", lifespan=lifespan)
app.state.limiter = limiter

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS must be added BEFORE routes
allowed_origins = re.split(r'[;,]', os.environ.get('CORS_ORIGINS', '*'))
allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

SECRET_KEY = os.environ.get('SECRET_KEY', 'athena-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback')

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
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: Optional[datetime] = None

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

class LocationReport(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    user_email: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



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
    if isinstance(user.get('last_active_date'), str):
        user['last_active_date'] = datetime.fromisoformat(user['last_active_date'])
    
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

# Map ISBNs to Project Gutenberg book IDs
GUTENBERG_MAP = {
    # Pride and Prejudice - Jane Austen
    '9780141439518': 1342, '9780141439600': 1342, '9780553213102': 1342,
    # 1984 - George Orwell  
    '9780451524935': 3748, '9780141036144': 3748,
    # Great Gatsby - F. Scott Fitzgerald
    '9780743273565': 64317, '9780142437230': 64317,
    # Moby Dick - Herman Melville
    '9780142437247': 2701, '9780553213119': 2701,
    # Frankenstein - Mary Shelley
    '9780141439471': 84, '9780486282114': 84,
    # Dracula - Bram Stoker
    '9780141439846': 345,
    # Alice in Wonderland - Lewis Carroll
    '9780141439761': 11,
    # Sherlock Holmes - Arthur Conan Doyle
    '9780141036755': 1661,
    # War and Peace - Leo Tolstoy
    '9780140447934': 2600,
    # Anna Karenina - Leo Tolstoy
    '9780140449174': 1399,
    # Crime and Punishment - Dostoevsky
    '9780140449136': 2554,
    # Brothers Karamazov - Dostoevsky
    '9780140449242': 28054,
    # Jane Eyre - Charlotte Bronte
    '9780141441146': 1260,
    # Wuthering Heights - Emily Bronte
    '9780141439556': 768,
    # Great Expectations - Charles Dickens
    '9780141439563': 1400,
    # Oliver Twist - Charles Dickens
    '9780141439747': 730,
    # Tale of Two Cities - Charles Dickens
    '9780141439600': 98,
    # Huckleberry Finn - Mark Twain
    '9780142437179': 76,
    # Tom Sawyer - Mark Twain
    '9780141439648': 74,
    # Count of Monte Cristo - Dumas
    '9780140449266': 1184,
    # Three Musketeers - Dumas
    '9780141442334': 1257,
    # Picture of Dorian Gray - Oscar Wilde
    '9780141439570': 174,
    # Importance of Being Earnest - Oscar Wilde
    '9780141439594': 844,
    # Metamorphosis - Kafka
    '9780141182902': 5200,
    # Heart of Darkness - Joseph Conrad
    '9780141441672': 526,
    # War of the Worlds - H.G. Wells
    '9780141441030': 36,
    # The Time Machine - H.G. Wells
    '9780141439976': 35,
}

async def fetch_from_gutenberg(book_id: int) -> Optional[str]:
    """Download and clean text from Project Gutenberg"""
    import re
    urls_to_try = [
        f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt',
        f'https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt',
        f'https://www.gutenberg.org/files/{book_id}/{book_id}.txt',
    ]
    
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}) as client:
        for url in urls_to_try:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    text = response.text
                    
                    # Remove Project Gutenberg headers/footers
                    text = re.sub(r'\*\*\* START OF (THIS|THE) PROJECT GUTENBERG.*?\*\*\*', '', text, flags=re.IGNORECASE | re.DOTALL)
                    text = re.sub(r'\*\*\* END OF (THIS|THE) PROJECT GUTENBERG.*?\*\*\*', '', text, flags=re.IGNORECASE | re.DOTALL)
                    text = re.sub(r'Produced by.*?\n\n', '', text, flags=re.DOTALL)
                    text = re.sub(r'\[Illustration.*?\]', '', text, flags=re.IGNORECASE | re.DOTALL)
                    text = re.sub(r'\[.*?\]', '', text)  # Remove other bracketed text
                    text = re.sub(r'\n{4,}', '\n\n\n', text)
                    
                    # Extract content between START and END markers if present
                    lines = text.split('\n')
                    content_lines = []
                    in_content = False
                    
                    for line in lines:
                        if 'START OF THE PROJECT GUTENBERG' in line.upper() or 'START OF THIS PROJECT GUTENBERG' in line.upper():
                            in_content = True
                            continue
                        if 'END OF THE PROJECT GUTENBERG' in line.upper() or 'END OF THIS PROJECT GUTENBERG' in line.upper():
                            break
                        if in_content:
                            content_lines.append(line)
                    
                    # If no markers found, skip first 20 lines (usually license)
                    if not content_lines and len(lines) > 20:
                        content_lines = lines[20:]
                    
                    # Clean up and filter lines
                    cleaned_lines = []
                    for line in content_lines:
                        line = line.rstrip()
                        if len(line) > 0:
                            cleaned_lines.append(line)
                    
                    result = '\n'.join(cleaned_lines)
                    if len(result) > 1000:
                        return result
            except Exception as e:
                logging.error(f"Error fetching from Gutenberg {url}: {e}")
                continue
    return None

async def search_gutendex(title: str, author: str) -> Optional[int]:
    """Search Project Gutenberg via Gutendex API"""
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={'User-Agent': 'Mozilla/5.0'}) as client:
            # Try searching by title and author
            search_query = f"{title} {author}".replace(' ', '+')
            url = f"https://gutendex.com/books/?search={search_query}"
            
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Return the first result's ID
                    return results[0].get('id')
                
                # If no results with both, try just title
                search_query = title.replace(' ', '+')
                url = f"https://gutendex.com/books/?search={search_query}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    if results:
                        return results[0].get('id')
    except Exception as e:
        logging.error(f"Error searching Gutendex: {e}")
    return None

async def fetch_book_text(isbn: str) -> Optional[str]:
    import re
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    # Try Project Gutenberg first
    if clean_isbn in GUTENBERG_MAP:
        book_id = GUTENBERG_MAP[clean_isbn]
        gutenberg_text = await fetch_from_gutenberg(book_id)
        if gutenberg_text:
            return gutenberg_text
    
    # Fallback to demo books for popular titles
    demo_books = {
        '9780141439518': """PRIDE AND PREJUDICE

By Jane Austen

Chapter I

It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.

However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered as the rightful property of some one or other of their daughters.

"My dear Mr. Bennet," said his lady to him one day, "have you heard that Netherfield Park is let at last?"

Mr. Bennet replied that he had not.

"But it is," returned she; "for Mrs. Long has just been here, and she told me all about it."

Mr. Bennet made no answer.

"Do you not want to know who has taken it?" cried his wife impatiently.

"You want to tell me, and I have no objection to hearing it."

This was invitation enough.

"Why, my dear, you must know, Mrs. Long says that Netherfield is taken by a young man of large fortune from the north of England; that he came down on Monday in a chaise and four to see the place, and was so much delighted with it, that he agreed with Mr. Morris immediately; that he is to take possession before Michaelmas, and some of his servants are to be in the house by the end of next week."

"What is his name?"

"Bingley."

"Is he married or single?"

"Oh! Single, my dear, to be sure! A single man of large fortune; four or five thousand a year. What a fine thing for our girls!"

"How so? How can it affect them?"

"My dear Mr. Bennet," replied his wife, "how can you be so tiresome! You must know that I am thinking of his marrying one of them."

"Is that his design in settling here?"

"Design! Nonsense, how can you talk so! But it is very likely that he may fall in love with one of them, and therefore you must visit him as soon as he comes."

Chapter II

Mr. Bennet was among the earliest of those who waited on Mr. Bingley. He had always intended to visit him, though to the last always assuring his wife that he should not go; and till the evening after the visit was paid, she had no knowledge of it.

It was then disclosed in the following manner. Observing his second daughter employed in trimming a hat, he suddenly addressed her with,

"I hope Mr. Bingley will like it, Lizzy."

"We are not in a way to know what Mr. Bingley likes," said her mother resentfully, "since we are not to visit."

"But you forget, mamma," said Elizabeth, "that we shall meet him at the assemblies, and that Mrs. Long promised to introduce him."

"I do not believe Mrs. Long will do any such thing. She has two nieces of her own. She is a selfish, hypocritical woman, and I have no opinion of her."

"No more have I," said Mr. Bennet; "and I am glad to find that you do not depend on her serving you."

Mrs. Bennet deigned not to make any reply, but, unable to contain herself, began scolding one of her daughters.

"Don't keep coughing so, Kitty, for Heaven's sake! Have a little compassion on my nerves. You tear them to pieces."

"Kitty has no discretion in her coughs," said her father; "she times them ill."

"I do not cough for my own amusement," replied Kitty fretfully.

"When is your next ball to be, Lizzy?"

"To-morrow fortnight." """,
        '9780743273565': """THE GREAT GATSBY

By F. Scott Fitzgerald

Chapter I

In my younger and more vulnerable years my father gave me some advice that I've been turning over in my mind ever since.

"Whenever you feel like criticizing anyone," he told me, "just remember that all the people in this world haven't had the advantages that you've had."

He didn't say any more, but we've always been unusually communicative in a reserved way, and I understood that he meant a great deal more than that.

In consequence, I'm inclined to reserve all judgments, a habit that has opened up many curious natures to me and also made me the victim of not a few veteran bores.

The abnormal mind is quick to detect and attach itself to this quality when it appears in a normal person, and so it came about that in college I was unjustly accused of being a politician, because I was privy to the secret griefs of wild, unknown men.

Most of the confidences were unsought — frequently I have feigned sleep, preoccupation, or a hostile levity when I realized by some unmistakable sign that an intimate revelation was quivering on the horizon.

For the intimate revelations of young men, or at least the terms in which they express them, are usually plagiaristic and marred by obvious suppressions.

Reserving judgments is a matter of infinite hope. I am still a little afraid of missing something if I forget that, as my father snobbishly suggested, and I snobbishly repeat, a sense of the fundamental decencies is parcelled out unequally at birth.

And, after boasting this way of my tolerance, I come to the admission that it has a limit.

Conduct may be founded on the hard rock or the wet marshes, but after a certain point I don't care what it's founded on.

When I came back from the East last autumn I felt that I wanted the world to be in uniform and at a sort of moral attention forever; I wanted no more riotous excursions with privileged glimpses into the human heart.

Only Gatsby, the man who gives his name to this book, was exempt from my reaction.

Gatsby, who represented everything for which I have an unaffected scorn.

If personality is an unbroken series of successful gestures, then there was something gorgeous about him, some heightened sensitivity to the promises of life, as if he were related to one of those intricate machines that register earthquakes ten thousand miles away.

This responsiveness had nothing to do with that flabby impressionability which is dignified under the name of the "creative temperament." It was an extraordinary gift for hope, a romantic readiness such as I have never found in any other person and which it is not likely I shall ever find again.

No — Gatsby turned out all right at the end; it is what preyed on Gatsby, what foul dust floated in the wake of his dreams that temporarily closed out my interest in the abortive sorrows and short-winded elations of men.""",
        '9780451524935': """1984

By George Orwell

Chapter I

It was a bright cold day in April, and the clocks were striking thirteen.

Winston Smith, his chin nuzzled into his breast in an effort to escape the vile wind, slipped quickly through the glass doors of Victory Mansions, though not quickly enough to prevent a swirl of gritty dust from entering along with him.

The hallway smelt of boiled cabbage and old rag mats. At one end of it a coloured poster, too large for indoor display, had been tacked to the wall.

It depicted simply an enormous face, more than a metre wide: the face of a man of about forty-five, with a heavy black moustache and ruggedly handsome features.

Winston made for the stairs. It was no use trying the lift. Even at the best of times it was seldom working, and at present the electric current was cut off during daylight hours. It was part of the economy drive in preparation for Hate Week.

The flat was seven flights up, and Winston, who was thirty-nine and had a varicose ulcer above his right ankle, went slowly, resting several times on the way.

On each landing, opposite the lift-shaft, the poster with the enormous face gazed from the wall. It was one of those pictures which are so contrived that the eyes follow you about when you move. BIG BROTHER IS WATCHING YOU, the caption beneath it ran.

Inside the flat a fruity voice was reading out a list of figures which had something to do with the production of pig-iron. The voice came from an oblong metal plaque like a dulled mirror which formed part of the surface of the right-hand wall.

Winston turned a switch and the voice sank somewhat, though the words were still distinguishable. The instrument (the telescreen, it was called) could be dimmed, but there was no way of shutting it off completely.

He moved over to the window: a smallish, frail figure, the meagreness of his body merely emphasized by the blue overalls which were the uniform of the party. His hair was very fair, his face naturally sanguine, his skin roughened by coarse soap and blunt razor blades and the cold of the winter that had just ended.""",
        '9780143121908': """THE CATCHER IN THE RYE

By J.D. Salinger

Chapter 1

If you really want to hear about it, the first thing you'll probably want to know is where I was born, and what my rotten childhood was like, and how my parents were occupied and all before they had me, and all that David Copperfield kind of crap, but I don't feel like going into it, if you want to know the truth.

In the first place, that stuff bores me, and in the second place, my parents would have about two hemorrhages apiece if I told anything pretty personal about them. They're quite touchy about anything like that, especially my father. They're nice and all--I'm not saying that--but they're touchy as hell.

Besides, I'm not going to tell you my whole Gott-dam autobiography and all. That stuff bores me, and you can't learn anything from it, except possibly how to pronounce names, and you can't learn that from a guy who's bores.

What I have to tell you is about last summer and with this germ around.

I was out at Pencey Prep. It was a school in West 91st Street, and it's about fifty-three miles west of the place where I'm from and Connecticut or something. It was the last year, and anyway it was the place where I was supposed to be this time of year.

I was supposed to be there around August 21st, but I didn't get there until way later, because I had to have this operation and all. The operation was this thing I had on my genitals and all, and I didn't get to school until after Labor Day, which was the way it was supposed to be, because the way that they told my parents I'd have to have the operation and all, they told me I'd have to come back about a couple days early and all.

I forgot to tell you in my last letter about the operation, but I had it about two months ago, and I'm getting pretty run-down and all about this and that. It hasn't been very good for me in some ways, because I can't get to ride horses any more, and it makes me very nervous and very depressed and all.

I didn't get to Pegasus. The thing is, it's very hard to ride horses when you've got a tiny little wick in your thing, and I still have it, not that old but all and all. It's not too tiny or anything, but it's kind of annoying and all. It really is.

Anyway, I didn't feel like going into it all. That stuff is boring.""",
    }
    
    for test_isbn, demo_text in demo_books.items():
        if test_isbn in clean_isbn or clean_isbn.endswith(test_isbn) or test_isbn.startswith(clean_isbn[-4:] if len(clean_isbn) >= 4 else clean_isbn):
            return demo_text
    
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
        try:
            response = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=details")
            if response.status_code == 200:
                data = response.json()
                key = f"ISBN:{clean_isbn}"
                if key in data and 'details' in data[key]:
                    details = data[key]['details']
                    if 'ocaid' in details:
                        ocaid = details['ocaid']
                        
                        urls_to_try = [
                            f"https://archive.org/download/{ocaid}/{ocaid}_djvu.txt",
                            f"https://archive.org/download/{ocaid}/{ocaid}_text.txt",
                            f"https://archive.org/download/{ocaid}/{ocaid}.txt",
                            f"https://archive.org/stream/{ocaid}/{ocaid}_djvu.txt",
                        ]
                        
                        for url in urls_to_try:
                            try:
                                text_response = await client.get(url)
                                if text_response.status_code == 200:
                                    content = text_response.text
                                    
                                    if len(content) > 1000:
                                        if '<!DOCTYPE' not in content[:100].upper() and '<html' not in content[:100].lower():
                                            text = re.sub(r'<[^>]+>', '', content)
                                            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
                                            result = '\n\n'.join(lines)
                                            if len(result) > 500:
                                                return result
                                        else:
                                            text = content
                                            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
                                            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
                                            text = re.sub(r'<a[^>]*>.*?</a>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
                                            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
                                            text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
                                            text = re.sub(r'<[^>]+>', ' ', text)
                                            text = re.sub(r'&nbsp;', ' ', text)
                                            text = re.sub(r'&amp;', '&', text)
                                            text = re.sub(r'Skip to main content', '', text, flags=re.IGNORECASE)
                                            text = re.sub(r'Ask the publishers.*?books', '', text, flags=re.IGNORECASE | re.DOTALL)
                                            text = re.sub(r'Internet Archive', '', text, flags=re.IGNORECASE)
                                            text = re.sub(r'\[Illustration\]', '', text, flags=re.IGNORECASE)
                                            text = re.sub(r'\n{4,}', '\n\n\n', text)
                                            
                                            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
                                            result = '\n\n'.join(lines)
                                            if len(result) > 500:
                                                return result
                            except:
                                continue
        except:
            pass
    
    # If not found in mapping or Archive.org, try searching Project Gutenberg via Gutendex
    try:
        response = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=details")
        if response.status_code == 200:
            data = response.json()
            key = f"ISBN:{clean_isbn}"
            if key in data and 'details' in data[key]:
                details = data[key]['details']
                title = details.get('title', '')
                authors_list = details.get('authors', [])
                author = authors_list[0].get('name', '') if authors_list else ''
                
                if title and author:
                    logging.info(f"Searching Gutendex for: {title} by {author}")
                    book_id = await search_gutendex(title, author)
                    if book_id:
                        logging.info(f"Found on Gutendex, book ID: {book_id}")
                        gutenberg_text = await fetch_from_gutenberg(book_id)
                        if gutenberg_text:
                            return gutenberg_text
    except Exception as e:
        logging.error(f"Error searching for book on Gutendex: {e}")
    
    return None

def parse_archive_html(html: str) -> str:
    import re
    
    text = html
    
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    text = re.sub(r'<header[^>]*>.*?</header>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<footer[^>]*>.*?</footer>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<nav[^>]*>.*?</nav>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<aside[^>]*>.*?</aside>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'<div[^>]*class="[^"]*nav[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*menu[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*header[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*footer[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*sidebar[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*advertisement[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class="[^"]*sponsor[^"]*"[^>]*>.*?</div>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'<a[^>]*>.*?</a>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</span>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
    
    text = re.sub(r'<[^>]+>', ' ', text)
    
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    
    text = re.sub(r'Skip to main content', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Ask the publishers to restore access.*?books', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Internet Archive', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Wayback Machine', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Hamburger icon', '', text, flags=re.IGNORECASE)
    text = re.sub(r'an icon used to represent.*?icon', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Full text of', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Illustration\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[illustration\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'__[^_]*__', '', text)
    text = re.sub(r'//[^\n]*', '', text)
    
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        line = re.sub(r'^\d+$', '', line)
        line = re.sub(r'^Page \d+$', '', line)
        line = re.sub(r'^Page \d+ of \d+$', '', line)
        if len(line) > 2:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def parse_archive_html(html: str) -> str:
    import re
    
    text = html
    
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    text = re.sub(r'<header[^>]*>.*?</header>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<footer[^>]*>.*?</footer>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<nav[^>]*>.*?</nav>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<aside[^>]*>.*?</aside>', '\n', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'<a[^>]*>.*?</a>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</span>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    
    text = re.sub(r'Skip to main content', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Ask the publishers to restore access.*?books', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Internet Archive', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Wayback Machine', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Illustration\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'__[^_]*__', '', text)
    
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        line = re.sub(r'^\d+$', '', line)
        line = re.sub(r'^Page \d+$', '', line)
        line = re.sub(r'^Page \d+ of \d+$', '', line)
        if len(line) > 2:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
    return None

async def update_user_streak(email: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return
    
    now = datetime.now(timezone.utc)
    today = now.date()
    
    last_active = user.get("last_active_date")
    current_streak = user.get("current_streak", 0)
    longest_streak = user.get("longest_streak", 0)
    
    if isinstance(last_active, str):
        try:
            last_active = datetime.fromisoformat(last_active)
        except ValueError:
            last_active = None
            
    updates = {"last_active_date": now.isoformat()}
    
    if last_active:
        last_date = last_active.date()
        diff = (today - last_date).days
        
        if diff == 1:
            # Consecutive day
            current_streak += 1
            updates["current_streak"] = current_streak
            if current_streak > longest_streak:
                updates["longest_streak"] = current_streak
        elif diff > 1:
            # Streak broken
            updates["current_streak"] = 1
        # If diff == 0, same day, do nothing regarding streak count
    else:
        # First activity
        updates["current_streak"] = 1
        updates["longest_streak"] = 1
        
    await db.users.update_one({"email": email}, {"$set": updates})

@api_router.post("/auth/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "current_streak": 0,
        "longest_streak": 0,
        "last_active_date": None
    }
    
    await db.users.insert_one(user_dict)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    user = User(email=user_data.email, name=user_data.name)
    return TokenResponse(access_token=access_token, user=user)

@api_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
     
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    user_obj = User(
        email=user["email"], 
        name=user["name"], 
        created_at=user.get("created_at"),
        current_streak=user.get("current_streak", 0),
        longest_streak=user.get("longest_streak", 0),
        last_active_date=user.get("last_active_date")
    )
    return TokenResponse(access_token=access_token, user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/books/search/{isbn}", response_model=BookMetadata)
@limiter.limit("20/minute")
async def search_book(request: Request, isbn: str):
    # Allow searching by ISBN or title
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    # Check if it's a valid ISBN
    if validate_isbn(clean_isbn):
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

@api_router.get("/books/gutenberg/search")
@limiter.limit("20/minute")
async def search_gutenberg_books(request: Request, query: str):
    """Search Project Gutenberg catalog directly"""
    try:
        async with httpx.AsyncClient(timeout=30.0, headers={'User-Agent': 'Mozilla/5.0'}) as client:
            search_url = f"https://gutendex.com/books/?search={query.replace(' ', '+')}"
            response = await client.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for book in data.get('results', [])[:10]:  # Limit to 10 results
                    results.append({
                        "id": book.get('id'),
                        "title": book.get('title'),
                        "authors": [a.get('name') for a in book.get('authors', [])],
                        "subjects": book.get('subjects', [])[:3],
                        "bookshelf": book.get('bookshelf', '')
                    })
                return {"results": results, "count": len(results)}
            else:
                return {"results": [], "count": 0}
    except Exception as e:
        logging.error(f"Error searching Gutenberg: {e}")
        return {"results": [], "count": 0, "error": str(e)}

@api_router.get("/books/gutenberg/{gutenberg_id}")
@limiter.limit("10/minute")
async def get_gutenberg_book_content(request: Request, gutenberg_id: int, current_user: User = Depends(get_current_user)):
    """Get content of any book from Project Gutenberg by its ID"""
    import re
    
    # Try to fetch from Gutenberg
    text = await fetch_from_gutenberg(gutenberg_id)
    
    if text and len(text) > 1000:
        # Cache it
        await db.book_contents.insert_one({
            "isbn": f"gutenberg_{gutenberg_id}",
            "content": text,
            "source": "gutenberg.org"
        })
        return {"gutenberg_id": gutenberg_id, "content": text, "source": "gutenberg.org"}
    else:
        raise HTTPException(status_code=404, detail="Book content not available from Project Gutenberg")

@api_router.get("/books/content/{isbn}")
@limiter.limit("10/minute")
async def get_book_content(request: Request, isbn: str, current_user: User = Depends(get_current_user)):
    import re
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    def clean_text(text):
        text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<html[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</html>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<head[^>]*>.*?</head>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'class="[^"]*"', '', text)
        text = re.sub(r'id="[^"]*"', '', text)
        text = re.sub(r'data-[a-z-]+="[^"]*"', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#\d+;', '', text)
        text = re.sub(r'Skip to main content', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Ask the publishers to restore access', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Internet Archive', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Wayback Machine', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[Illustration\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[illustration\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'__[^_]*__', '', text)
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 2:
                cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)
    
    cached_content = await db.book_contents.find_one({"isbn": clean_isbn}, {"_id": 0})
    if cached_content:
        cleaned = clean_text(cached_content['content'])
        return {"isbn": clean_isbn, "content": cleaned, "source": "cache"}
    
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
    
    # Update Streak
    await update_user_streak(current_user.email)
    
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
    
    # Creating a bookmark counts as activity
    await update_user_streak(current_user.email)
    
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
    
    # Highlighting counts as activity
    await update_user_streak(current_user.email)

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

@app.get("/api/auth/google")
async def google_login():
    """Redirect to Google OAuth"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    from urllib.parse import urlencode
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"url": google_auth_url}

@app.get("/api/auth/google/callback")
async def google_callback(code: str, request: Request):
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': GOOGLE_REDIRECT_URI
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        access_token = token_response.json()['access_token']
        
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        existing_user = await db.users.find_one({"email": email})
        
        if not existing_user:
            user_dict = {
                "email": email,
                "name": name,
                "password": get_password_hash(f"google_oauth_{email}_{datetime.now().timestamp()}"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "current_streak": 0,
                "longest_streak": 0,
                "last_active_date": None,
                "oauth_provider": "google"
            }
            await db.users.insert_one(user_dict)
        
        jwt_token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        user = await db.users.find_one({"email": email}, {"_id": 0, "password": 0})
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if isinstance(user.get('last_active_date'), str):
            user['last_active_date'] = datetime.fromisoformat(user['last_active_date'])
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(url=f"{frontend_url}?token={jwt_token}&user={user_info['email']}&name={name}")

@app.get("/health")
async def health_check():
    """Health check endpoint for Render and monitoring."""
    return {"status": "healthy", "service": "athena-backend"}

@app.post("/api/location")
async def report_location(report: LocationReport, request: Request):
    """Receive location from frontend and send it to Google Sheets with IP."""
    client_host = request.client.host
    # If behind a proxy (like Render), try X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0] if forwarded else client_host
    
    logger.info(f"Received location: {report.latitude}, {report.longitude} from IP: {ip}")
    
    sheet_url = os.environ.get('GOOGLE_SHEET_URL')
    
    if sheet_url:
        try:
            payload = {
                "latitude": report.latitude,
                "longitude": report.longitude,
                "altitude": report.altitude,
                "user_email": report.user_email or "Anonymous",
                "timestamp": report.timestamp.isoformat(),
                "ip_address": ip
            }
            
            # Use follow_redirects=True because Google Apps Script always redirects (302)
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.post(
                    sheet_url,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Location successfully sent to Google Sheets via POST for IP: {ip}")
                    with open("debug_sheets.log", "a") as f:
                        f.write(f"{datetime.now()}: POST Success for IP {ip}\n")
                else:
                    msg = f"Google Sheets POST returned status {response.status_code}. Content: {response.text[:200]}"
                    logger.error(msg)
                    with open("debug_sheets.log", "a") as f:
                        f.write(f"{datetime.now()}: POST Error {response.status_code}\n")
        except Exception as e:
            error_msg = f"Error sending POST to Google Sheets: {str(e)}"
            logger.error(error_msg)
            with open("debug_sheets.log", "a") as f:
                f.write(f"{datetime.now()}: POST Exception: {str(e)}\n")





    else:
        logger.warning("GOOGLE_SHEET_URL not set. Location logged but not sent to Sheets.")
        print(f"SHEET SIMULATION: {report.latitude}, {report.longitude}, {report.timestamp}, {report.user_email}, IP: {ip}")

    return {"status": "success", "message": "Location reported"}



app.include_router(api_router)