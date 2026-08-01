# Streamlit Deployment Plan

This document outlines the steps to deploy the `secondself` project to Streamlit Community Cloud.

## 1. Prerequisites
- A GitHub account.
- A Streamlit Community Cloud account (linked to your GitHub account).
- The project must be pushed to a GitHub repository.

## 2. Project Structure Verification
Ensure your repository has the following structure at the root level (or ensure you configure the correct path during deployment):
- `app.py` (The main Streamlit application script)
- `requirements.txt` (Dependencies, currently including `streamlit`, `groq`, `sentence-transformers`, etc.)
- `.env.example` (Reference for required environment variables)

## 3. Environment Variables (Secrets)
The app relies on a `.env` file for local development. For deployment on Streamlit Cloud, you will need to set up Streamlit Secrets.
Identify all keys in your `.env` (e.g., `GROQ_API_KEY`, etc.) so they can be added to the Streamlit Secrets manager later.

## 4. Deployment Steps

### Step 4.1: Push to GitHub
1. Initialize a git repository if not already done.
2. Commit your code. (Make sure `.env` is listed in `.gitignore` so secrets are not exposed).
3. Push to a public or private GitHub repository.

### Step 4.2: Connect to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in.
2. Click on **"New app"**.
3. If this is your first time, authorize Streamlit to access your GitHub repositories.

### Step 4.3: Configure the App
1. **Repository:** Select your GitHub repository containing the `secondself` project.
2. **Branch:** Select the main/master branch.
3. **Main file path:** Enter `app.py` (or `secondself/app.py` depending on where the repo root is).
4. Click on **Advanced settings...** before deploying.

### Step 4.4: Add Secrets
In the "Advanced settings" modal, locate the **Secrets** field. Add your environment variables in TOML format.
For example:
```toml
GROQ_API_KEY = "your-actual-api-key-here"
# Add any other keys required by the application
```
Click **Save**.

### Step 4.5: Deploy
1. Click **Deploy!**
2. Streamlit will pull your code, install the dependencies from `requirements.txt`, and start the app.
3. You can watch the deployment logs in the bottom right corner. If there are any issues (like missing dependencies or incorrect paths), they will appear here.

## 5. Post-Deployment
- **Custom Domain:** You can configure a custom subdomain (e.g., `secondself-ai.streamlit.app`) from the app settings.
- **Continuous Deployment:** Any pushes to the selected GitHub branch will automatically trigger a redeployment on Streamlit Cloud.
