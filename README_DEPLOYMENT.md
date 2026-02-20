# 🚀 Fintrace Backend - Ready for Railway + Vercel

## ✅ What's Been Configured

Your backend is **100% ready** for production deployment on Railway with Vercel frontend integration.

### Core Features
- ✅ FastAPI application with fraud detection algorithms
- ✅ File upload support (CSV, TSV, XLSX, XLS)
- ✅ Graph-based pattern detection (cycles, smurfing, layered shells)
- ✅ RESTful API with comprehensive documentation
- ✅ Health check endpoint for monitoring

### Deployment Ready
- ✅ Dockerfile optimized for Railway
- ✅ railway.toml configuration
- ✅ nixpacks.toml alternative builder
- ✅ Procfile for process management
- ✅ CORS configured for cross-origin requests
- ✅ Environment variable support

### Documentation
- ✅ Complete API integration guide
- ✅ Frontend code examples
- ✅ Deployment verification checklist
- ✅ Troubleshooting guide
- ✅ Quick reference card

## 🎯 Quick Start

### 1. Deploy to Railway (2 minutes)

```bash
# Push to GitHub
git push origin main

# Then visit: https://railway.app/new
# Click: "Deploy from GitHub repo"
# Select your repository
# Done! Railway handles the rest
```

### 2. Configure CORS (1 minute)

In Railway dashboard → Variables:
```
ALLOWED_ORIGINS=https://yourapp.vercel.app
```

### 3. Connect Frontend (1 minute)

In Vercel → Environment Variables:
```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

### 4. Test (30 seconds)

```bash
curl https://your-app.up.railway.app/health
# Should return: {"status":"ok","service":"fraudai-backend"}
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Analyze transactions (main endpoint) |
| `/export/csv` | POST | Export results to CSV |
| `/docs` | GET | Interactive API documentation |
| `/redoc` | GET | Alternative documentation |

## 💻 Frontend Integration

### React/Next.js Example

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function analyzeTransactions(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    body: formData
  });

  return response.json();
}
```

See `frontend-example.js` for complete implementation.

## 📋 CSV Format

Your CSV must include these columns:

```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TX001,ACC_A,ACC_B,500.00,2025-01-01 09:00:00
TX002,ACC_B,ACC_C,490.00,2025-01-01 10:00:00
```

**Required columns:**
- `transaction_id` - Unique identifier
- `sender_id` - Sending account
- `receiver_id` - Receiving account
- `amount` - Transaction amount (positive number)
- `timestamp` - Date/time

## 🧪 Testing

### Test Locally

```bash
# Start server
./start.sh

# Or manually
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Test Deployed API

```bash
# Run test suite
python3 test_api.py https://your-app.up.railway.app

# Or test manually
curl -X POST https://your-app.up.railway.app/analyze \
  -F "file=@test_transactions.csv"
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `RAILWAY_VERCEL_SETUP.md` | Complete setup guide |
| `API_INTEGRATION.md` | Frontend integration details |
| `VERIFY_DEPLOYMENT.md` | Deployment checklist |
| `QUICK_REFERENCE.md` | Quick reference card |
| `frontend-example.js` | Frontend code examples |
| `test_api.py` | API testing script |

## 🔧 Configuration

### Environment Variables

**Railway (Backend):**
- `PORT` - Auto-set by Railway
- `ALLOWED_ORIGINS` - Your Vercel domain(s)

**Vercel (Frontend):**
- `NEXT_PUBLIC_API_URL` - Your Railway URL
- Or `VITE_API_URL` for Vite
- Or `REACT_APP_API_URL` for CRA

### Example Configuration

**Railway:**
```bash
ALLOWED_ORIGINS=https://yourapp.vercel.app,https://yourapp-preview.vercel.app
```

**Vercel:**
```bash
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

## ⚡ Performance

Expected processing times:
- Small files (100 rows): < 1 second
- Medium files (1,000 rows): 1-3 seconds
- Large files (10,000 rows): 5-10 seconds

## 🛡️ Security

- ✅ HTTPS enabled by default (Railway)
- ✅ CORS configured for specific origins
- ✅ File validation and sanitization
- ✅ Error handling without sensitive data exposure
- ✅ Input validation on all endpoints

## 🐛 Troubleshooting

### CORS Error?
→ Add your Vercel domain to `ALLOWED_ORIGINS` in Railway

### Network Error?
→ Check Railway service status (should be green)

### 400 Bad Request?
→ Verify CSV has all required columns

### Environment Variable Not Working?
→ Use correct prefix: `NEXT_PUBLIC_` or `VITE_` or `REACT_APP_`

See `VERIFY_DEPLOYMENT.md` for detailed troubleshooting.

## 📊 Response Schema

```json
{
  "suspicious_accounts": [
    {
      "account_id": "ACC_00123",
      "suspicion_score": 87.5,
      "detected_patterns": ["cycle_length_3", "high_velocity"],
      "ring_id": "RING_001"
    }
  ],
  "fraud_rings": [
    {
      "ring_id": "RING_001",
      "member_accounts": ["ACC_00123", "ACC_00456"],
      "pattern_type": "cycle",
      "risk_score": 95.3,
      "member_count": 2
    }
  ],
  "summary": {
    "total_accounts_analyzed": 500,
    "suspicious_accounts_flagged": 15,
    "fraud_rings_detected": 4,
    "processing_time_seconds": 2.345
  }
}
```

## 🎓 Next Steps

1. **Deploy Backend**
   - Push to GitHub
   - Deploy on Railway
   - Get your Railway URL

2. **Configure CORS**
   - Set `ALLOWED_ORIGINS` in Railway
   - Include your Vercel domain

3. **Connect Frontend**
   - Set `NEXT_PUBLIC_API_URL` in Vercel
   - Update frontend code to use API

4. **Test Integration**
   - Upload test CSV
   - Verify results display
   - Check for CORS errors

5. **Go Live**
   - Test with real data
   - Monitor performance
   - Set up alerts (optional)

## 📞 Support

- **API Documentation:** https://your-app.up.railway.app/docs
- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **Test Script:** `python3 test_api.py`

## 🎉 Success Criteria

Your deployment is successful when:

✅ Health check returns 200 OK  
✅ API docs are accessible  
✅ File upload works from frontend  
✅ Results are returned correctly  
✅ No CORS errors in browser  
✅ Processing completes in < 30s  

---

## 🚀 Ready to Deploy!

Your backend is production-ready. Follow the Quick Start above to deploy in 5 minutes.

**Estimated deployment time:** 5 minutes  
**Estimated setup time:** 10 minutes total

Good luck! 🎉
