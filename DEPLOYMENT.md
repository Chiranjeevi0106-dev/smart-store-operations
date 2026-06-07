# Cloud Deployment Guide

This document provides step-by-step instructions to deploy the **Smart Store Operations Platform** online so it is accessible to everyone.

---

## 🏗️ Deployment Architecture

We deploy the system as three separate layers:
1. **Database**: Managed **MongoDB Atlas** (Free M0 Cluster)
2. **Backend**: **FastAPI** hosted on **Render** (Free Web Service)
3. **Frontend**: **React (Vite)** hosted on **Vercel** or **Netlify** (Free Static Hosting)

---

## 1. Cloud Database Setup (MongoDB Atlas)

1. Sign up for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a new project and select **Build a Database**.
3. Choose the **M0 Free** shared cluster, select your preferred region (e.g., AWS / Mumbai or US East), and name your cluster.
4. Under **Security Quickstart**:
   * Create a database user (e.g., username `db_user` and a strong password). Save these credentials!
   * Under **Network Access**, add IP address `0.0.0.0/0` (Allow access from anywhere) so that Render can connect to it.
5. Once the cluster is deployed, click **Connect** -> **Drivers** (Python).
6. Copy the connection string. It will look like this:
   ```
   mongodb+srv://db_user:<password>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   ```
7. Replace `<password>` with your database user's password, and insert the database name `smartstore` before the `?` query:
   ```
   mongodb+srv://db_user:YOUR_PASSWORD@cluster0.xxxxxx.mongodb.net/smartstore?retryWrites=true&w=majority&appName=Cluster0
   ```
   This is your `MONGO_URI`.

---

## 2. Deploy the Backend (Render)

Render can build and run the FastAPI server directly from your GitHub repository.

1. Push your local codebase to a new **GitHub repository** (make sure it's public or private, Render supports both).
2. Sign up or log in to [Render](https://render.com/).
3. Click **New +** and select **Web Service**.
4. Connect your GitHub repository.
5. Configure the Web Service settings:
   * **Name**: `smart-store-api` (or any unique name)
   * **Region**: Choose a region close to your database/users
   * **Language**: `Python`
   * **Branch**: `main` (or your default branch)
   * **Build Command**:
     ```bash
     pip install -r cloud/api/requirements.txt
     ```
   * **Start Command**:
     ```bash
     cd cloud/api && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
6. Scroll down and click **Advanced** -> **Add Environment Variable**:
   * Key: `MONGO_URI`
   * Value: `mongodb+srv://db_user:YOUR_PASSWORD@cluster0.xxxxxx.mongodb.net/smartstore?retryWrites=true&w=majority&appName=Cluster0` (your connection string from step 1)
7. Click **Create Web Service**.
8. Once deployment is complete, Render will provide a public URL (e.g., `https://smart-store-api.onrender.com`).
   * Test it by opening `https://smart-store-api.onrender.com/stores/IND-BGR-082/shelf-status` in your browser.

---

## 3. Deploy the Frontend (Vercel)

Vercel is the easiest platform to deploy Vite + React apps.

1. Sign up or log in to [Vercel](https://vercel.com/).
2. Click **Add New** -> **Project**.
3. Import your GitHub repository.
4. Configure the settings:
   * **Framework Preset**: `Vite` (automatically detected)
   * **Root Directory**: Select `dashboard` (This is critical since the React project is in the `/dashboard` folder!).
5. Expand the **Environment Variables** section and add the following:
   * **VITE_API_BASE_URL**: `https://smart-store-api.onrender.com` (replace with your Render URL)
   * **VITE_WS_URL**: `wss://smart-store-api.onrender.com/ws/alerts` (replace with your Render URL, using `wss://` instead of `https://` for secure WebSockets)
6. Click **Deploy**.
7. Vercel will build and deploy the React application. Once finished, you will receive a production URL (e.g., `https://dashboard-xxxx.vercel.app`) that anyone can use!

---

## ⚙️ Testing the Deployment Locally

To make sure your configurations are correct before pushing to GitHub:

1. **Test the Backend locally with custom PORT**:
   ```powershell
   $env:PORT="9000"
   $env:MONGO_URI="YOUR_MONGODB_ATLAS_URI"
   .\venv\Scripts\python cloud/api/main.py
   ```
   * The backend should run on port `9000` and connect to MongoDB Atlas.

2. **Build the Frontend locally**:
   ```bash
   cd dashboard
   npm run build
   ```
   * This ensures there are no TypeScript or build-time syntax errors.
