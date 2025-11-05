# 🚀 Render Deployment Guide for Sentilizer

## Quick Setup Steps:

### 1. **Create New Web Service**
- Go to [Render Dashboard](https://dashboard.render.com/)
- Click "New +" → "Web Service"
- Connect your Git repository

### 2. **Configure Settings**

#### Basic Settings:
- **Name:** `sentilizer` (or whatever you want)
- **Region:** Choose closest to you (Oregon, Frankfurt, etc.)
- **Branch:** `main`
- **Root Directory:** Leave blank
- **Runtime:** Python

#### Build & Deploy Settings:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

### 3. **Environment Variables** (IMPORTANT!)

Click "Advanced" and add these environment variables:

#### Option A: Without Database (Simpler - uses SQLite)
Just deploy as-is. The app will use SQLite (might have limitations on Render).

#### Option B: With PostgreSQL Database (Recommended)
1. First, create a PostgreSQL database:
   - Click "New +" → "PostgreSQL"
   - Name: `sentilizer-db`
   - Plan: Free
   - Click "Create Database"

2. Add environment variable to your Web Service:
   - Key: `DATABASE_URL`
   - Value: Copy the **Internal Database URL** from your PostgreSQL database

### 4. **Important Notes**

✅ **Python Version:** The app uses Python 3.11.11 (specified in `runtime.txt`)

✅ **SECRET_KEY:** Auto-generated on startup (no need to set manually)

✅ **Model Files:** Make sure you pushed the `models/` folder with:
   - `log_reg.pkl`
   - `tfidf.pkl`

### 5. **Deploy!**

Click "Create Web Service" and wait for deployment to complete (3-5 minutes).

---

## Troubleshooting

### If you see "Python 3.13" in logs:
- Render might be ignoring the runtime.txt
- In Dashboard, go to "Environment" and add:
  - Key: `PYTHON_VERSION`
  - Value: `3.11.11`
- Trigger manual redeploy

### If you see "FileNotFoundError: Model or vectorizer file not found":
- The ML model files are missing
- Make sure you committed and pushed the `models/` folder
- Check that both `.pkl` files are in the folder

### If you see database errors:
- If using PostgreSQL, make sure DATABASE_URL is set correctly
- Try without DATABASE_URL first (uses SQLite)

---

## 🎉 Success!

Once deployed, your app will be available at:
`https://sentilizer.onrender.com` (or your custom name)

The first request might be slow (cold start), but subsequent requests will be faster.

