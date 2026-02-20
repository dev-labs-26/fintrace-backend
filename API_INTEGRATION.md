# API Integration Guide: Railway Backend + Vercel Frontend

## Overview

This guide ensures your FastAPI backend (Railway) and frontend (Vercel) communicate properly.

## Backend API Endpoints

### Base URL
After Railway deployment: `https://your-app.up.railway.app`

### Available Endpoints

#### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "fraudai-backend"
}
```

**Usage:**
```javascript
// Frontend code
const response = await fetch('https://your-app.up.railway.app/health');
const data = await response.json();
console.log(data.status); // "ok"
```

---

#### 2. Analyze Transactions (Main Endpoint)
```
POST /analyze
Content-Type: multipart/form-data
```

**Request:**
- Field name: `file`
- Accepted types: `.csv`, `.tsv`, `.xlsx`, `.xls`
- Required columns: `transaction_id`, `sender_id`, `receiver_id`, `amount`, `timestamp`

**Response Schema:**
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
  },
  "transactions": []
}
```

**Frontend Integration (React/Next.js):**

```javascript
// Example: Upload CSV file from frontend
async function analyzeTransactions(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('https://your-app.up.railway.app/analyze', {
      method: 'POST',
      body: formData,
      // Note: Don't set Content-Type header - browser sets it automatically with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis failed');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error analyzing transactions:', error);
    throw error;
  }
}

// Usage in component
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const results = await analyzeTransactions(file);
    console.log('Suspicious accounts:', results.suspicious_accounts);
    console.log('Fraud rings:', results.fraud_rings);
    console.log('Summary:', results.summary);
  } catch (error) {
    alert('Error: ' + error.message);
  }
};
```

**Frontend Integration (Vanilla JS):**

```javascript
// HTML
<input type="file" id="csvFile" accept=".csv,.xlsx,.xls,.tsv" />
<button onclick="uploadFile()">Analyze</button>

// JavaScript
async function uploadFile() {
  const fileInput = document.getElementById('csvFile');
  const file = fileInput.files[0];
  
  if (!file) {
    alert('Please select a file');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('https://your-app.up.railway.app/analyze', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();
    displayResults(data);
  } catch (error) {
    alert('Error: ' + error.message);
  }
}

function displayResults(data) {
  console.log('Analysis complete!');
  console.log('Suspicious accounts:', data.suspicious_accounts.length);
  console.log('Fraud rings detected:', data.fraud_rings.length);
  console.log('Processing time:', data.summary.processing_time_seconds + 's');
}
```

---

#### 3. Export to CSV
```
POST /export/csv
Content-Type: application/json
```

**Request Body:**
```json
{
  "suspicious_accounts": [...],
  "fraud_rings": [...],
  "summary": {...}
}
```

**Response:**
- Content-Type: `text/csv`
- Downloads as `fraud_analysis.csv`

---

#### 4. API Documentation
```
GET /docs     - Swagger UI (interactive)
GET /redoc    - ReDoc (alternative docs)
```

## CORS Configuration

### For Development (Local Testing)

Backend `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### For Production (Vercel + Railway)

Railway Environment Variables:
```bash
ALLOWED_ORIGINS=https://yourapp.vercel.app,https://yourapp-git-main-yourname.vercel.app,https://yourapp-preview.vercel.app
```

**Important:** Include all Vercel domains:
- Production: `https://yourapp.vercel.app`
- Git branch: `https://yourapp-git-main-yourname.vercel.app`
- Preview: `https://yourapp-preview-*.vercel.app` (use wildcard or specific URLs)

### Setting CORS in Railway

1. Go to your Railway project
2. Click on your service
3. Go to "Variables" tab
4. Add new variable:
   - Key: `ALLOWED_ORIGINS`
   - Value: `https://yourapp.vercel.app` (or comma-separated list)
5. Redeploy (Railway auto-redeploys on variable changes)

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "detail": "Missing required columns: ['amount', 'timestamp']"
}
```

**Cause:** Invalid CSV format or missing columns

**Solution:** Ensure CSV has required columns:
- `transaction_id`
- `sender_id` (or aliases: `from_account`, `source_id`)
- `receiver_id` (or aliases: `to_account`, `destination_id`)
- `amount`
- `timestamp`

#### 400 Bad Request - File Type
```json
{
  "detail": "Unsupported file type. Allowed: CSV, TSV, XLSX, XLS. Got: file.txt"
}
```

**Cause:** Wrong file extension

**Solution:** Only upload `.csv`, `.tsv`, `.xlsx`, or `.xls` files

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

**Cause:** Server-side processing error

**Solution:** Check Railway logs for details

#### CORS Error (Browser Console)
```
Access to fetch at 'https://your-app.up.railway.app/analyze' from origin 'https://yourapp.vercel.app' 
has been blocked by CORS policy
```

**Cause:** Frontend domain not in `ALLOWED_ORIGINS`

**Solution:** Add your Vercel domain to Railway's `ALLOWED_ORIGINS` environment variable

## Testing the API

### Using cURL

```bash
# Health check
curl https://your-app.up.railway.app/health

# Analyze transactions
curl -X POST https://your-app.up.railway.app/analyze \
  -F "file=@test_transactions.csv"

# With verbose output
curl -v -X POST https://your-app.up.railway.app/analyze \
  -F "file=@test_transactions.csv"
```

### Using Postman

1. Create new request
2. Method: `POST`
3. URL: `https://your-app.up.railway.app/analyze`
4. Body → form-data
5. Key: `file` (type: File)
6. Value: Select your CSV file
7. Send

### Using Python

```python
import requests

# Health check
response = requests.get('https://your-app.up.railway.app/health')
print(response.json())

# Analyze transactions
with open('test_transactions.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'https://your-app.up.railway.app/analyze',
        files=files
    )
    
if response.ok:
    data = response.json()
    print(f"Suspicious accounts: {len(data['suspicious_accounts'])}")
    print(f"Fraud rings: {len(data['fraud_rings'])}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Frontend Environment Variables

### Vercel Environment Variables

In your Vercel project settings, add:

```bash
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
# or for React/Vite
VITE_API_URL=https://your-app.up.railway.app
```

### Using in Frontend Code

```javascript
// Next.js
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Vite/React
const API_URL = import.meta.env.VITE_API_URL;

// Usage
const response = await fetch(`${API_URL}/analyze`, {
  method: 'POST',
  body: formData
});
```

## Sample CSV Format

Create `test_transactions.csv`:

```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TX001,ACC_A,ACC_B,500.00,2025-01-01 09:00:00
TX002,ACC_B,ACC_C,490.00,2025-01-01 10:00:00
TX003,ACC_C,ACC_A,480.00,2025-01-01 11:00:00
TX004,ACC_D,ACC_E,1000.00,2025-01-02 08:00:00
TX005,ACC_E,ACC_F,950.00,2025-01-02 09:00:00
```

## Performance Considerations

- **File Size:** Optimized for files up to 10,000 transactions
- **Processing Time:** Typically 2-10 seconds depending on data complexity
- **Max File Size:** Railway default is 100MB (configurable)
- **Timeout:** 100 seconds (configured in railway.toml)

## Security Best Practices

1. **Always use HTTPS** - Railway provides this automatically
2. **Validate file size on frontend** before uploading
3. **Set specific CORS origins** - Don't use `*` in production
4. **Rate limiting** - Consider adding rate limiting for production
5. **File validation** - Frontend should validate file type before upload

## Troubleshooting Checklist

- [ ] Railway service is deployed and running
- [ ] Health check endpoint returns 200 OK
- [ ] ALLOWED_ORIGINS includes your Vercel domain
- [ ] Frontend uses correct Railway URL
- [ ] File has correct format and required columns
- [ ] CORS headers are present in response
- [ ] No browser console errors
- [ ] Railway logs show no errors

## Complete Integration Example

```javascript
// frontend/src/api/fraud-detection.js

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

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

export async function exportToCSV(analysisData) {
  const response = await fetch(`${API_URL}/export/csv`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(analysisData),
  });

  if (!response.ok) {
    throw new Error('Export failed');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'fraud_analysis.csv';
  a.click();
}
```

## Support

- Backend API Docs: `https://your-app.up.railway.app/docs`
- Railway Dashboard: https://railway.app/dashboard
- Vercel Dashboard: https://vercel.com/dashboard

---

**Your API is ready for production use with Railway + Vercel! 🚀**
