/**
 * Frontend Integration Example for Fintrace API
 * Works with React, Next.js, Vue, or vanilla JavaScript
 * 
 * Usage:
 * 1. Set your Railway backend URL in environment variables
 * 2. Import and use these functions in your components
 * 3. Handle file uploads and display results
 */

// ============================================================================
// Configuration
// ============================================================================

// For Next.js: Use NEXT_PUBLIC_ prefix
const API_URL = process.env.NEXT_PUBLIC_API_URL || 
                // For Vite/React: Use VITE_ prefix
                import.meta.env?.VITE_API_URL || 
                // Fallback for development
                'http://localhost:8000';

// ============================================================================
// API Functions
// ============================================================================

/**
 * Check if the backend API is healthy and reachable
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_URL}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
}

/**
 * Analyze transactions from a CSV file
 * @param {File} file - CSV file containing transaction data
 * @returns {Promise<Object>} Analysis results
 */
export async function analyzeTransactions(file) {
  // Validate file
  if (!file) {
    throw new Error('No file provided');
  }

  const allowedTypes = [
    'text/csv',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];

  const allowedExtensions = ['.csv', '.tsv', '.xlsx', '.xls'];
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

  if (!allowedExtensions.includes(fileExtension)) {
    throw new Error(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
  }

  // Create form data
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Analysis failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Analysis error:', error);
    throw error;
  }
}

/**
 * Export analysis results to CSV
 * @param {Object} analysisData - Analysis results from analyzeTransactions
 */
export async function exportToCSV(analysisData) {
  try {
    const response = await fetch(`${API_URL}/export/csv`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(analysisData),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }

    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fraud_analysis.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export error:', error);
    throw error;
  }
}

// ============================================================================
// React Component Example
// ============================================================================

/**
 * Example React component for file upload and analysis
 */
export function FraudAnalysisUploader() {
  const [file, setFile] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState(null);
  const [error, setError] = React.useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
    setError(null);
    setResults(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await analyzeTransactions(file);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!results) return;

    try {
      await exportToCSV(results);
    } catch (err) {
      setError('Export failed: ' + err.message);
    }
  };

  return (
    <div className="fraud-analysis-uploader">
      <h2>Transaction Analysis</h2>
      
      {/* File Upload */}
      <div className="upload-section">
        <input
          type="file"
          accept=".csv,.xlsx,.xls,.tsv"
          onChange={handleFileChange}
          disabled={loading}
        />
        <button onClick={handleUpload} disabled={!file || loading}>
          {loading ? 'Analyzing...' : 'Analyze Transactions'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div className="results-section">
          <h3>Analysis Results</h3>
          
          {/* Summary */}
          <div className="summary">
            <h4>Summary</h4>
            <p>Total Accounts: {results.summary.total_accounts_analyzed}</p>
            <p>Suspicious Accounts: {results.summary.suspicious_accounts_flagged}</p>
            <p>Fraud Rings: {results.summary.fraud_rings_detected}</p>
            <p>Processing Time: {results.summary.processing_time_seconds.toFixed(3)}s</p>
          </div>

          {/* Suspicious Accounts */}
          {results.suspicious_accounts.length > 0 && (
            <div className="suspicious-accounts">
              <h4>Suspicious Accounts</h4>
              <table>
                <thead>
                  <tr>
                    <th>Account ID</th>
                    <th>Suspicion Score</th>
                    <th>Patterns</th>
                    <th>Ring ID</th>
                  </tr>
                </thead>
                <tbody>
                  {results.suspicious_accounts.map((account) => (
                    <tr key={account.account_id}>
                      <td>{account.account_id}</td>
                      <td>{account.suspicion_score}</td>
                      <td>{account.detected_patterns.join(', ')}</td>
                      <td>{account.ring_id || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Fraud Rings */}
          {results.fraud_rings.length > 0 && (
            <div className="fraud-rings">
              <h4>Fraud Rings</h4>
              <table>
                <thead>
                  <tr>
                    <th>Ring ID</th>
                    <th>Pattern Type</th>
                    <th>Risk Score</th>
                    <th>Members</th>
                  </tr>
                </thead>
                <tbody>
                  {results.fraud_rings.map((ring) => (
                    <tr key={ring.ring_id}>
                      <td>{ring.ring_id}</td>
                      <td>{ring.pattern_type}</td>
                      <td>{ring.risk_score}</td>
                      <td>{ring.member_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Export Button */}
          <button onClick={handleExport}>
            Export to CSV
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Vanilla JavaScript Example
// ============================================================================

/**
 * Example vanilla JavaScript implementation
 * Add this to your HTML page
 */
export function initVanillaJS() {
  const fileInput = document.getElementById('csvFile');
  const uploadBtn = document.getElementById('uploadBtn');
  const resultsDiv = document.getElementById('results');

  uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
      alert('Please select a file');
      return;
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Analyzing...';

    try {
      const results = await analyzeTransactions(file);
      displayResults(results);
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.textContent = 'Analyze';
    }
  });

  function displayResults(data) {
    resultsDiv.innerHTML = `
      <h3>Analysis Complete</h3>
      <div class="summary">
        <p><strong>Total Accounts:</strong> ${data.summary.total_accounts_analyzed}</p>
        <p><strong>Suspicious Accounts:</strong> ${data.summary.suspicious_accounts_flagged}</p>
        <p><strong>Fraud Rings:</strong> ${data.summary.fraud_rings_detected}</p>
        <p><strong>Processing Time:</strong> ${data.summary.processing_time_seconds.toFixed(3)}s</p>
      </div>
      ${data.suspicious_accounts.length > 0 ? `
        <h4>Suspicious Accounts</h4>
        <ul>
          ${data.suspicious_accounts.map(acc => `
            <li>
              ${acc.account_id} - Score: ${acc.suspicion_score} 
              (${acc.detected_patterns.join(', ')})
            </li>
          `).join('')}
        </ul>
      ` : ''}
    `;
  }
}

// ============================================================================
// TypeScript Types (Optional)
// ============================================================================

/**
 * TypeScript type definitions for API responses
 */

/*
export interface SuspiciousAccount {
  account_id: string;
  suspicion_score: number;
  detected_patterns: string[];
  ring_id: string | null;
}

export interface FraudRing {
  ring_id: string;
  member_accounts: string[];
  pattern_type: string;
  risk_score: number;
  member_count: number;
}

export interface Summary {
  total_accounts_analyzed: number;
  suspicious_accounts_flagged: number;
  fraud_rings_detected: number;
  processing_time_seconds: number;
}

export interface AnalysisResponse {
  suspicious_accounts: SuspiciousAccount[];
  fraud_rings: FraudRing[];
  summary: Summary;
  transactions: any[];
}
*/

// ============================================================================
// Usage Instructions
// ============================================================================

/*
1. Set environment variables:
   - Next.js: NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
   - Vite: VITE_API_URL=https://your-app.up.railway.app

2. Import functions:
   import { analyzeTransactions, checkHealth } from './frontend-example';

3. Use in your components:
   const results = await analyzeTransactions(file);

4. Display results in your UI

5. Test CORS:
   - Ensure ALLOWED_ORIGINS is set in Railway
   - Include your Vercel domain in the list
*/
