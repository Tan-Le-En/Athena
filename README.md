# Athena — Digital Editorial Library

An immersive, editorial-style digital library that lets you search books by ISBN and instantly read public domain works from Internet Archive.

![Athena Logo](frontend/public/Athena_logo.png)

## Features

- **ISBN Search** - Find any book instantly by ISBN
- **Instant Reading** - Get full text from Internet Archive in seconds
- **Reading Progress** - Save and sync your reading position
- **Bookmarks** - Save your favorite passages
- **Highlights** - Mark and color-code important text
- **Personal Library** - Track your reading collection
- **Reading Streaks** - Stay motivated with daily reading goals

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (CRA) + CRACO + TailwindCSS 3 |
| Backend | FastAPI + Uvicorn |
| Database | MongoDB (local or Atlas) |
| Auth | JWT (python-jose) + bcrypt |
| Hosting | Vercel (frontend) + Render (backend) |

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- MongoDB (local or Atlas)

### Local Development

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=athena_db
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=your-secret-key-here
```

Start the backend:

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

Start the frontend:

```bash
cd frontend
npm start
```

The app opens at **http://localhost:3000**

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | Login |
| GET | `/api/auth/me` | Yes | Get current user |
| GET | `/api/books/search/{isbn}` | No | Search book by ISBN |
| GET | `/api/books/content/{isbn}` | Yes | Get book full text |
| POST | `/api/progress` | Yes | Save reading progress |
| GET | `/api/progress/{isbn}` | Yes | Get reading progress |
| POST | `/api/bookmarks` | Yes | Create bookmark |
| GET | `/api/bookmarks/{isbn}` | Yes | Get bookmarks |
| DELETE | `/api/bookmarks/{isbn}/{position}` | Yes | Delete bookmark |
| POST | `/api/highlights` | Yes | Create highlight |
| GET | `/api/highlights/{isbn}` | Yes | Get highlights |
| GET | `/api/library` | Yes | Get user's book library |

## Project Structure

```
Athena/
├── backend/
│   ├── server.py           # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Local env vars (not committed)
├── frontend/
│   ├── src/
│   │   ├── pages/          # Home, Auth, Reader, Library
│   │   ├── components/ui/  # Radix UI + shadcn components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # Utility functions
│   │   ├── App.js          # Main app with routing
│   │   ├── index.js        # Entry point
│   │   └── index.css       # Global styles + CSS variables
│   ├── public/             # Static assets
│   ├── craco.config.js     # Webpack/Babel config
│   ├── tailwind.config.js  # TailwindCSS config
│   ├── vercel.json         # Vercel deployment config
│   ├── package.json        # Dependencies
│   └── .env                # Local env vars (not committed)
├── render.yaml             # Render deployment blueprint
├── DATABASE.md             # MongoDB Atlas setup guide
├── DEPLOY.md               # Deployment tutorial
└── README.md               # This file
```

## Deployment

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions for Vercel and Render.

## License

MIT

---

Made by Tan Le En
