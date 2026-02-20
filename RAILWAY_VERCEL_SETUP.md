# Complete Setup Guide: Railway Backend + Vercel Frontend

## Overview

This guide walks you through deploying your Fintrace backend to Railway and connecting it with a Vercel frontend.

## Architecture

```
┌─────────────────┐         HTTPS          ┌─────────────────┐
│                 │ ◄──────────────────────► │                 │
│  Vercel         │    POST /analyze        │   Railway       │
│  (Frontend)     │    (multipart/form)     │   (Backend)     │
│                 │ ◄──────────────────────► │                 │
└─────────────────┘    JSON Response        └─────────────────┘
  yourapp.vercel.app                         your-app.railway.app
```

## Part 1: Deploy Backend to Railway

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Backend ready for Railway deployment"

# Push to GitHub
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically:
   - Detect your Dockerfile
   - Build the container
   - Deploy the service
   - Assign a public URL

### Step 3: Get Your Railway URL

After deployment completes (2-5 minutes):
1. Click on your service in Railway dashboard
2. Go to "Settings" tab
3. Click "Generate Domain" if not already generated
4. Copy your URL: `https://your-app.up.railway.app`

### Step 4: Test Backend

```bash
# Test health endpoint
curl https://your-app.up.railway.app/health

# Expected response:
# {"status":"ok","service":"fraudai-backend"}

# Test API docs
open https://your-app.up.railway.app/docs
```

## Part 2: Configure CORS for Vercel

### Step 1: Get Your Vercel Domain

Your Vercel frontend will have URLs like:
- Production: `https://yourapp.vercel.app`
- Preview: `https://yourapp-git-branch-username.vercel.app`

### Step 2: Set ALLOWED_ORIGINS in Railway

1. Go to Railway dashboard
2. Click your service
3. Go to "Variables" tab
4. Click "New Variable"
5. Add:
   - **Variable:** `ALLOWED_ORIGINS`
   - **Value:** `https://yourapp.vercel.app`

For multiple domains (recommended):
```
https://yourapp.vercel.app,https://yourapp-git-main-username.vercel.app
```

6. Railway will automatically redeploy

### Step 3: Verify CORS

```bash
# Test CORS headers
curl -I -X OPTIONS https://your-app.up.railway.app/analyze \
  -H "Origin: https://yourapp.vercel.app" \
  -H "Access-Control-Request-Method: POST"

# Should see:
# Access-Control-Allow-Origin: https://yourapp.vercel.app
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## Part 3: Configure Frontend (Vercel)

### Step 1: Set Environment Variable

In your Vercel project settings → Environment Variables:

**For Next.js:**
```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

**For Vite/React:**
```
VITE_API_URL=https://your-app.up.railway.app
```

**For Create React App:**
```
REACT_APP_API_URL=https://your-app.up.railway.app
```

### Step 2: Update Frontend Code

Create an API utility file:

```javascript
// src/utils/api.js or src/lib/api.js

const API_URL = process.env.NEXT_PUBLIC_API_URL || 
                import.meta.env?.VITE_API_URL ||
                process.env.REACT_APP_API_URL;

export async function analyzeTransactions(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Analysis failed');
  }

  return response.json();
}
```

### Step 3: Use in Component

```javascript
// Example React component
import { analyzeTransactions } from './utils/api';

function UploadComponent() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    try {
      const data = await analyzeTransactions(file);
      setResults(data);
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        accept=".csv,.xlsx,.xls" 
        onChange={handleUpload}
        disabled={loading}
      />
      
      {loading && <p>Analyzing...</p>}
      
      {results && (
        <div>
          <h3>Results</h3>
          <p>Suspicious Accounts: {results.summary.suspicious_accounts_flagged}</p>
          <p>Fraud Rings: {results.summary.fraud_rings_detected}</p>
        </div>
      )}
    </div>
  );
}
```

### Step 4: Deploy Frontend

```bash
# Vercel will automatically deploy on git push
git add .
git commit -m "Add backend integration"
git push origin main
```

## Part 4: Test End-to-End

### Test 1: Health Check from Frontend

```javascript
// In browser console on your Vercel site
fetch('https://your-app.up.railway.app/health')
  .then(r => r.json())
  .then(console.log);

// Should log: {status: "ok", service: "fraudai-backend"}
```

### Test 2: File Upload

1. Go to your Vercel frontend
2. Select a CSV file with transaction data
3. Upload and analyze
4. Verify results display correctly

### Test 3: Check Browser Console

- Open browser DevTools (F12)
- Go to Console tab
- Should see NO CORS errors
- Network tab should show successful requests

## Troubleshooting

### Problem: CORS Error

```
Access to fetch at 'https://your-app.up.railway.app/analyze' 
from origin 'https://yourapp.vercel.app' has been blocked by CORS policy
```

**Solution:**
1. Check ALLOWED_ORIGINS in Railway includes your Vercel domain
2. Ensure exact match (including https://, no trailing slash)
3. Wait for Railway to redeploy after changing variables
4. Clear browser cache and try again

### Problem: Network Error

```
Failed to fetch
```

**Solution:**
1. Verify Railway service is running (green status in dashboard)
2. Test backend directly: `curl https://your-app.up.railway.app/health`
3. Check Railway logs for errors
4. Verify URL is correct in frontend environment variables

### Problem: 400 Bad Request

```json
{"detail": "Missing required columns: ['amount']"}
```

**Solution:**
1. Verify CSV has all required columns:
   - transaction_id
   - sender_id (or from_account)
   - receiver_id (or to_account)
   - amount
   - timestamp
2. Check CSV format is valid
3. Ensure file is not empty

### Problem: Environment Variable Not Working

**Solution:**
1. Verify variable name matches your framework:
   - Next.js: Must start with `NEXT_PUBLIC_`
   - Vite: Must start with `VITE_`
   - CRA: Must start with `REACT_APP_`
2. Redeploy frontend after adding variables
3. Check variable is set: `console.log(process.env.NEXT_PUBLIC_API_URL)`

## API Endpoints Reference

### POST /analyze
Upload and analyze transaction CSV file

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Field name: `file`
- Accepted: .csv, .xlsx, .xls, .tsv

**Response:**
```json
{
  "suspicious_accounts": [...],
  "fraud_rings": [...],
  "summary": {
    "total_accounts_analyzed": 500,
    "suspicious_accounts_flagged": 15,
    "fraud_rings_detected": 4,
    "processing_time_seconds": 2.345
  }
}
```

### GET /health
Check if backend is running

**Response:**
```json
{
  "status": "ok",
  "service": "fraudai-backend"
}
```

### GET /docs
Interactive API documentation (Swagger UI)

### GET /redoc
Alternative API documentation (ReDoc)

## CSV Format Requirements

Your CSV must have these columns:

```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TX001,ACC_A,ACC_B,500.00,2025-01-01 09:00:00
TX002,ACC_B,ACC_C,490.00,2025-01-01 10:00:00
```

**Required columns:**
- `transaction_id` - Unique transaction identifier
- `sender_id` - Account sending money (aliases: from_account, source_id)
- `receiver_id` - Account receiving money (aliases: to_account, destination_id)
- `amount` - Transaction amount (must be positive number)
- `timestamp` - Date/time (formats: YYYY-MM-DD HH:MM:SS, DD/MM/YYYY, etc.)

## Performance Expectations

- Small files (100 rows): < 1 second
- Medium files (1,000 rows): 1-3 seconds
- Large files (10,000 rows): 5-10 seconds
- Max file size: 100MB (Railway default)

## Security Best Practices

1. **Use specific CORS origins**
   - Don't use `*` in production
   - Only allow your Vercel domains

2. **Use HTTPS**
   - Railway provides HTTPS automatically
   - Vercel provides HTTPS automatically

3. **Validate files on frontend**
   - Check file size before upload
   - Validate file extension
   - Show progress indicator

4. **Handle errors gracefully**
   - Show user-friendly error messages
   - Log errors for debugging
   - Don't expose sensitive information

## Monitoring

### Railway Dashboard
- View real-time logs
- Monitor CPU/memory usage
- Check deployment history
- View metrics and analytics

### Vercel Dashboard
- View deployment logs
- Monitor function execution
- Check analytics
- View error reports

## Cost Estimates

### Railway
- Free tier: $5/month credit
- Typical usage: $0-5/month for small projects
- Scales automatically with usage

### Vercel
- Free tier: Generous limits for personal projects
- Typical usage: Free for most small projects
- Scales automatically

## Next Steps

1. ✅ Backend deployed to Railway
2. ✅ CORS configured
3. ✅ Frontend connected to backend
4. ✅ End-to-end testing complete

**Optional enhancements:**
- Add authentication
- Implement rate limiting
- Set up monitoring alerts
- Add custom domain
- Optimize performance
- Add caching

## Support Resources

- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **API Documentation:** https://your-app.up.railway.app/docs
- **Test Script:** `python3 test_api.py`
- **Integration Guide:** See `API_INTEGRATION.md`

---

**Your full-stack application is now live! 🎉**

Backend: https://your-app.up.railway.app  
Frontend: https://yourapp.vercel.app
