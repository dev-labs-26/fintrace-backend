# Railway Deployment Guide

## Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub repository (recommended) or Railway CLI

## Deployment Steps

### Option 1: Deploy from GitHub (Recommended)

1. Push your code to GitHub
2. Go to https://railway.app/new
3. Click "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the configuration from `railway.toml`

### Option 2: Deploy using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## Environment Variables

Railway will automatically set `PORT` - no manual configuration needed.

Optional environment variables you can set in Railway dashboard:

- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (default: `*`)
  - Example: `https://yourfrontend.com,https://app.yourfrontend.com`

## Configuration Files

Your backend includes multiple deployment configurations:

1. `railway.toml` - Railway-specific configuration (primary)
2. `nixpacks.toml` - Alternative Nixpacks builder configuration
3. `Dockerfile` - Docker-based deployment
4. `Procfile` - Process configuration fallback

Railway will automatically detect and use the appropriate configuration.

## Health Check

Railway uses the `/health` endpoint to verify your service is running:
- Endpoint: `GET /health`
- Expected response: `{"status": "ok", "service": "fraudai-backend"}`
- Timeout: 100 seconds (configured in railway.toml)

## Post-Deployment

After deployment, Railway will provide:
- A public URL (e.g., `https://your-app.up.railway.app`)
- Automatic HTTPS
- Environment variable management
- Logs and metrics

### Test Your Deployment

```bash
# Health check
curl https://your-app.up.railway.app/health

# API documentation
open https://your-app.up.railway.app/docs

# Test analyze endpoint
curl -X POST https://your-app.up.railway.app/analyze \
  -F "file=@test_transactions.csv"
```

## Monitoring

Access your Railway dashboard to:
- View real-time logs
- Monitor resource usage
- Set up custom domains
- Configure environment variables
- View deployment history

## Troubleshooting

### Build Fails
- Check Railway logs for specific error messages
- Verify `requirements.txt` has all dependencies
- Ensure Python version matches `runtime.txt` (3.11.9)

### Service Won't Start
- Check that `PORT` environment variable is being used
- Verify `/health` endpoint is accessible
- Review application logs in Railway dashboard

### CORS Issues
- Set `ALLOWED_ORIGINS` environment variable with your frontend URL
- Ensure frontend is using the correct backend URL

## Scaling

Railway automatically handles:
- Horizontal scaling (multiple instances)
- Load balancing
- Zero-downtime deployments

To scale manually:
- Go to your service settings in Railway
- Adjust the number of replicas
- Configure resource limits if needed

## Cost Optimization

- Railway offers a free tier with $5 monthly credit
- Monitor usage in the dashboard
- Consider setting up usage alerts
- Use sleep mode for development environments

## Security Best Practices

1. Set specific `ALLOWED_ORIGINS` instead of `*`
2. Use Railway's environment variables for sensitive data
3. Enable Railway's built-in DDoS protection
4. Review and rotate any API keys regularly
5. Monitor logs for suspicious activity

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Create issues in your repository
