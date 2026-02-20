# Railway Deployment Troubleshooting

## Issue: Domain Not Resolving

If you get `Could not resolve host: fintrace-backend-production.up.railway.app`, follow these steps:

## Step 1: Check Railway Dashboard

1. Go to https://railway.app/dashboard
2. Find your `fintrace-backend-production` project
3. Check the deployment status

### Possible States:

#### 🟡 Building/Deploying
- **Status:** Yellow/Orange indicator
- **Action:** Wait for deployment to complete (2-5 minutes)
- **What's happening:** Railway is building your Docker container

#### 🔴 Failed
- **Status:** Red indicator with error message
- **Action:** Click on the deployment to see logs
- **Common issues:**
  - Build errors (check Dockerfile)
  - Missing dependencies (check requirements.txt)
  - Port configuration issues

#### 🟢 Running but No Domain
- **Status:** Green indicator but no public URL
- **Action:** Generate a domain (see Step 2)

## Step 2: Generate Public Domain

If your service is running but has no domain:

1. In Railway dashboard, click your service
2. Go to **Settings** tab
3. Scroll to **Networking** section
4. Click **Generate Domain** button
5. Railway will create a public URL like:
   - `fintrace-backend-production.up.railway.app`
   - Or a different format depending on Railway's current naming

## Step 3: Verify Service is Running

### Check Deployment Logs

1. Click on your service in Railway
2. Go to **Deployments** tab
3. Click on the latest deployment
4. Check the logs for:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### Common Log Errors

#### Error: "Port already in use"
```bash
# Not an issue - Railway handles this
```

#### Error: "ModuleNotFoundError"
```bash
# Fix: Check requirements.txt has all dependencies
# Redeploy after fixing
```

#### Error: "Address already in use"
```bash
# Fix: Ensure Dockerfile uses $PORT variable
# Should be: CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

## Step 4: Test with Correct URL

Once you have the domain from Railway:

```bash
# Replace with your actual Railway URL
export RAILWAY_URL="https://your-actual-url.railway.app"

# Test health endpoint
curl $RAILWAY_URL/health

# Expected response:
# {"status":"ok","service":"fraudai-backend"}
```

## Step 5: Common Railway URL Formats

Railway URLs can be in different formats:

1. **Standard format:**
   ```
   https://your-service-name.up.railway.app
   ```

2. **Alternative format:**
   ```
   https://your-service-name-production.up.railway.app
   ```

3. **Custom domain (if configured):**
   ```
   https://api.yourdomain.com
   ```

## Step 6: Check Railway Service Settings

### Verify Start Command

In Railway dashboard → Settings → Deploy:

**Should be:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Or let Dockerfile handle it** (recommended - already configured)

### Verify Health Check

In Railway dashboard → Settings → Deploy:

- **Health Check Path:** `/health`
- **Health Check Timeout:** 100 seconds

## Step 7: Manual Deployment Check

If automatic deployment didn't work:

### Option A: Redeploy from Dashboard

1. Go to Railway dashboard
2. Click your service
3. Click **Deployments** tab
4. Click **Deploy** button (top right)
5. Select **Redeploy**

### Option B: Deploy via CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up

# Get the URL
railway domain
```

## Step 8: Verify Environment Variables

Check that Railway has these variables set:

1. Go to **Variables** tab
2. Verify `PORT` is NOT manually set (Railway sets this automatically)
3. Add `ALLOWED_ORIGINS` if needed:
   ```
   ALLOWED_ORIGINS=https://yourapp.vercel.app
   ```

## Step 9: Check Build Logs

If deployment fails, check build logs:

1. Click on failed deployment
2. Look for errors in **Build Logs** section
3. Common issues:
   - Python version mismatch
   - Missing system dependencies
   - Dockerfile syntax errors

### Fix Build Errors

If you see errors related to:

**Python version:**
```bash
# Ensure runtime.txt has: python-3.11.9
# Or update Dockerfile to use correct Python version
```

**Missing packages:**
```bash
# Add to requirements.txt
# Commit and push
```

**Docker build fails:**
```bash
# Test locally first:
docker build -t test-backend .
docker run -p 8000:8000 -e PORT=8000 test-backend
```

## Step 10: Test Locally First

Before debugging Railway, ensure it works locally:

```bash
# Build and run with Docker
docker build -t fintrace-backend .
docker run -p 8000:8000 -e PORT=8000 fintrace-backend

# Test in another terminal
curl http://localhost:8000/health
```

If local works but Railway doesn't, the issue is Railway-specific.

## Quick Checklist

- [ ] Railway project exists and is selected
- [ ] Service shows green (running) status
- [ ] Public domain is generated
- [ ] Health check endpoint is configured
- [ ] No errors in deployment logs
- [ ] Environment variables are set correctly
- [ ] Dockerfile is correct
- [ ] requirements.txt is complete
- [ ] Code is pushed to GitHub
- [ ] Railway is connected to correct repo/branch

## Get Your Actual Railway URL

### Method 1: Railway Dashboard
1. Go to https://railway.app/dashboard
2. Click your service
3. Look for the public URL at the top
4. Copy the full URL

### Method 2: Railway CLI
```bash
railway login
railway link
railway domain
```

### Method 3: Check Settings
1. Railway dashboard → Your service
2. Settings tab
3. Networking section
4. Copy the domain shown

## Still Not Working?

### Check Railway Status
- Visit: https://status.railway.app
- Verify Railway services are operational

### Check Railway Logs
```bash
# Using CLI
railway logs

# Or in dashboard
# Click service → Deployments → View Logs
```

### Contact Railway Support
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

## Next Steps After Domain Works

Once you get the correct URL and it resolves:

```bash
# Test all endpoints
curl https://your-actual-url.railway.app/health
curl https://your-actual-url.railway.app/docs

# Test file upload
curl -X POST https://your-actual-url.railway.app/analyze \
  -F "file=@test_transactions.csv"

# Run full test suite
python3 test_api.py https://your-actual-url.railway.app
```

## Update Frontend

Once backend is working, update your Vercel environment variables:

```bash
# In Vercel dashboard → Environment Variables
NEXT_PUBLIC_API_URL=https://your-actual-url.railway.app
```

---

**Need the exact URL?** Check your Railway dashboard - the public URL is displayed prominently when the service is running.
