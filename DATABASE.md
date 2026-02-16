# Athena Database Setup (Production)

To deploy Athena to Render, you need a cloud-hosted MongoDB instance (e.g., MongoDB Atlas).

## 1. Get a MongoDB Atlas Cluster

1. Create a free account at [mongodb.com](https://www.mongodb.com/).
2. Create a new Cluster (Free Tier).
3. In "Network Access", allow access from `0.0.0.0/0` (Render needs this).
4. In "Database Access", create a user with a password.
5. Click "Connect" -> "Drivers" -> "Python" to get your connection string.

## 2. Configure Render

In your Render dashboard for the `athena-backend` service:

1. Go to **Environment**.
2. Update `MONGO_URL` with your Atlas connection string (replace `<password>` with your user's password).
   - _Example:_ `mongodb+srv://user:pass@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority`
3. Update `DB_NAME` to `athena` (or your choice).

## 3. Configure Frontend

Ensure your frontend `REACT_APP_BACKEND_URL` points to your backend URL (e.g., `https://athena-backend.onrender.com`).
