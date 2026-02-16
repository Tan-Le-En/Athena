# Athena — Editorial Library

> An immersive, editorial-style digital library that lets you search books by ISBN and instantly read public domain works from Internet Archive.

## Tech Stack

| Layer    | Technology                           |
| -------- | ------------------------------------ |
| Frontend | React (CRA) + CRACO + TailwindCSS 3  |
| Backend  | FastAPI + Uvicorn                    |
| Database | MongoDB (local or Atlas)             |
| Auth     | JWT (python-jose) + bcrypt           |
| Hosting  | Vercel (frontend) + Render (backend) |

---

## Local Development

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.10+
- **MongoDB** running locally on `mongodb://localhost:27017` (or use MongoDB Atlas)

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=athena_db
CORS_ORIGINS=http://localhost:3000
```

Start the backend:

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at:

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
ENABLE_HEALTH_CHECK=false
```

Start the frontend:

```bash
cd frontend
npm start
```

The app opens at **http://localhost:3000**

---

## Production Deployment

### Frontend → Vercel

1. **Push your code** to GitHub
2. **Import** the repo in [vercel.com](https://vercel.com)
3. Set the **Root Directory** to `frontend`
4. Set **Framework Preset** to `Create React App`
5. Add **Environment Variable** in Vercel dashboard:
   - `REACT_APP_BACKEND_URL` = `https://athena-backend.onrender.com` (your Render URL)
6. **Deploy** — Vercel will run `npm run build` automatically

The `vercel.json` in the frontend directory handles SPA routing (all routes → index.html).

### Backend → Render

1. **Push your code** to GitHub
2. Go to [render.com](https://render.com) → **New** → **Blueprint**
3. Connect your repo — the `render.yaml` will auto-configure the service
4. Set **Environment Variables** in Render dashboard:
   - `MONGO_URL` = your MongoDB Atlas connection string
   - `CORS_ORIGINS` = your Vercel frontend URL (e.g., `https://athena-xyz.vercel.app`)
5. `SECRET_KEY` and `DB_NAME` are auto-configured by render.yaml

Or create a **Web Service** manually:

- **Root Directory**: `backend`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

### MongoDB Atlas Setup

See [DATABASE.md](DATABASE.md) for detailed instructions on setting up MongoDB Atlas for production.

---

## API Endpoints

| Method | Endpoint                           | Auth | Description             |
| ------ | ---------------------------------- | ---- | ----------------------- |
| POST   | `/api/auth/register`               | No   | Create account          |
| POST   | `/api/auth/login`                  | No   | Login                   |
| GET    | `/api/auth/me`                     | Yes  | Get current user        |
| GET    | `/api/books/search/{isbn}`         | No   | Search book by ISBN     |
| GET    | `/api/books/content/{isbn}`        | Yes  | Get book full text      |
| POST   | `/api/progress`                    | Yes  | Save reading progress   |
| GET    | `/api/progress/{isbn}`             | Yes  | Get reading progress    |
| POST   | `/api/bookmarks`                   | Yes  | Create bookmark         |
| GET    | `/api/bookmarks/{isbn}`            | Yes  | Get bookmarks           |
| DELETE | `/api/bookmarks/{isbn}/{position}` | Yes  | Delete bookmark         |
| POST   | `/api/highlights`                  | Yes  | Create highlight        |
| GET    | `/api/highlights/{isbn}`           | Yes  | Get highlights          |
| GET    | `/api/library`                     | Yes  | Get user's book library |
| GET    | `/health`                          | No   | Health check            |

---

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
└── README.md               # This file
```

---

_Built by Tan Le En_
