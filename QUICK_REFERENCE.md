# Quick Reference Card

## 🚀 Deploy Backend (Railway)

```bash
git push origin main
# Then: railway.app/new → Deploy from GitHub
```

## 🔗 Connect Frontend (Vercel)

### Set in Vercel Environment Variables:
```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

### Set in Railway Environment Variables:
```
ALLOWED_ORIGINS=https://yourapp.vercel.app
```

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/analyze` | POST | Analyze transactions |
| `/docs` | GET | API documentation |

## 💻 Frontend Code

```javascript
// Upload file
const formData = new FormData();
formData.append('file', file);

const response = await fetch(`${API_URL}/analyze`, {
  method: 'POST',
  body: formData
});

const results = await response.json();
```

## 📋 CSV Format

```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TX001,ACC_A,ACC_B,500.00,2025-01-01 09:00:00
```

## 🧪 Test Commands

```bash
# Health check
curl https://your-app.up.railway.app/health

# Upload file
curl -X POST https://your-app.up.railway.app/analyze \
  -F "file=@test_transactions.csv"

# Run test suite
python3 test_api.py https://your-app.up.railway.app
```

## ⚠️ Troubleshooting

### CORS Error?
→ Add Vercel domain to `ALLOWED_ORIGINS` in Railway

### Network Error?
→ Check Railway service is running (green status)

### 400 Bad Request?
→ Verify CSV has required columns

### Env var not working?
→ Use correct prefix: `NEXT_PUBLIC_` or `VITE_` or `REACT_APP_`

## 📚 Documentation Files

- `RAILWAY_VERCEL_SETUP.md` - Complete setup guide
- `API_INTEGRATION.md` - Frontend integration details
- `VERIFY_DEPLOYMENT.md` - Deployment checklist
- `frontend-example.js` - Code examples
- `test_api.py` - API testing script

## 🎯 Success Checklist

- [ ] Backend deployed to Railway
- [ ] Health endpoint returns 200 OK
- [ ] ALLOWED_ORIGINS set in Railway
- [ ] API_URL set in Vercel
- [ ] Frontend can upload files
- [ ] No CORS errors in console
- [ ] Results display correctly

---

**Need help?** Check the detailed guides or visit:
- Railway: https://docs.railway.app
- API Docs: https://your-app.up.railway.app/docs
