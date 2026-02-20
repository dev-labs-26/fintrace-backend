# 🚀 Deploy to Railway NOW

## Your backend is 100% ready! Here's how to deploy:

### Option 1: Deploy via GitHub (5 minutes)

```bash
# 1. Commit everything
git add .
git commit -m "Backend ready for Railway deployment"

# 2. Push to GitHub (if not already)
git push origin main

# 3. Go to Railway and deploy
# Visit: https://railway.app/new
# Click: "Deploy from GitHub repo"
# Select: Your repository
# Done! Railway will auto-deploy
```

### Option 2: Deploy via Railway CLI (3 minutes)

```bash
# 1. Install Railway CLI (if not installed)
npm i -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize and deploy
railway init
railway up

# 4. Get your URL
railway domain
```

## After Deployment

Your app will be live at: `https://your-app.up.railway.app`

Test it:
```bash
# Health check
curl https://your-app.up.railway.app/health

# API docs
open https://your-app.up.railway.app/docs
```

## Set Environment Variables (Optional)

In Railway dashboard → Variables:
- `ALLOWED_ORIGINS` = `https://your-frontend-domain.com`

## That's It!

Your backend is deployed and ready to handle fraud detection requests! 🎉

---

**Need help?** Check `DEPLOYMENT.md` for detailed instructions.
