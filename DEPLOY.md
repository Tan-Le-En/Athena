# Athena Deployment Guide

This guide walks you through deploying Athena (the editorial digital library) to Vercel (frontend) and Render (backend).

## Prerequisites

- GitHub account
- Vercel account (free)
- Render account (free)
- MongoDB Atlas account (free tier)

---

## Step 1: Set Up MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas/database) and create a free account
2. Create a free cluster (选择免费套餐)
3. Create a database user (用户名和密码记下来)
4. Network Access: Add IP `0.0.0.0/0` (允许所有IP访问)
5. Get connection string: Click "Connect" → "Connect your application" → Copy the connection string
   - Replace `<password>` with your database password
   - Connection string looks like: `mongodb+srv://username:password@cluster.mongodb.net/athena_db`

---

## Step 2: Deploy Backend to Render

### Option A: Automatic Deployment (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml` and configure:
   - Service name: `athena-backend`
   - Region: Choose closest to you
6. Add these Environment Variables:
   - `MONGO_URL`: Your MongoDB Atlas connection string
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://athena-yourname.vercel.app`)
   - `SECRET_KEY`: Generate a random string (use: `openssl rand -base64 32`)
   - `DB_NAME`: `athena_db`
7. Click "Apply Blueprint"

### Option B: Manual Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - Name: `athena-backend`
   - Root Directory: `backend`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (same as above)
6. Click "Create Web Service"

### Get Your Backend URL

After deployment, your backend will be at:

```
https://athena-backend.onrender.com
```

---

## Step 3: Deploy Frontend to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - Framework Preset: `Create React App`
   - Root Directory: `frontend`
5. Add Environment Variable:
   - `REACT_APP_BACKEND_URL`: Your Render backend URL
   - Example: `https://athena-backend.onrender.com`
6. Click "Deploy"

### Get Your Frontend URL

After deployment, your frontend will be at:

```
https://athena.vercel.app
```

(or similar based on your project name)

---

## Step 4: Configure CORS

1. Go to your Render dashboard
2. Find your backend service
3. Update `CORS_ORIGINS` environment variable to include your Vercel URL:
   - Example: `https://athena-yourname.vercel.app`
4. Click "Save Changes"

---

## Step 5: Test Your Deployment

1. Open your Vercel frontend URL
2. Register a new account
3. Search for a book using ISBN (try: `9780141439518`)
4. Click "Enter Reading Room" to read

---

## Troubleshooting

### CORS Errors

- Make sure `CORS_ORIGINS` in Render includes your exact Vercel URL (no trailing slash)

### Database Connection Issues

- Verify MongoDB Atlas IP whitelist includes `0.0.0.0/0`
- Check that `MONGO_URL` is correct in Render

### Build Failures

- Check that `package.json` has proper build scripts
- Ensure all dependencies are in `requirements.txt` (Python) and `package.json` (Node)

---

## Environment Variables Reference

### Backend (Render)

| Variable         | Description                     | Example                                       |
| ---------------- | ------------------------------- | --------------------------------------------- |
| MONGO_URL        | MongoDB Atlas connection string | `mongodb+srv://...`                           |
| CORS_ORIGINS     | Frontend URL                    | `https://athena.vercel.app`                   |
| SECRET_KEY       | JWT signing key                 | Random 32-char string                         |
| DB_NAME          | Database name                   | `athena_db`                                   |
| GOOGLE_SHEET_URL | Google Apps Script Web App      | `https://script.google.com/macros/s/.../exec` |

### Frontend (Vercel)

| Variable              | Description     | Example                               |
| --------------------- | --------------- | ------------------------------------- |
| REACT_APP_BACKEND_URL | Backend API URL | `https://athena-backend.onrender.com` |

---

## Made By Tan Le En
