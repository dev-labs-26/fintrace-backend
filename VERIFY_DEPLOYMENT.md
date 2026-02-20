# Deployment Verification Checklist

## Pre-Deployment

- [ ] All files committed to Git
- [ ] `.env` file NOT committed (should be in .gitignore)
- [ ] `requirements.txt` is complete
- [ ] Code has no syntax errors

## Railway Deployment

### 1. Deploy Backend to Railway

```bash
# Option A: Via GitHub
git push origin main
# Then deploy from Railway dashboard

# Option B: Via Railway CLI
railway up
```

### 2. Get Your Railway URL

After deployment, Railway provides a URL like:
```
https://your-app.up.railway.app
```

### 3. Test Backend Endpoints

```bash
# Replace with your actual Railway URL
export RAILWAY_URL="https://your-app.up.railway.app"

# Test health check
curl $RAILWAY_URL/health

# Expected response:
# {"status":"ok","service":"fraudai-backend"}
```

### 4. Test API Documentation

Visit in browser:
```
https://your-app.up.railway.app/docs
```

You should see Swagger UI with all endpoints.

### 5. Test File Upload

Using the test script:
```bash
python3 test_api.py https://your-app.up.railway.app
```

Or using curl:
```bash
curl -X POST $RAILWAY_URL/analyze \
  -F "file=@test_transactions.csv"
```

## Frontend Integration (Vercel)

### 1. Set Environment Variable in Vercel

In your Vercel project settings:

**For Next.js:**
```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

**For Vite/React:**
```
VITE_API_URL=https://your-app.up.railway.app
```

### 2. Update CORS in Railway

In Railway dashboard → Variables:
```
ALLOWED_ORIGINS=https://yourapp.vercel.app
```

For multiple domains (production + preview):
```
ALLOWED_ORIGINS=https://yourapp.vercel.app,https://yourapp-git-main-yourname.vercel.app,https://yourapp-preview.vercel.app
```

### 3. Redeploy Backend

After setting ALLOWED_ORIGINS, Railway will automatically redeploy.

### 4. Test from Frontend

In your frontend code:

```javascript
// Test health check
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
const data = await response.json();
console.log(data); // Should show: {status: "ok", ...}

// Test file upload
const formData = new FormData();
formData.append('file', file);

const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analyze`, {
  method: 'POST',
  body: formData
});

const results = await response.json();
console.log(results);
```

## Verification Checklist

### Backend (Railway)

- [ ] Health endpoint returns 200 OK
  ```bash
  curl https://your-app.up.railway.app/health
  ```

- [ ] API docs are accessible
  ```
  https://your-app.up.railway.app/docs
  ```

- [ ] Analyze endpoint accepts CSV files
  ```bash
  curl -X POST https://your-app.up.railway.app/analyze \
    -F "file=@test_transactions.csv"
  ```

- [ ] CORS headers are present
  ```bash
  curl -I -X OPTIONS https://your-app.up.railway.app/analyze \
    -H "Origin: https://yourapp.vercel.app"
  ```

- [ ] No errors in Railway logs

### Frontend (Vercel)

- [ ] Environment variable is set (NEXT_PUBLIC_API_URL or VITE_API_URL)
- [ ] Frontend can reach backend health endpoint
- [ ] File upload works without CORS errors
- [ ] Results display correctly
- [ ] No console errors in browser

### CORS Troubleshooting

If you see CORS errors in browser console:

1. **Check ALLOWED_ORIGINS in Railway**
   - Go to Railway dashboard
   - Click your service
   - Go to Variables tab
   - Verify ALLOWED_ORIGINS includes your Vercel domain

2. **Check the exact domain**
   - Use the exact URL from browser address bar
   - Include https://
   - Don't include trailing slash
   - Example: `https://yourapp.vercel.app`

3. **Test CORS headers**
   ```bash
   curl -I -X OPTIONS https://your-app.up.railway.app/analyze \
     -H "Origin: https://yourapp.vercel.app" \
     -H "Access-Control-Request-Method: POST"
   ```
   
   Should return:
   ```
   Access-Control-Allow-Origin: https://yourapp.vercel.app
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   ```

4. **Redeploy after changes**
   - Railway auto-redeploys when you change variables
   - Wait for deployment to complete
   - Test again

## Common Issues

### Issue: "CORS policy blocked"

**Solution:**
1. Add your Vercel domain to ALLOWED_ORIGINS in Railway
2. Format: `https://yourapp.vercel.app` (no trailing slash)
3. For multiple domains, separate with commas
4. Wait for Railway to redeploy

### Issue: "Network error" or "Failed to fetch"

**Solution:**
1. Check Railway service is running (green status)
2. Test health endpoint directly: `curl https://your-app.up.railway.app/health`
3. Check Railway logs for errors
4. Verify URL is correct (no typos)

### Issue: "400 Bad Request - Missing columns"

**Solution:**
1. Verify CSV has required columns:
   - transaction_id
   - sender_id (or from_account, source_id)
   - receiver_id (or to_account, destination_id)
   - amount
   - timestamp
2. Check CSV format is valid
3. Ensure file is not empty

### Issue: "File upload fails"

**Solution:**
1. Check file size (should be < 100MB)
2. Verify file extension (.csv, .xlsx, .xls, .tsv)
3. Don't set Content-Type header manually (let browser set it)
4. Use FormData correctly:
   ```javascript
   const formData = new FormData();
   formData.append('file', file); // field name must be 'file'
   ```

## Success Criteria

Your deployment is successful when:

✅ Backend health check returns 200 OK  
✅ API documentation is accessible  
✅ File upload works from frontend  
✅ Results are returned correctly  
✅ No CORS errors in browser console  
✅ No errors in Railway logs  
✅ Processing completes in reasonable time (<30s)

## Performance Benchmarks

Expected performance:
- Health check: < 100ms
- Small CSV (100 rows): < 1s
- Medium CSV (1,000 rows): 1-3s
- Large CSV (10,000 rows): 5-10s

If processing takes longer:
- Check Railway logs for errors
- Verify CSV format is correct
- Consider optimizing data size

## Next Steps

After successful deployment:

1. **Monitor Performance**
   - Check Railway metrics dashboard
   - Monitor response times
   - Watch for errors in logs

2. **Set Up Alerts** (Optional)
   - Railway can notify you of downtime
   - Set up uptime monitoring (e.g., UptimeRobot)

3. **Optimize CORS**
   - Replace `*` with specific domains
   - Only allow your production domains

4. **Document API URL**
   - Share Railway URL with frontend team
   - Update frontend environment variables
   - Document in project README

5. **Test with Real Data**
   - Upload actual transaction files
   - Verify results are accurate
   - Check performance with larger datasets

---

**Your API is production-ready! 🚀**

For support:
- Railway Docs: https://docs.railway.app
- API Docs: https://your-app.up.railway.app/docs
- Test Script: `python3 test_api.py`
