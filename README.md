# Fintrace – Graph-Based Financial Forensics Engine

> **Money Muling Detection API**
> A production-ready FastAPI backend that detects financial crime rings using
> graph theory, temporal analysis, and intelligent suspicion scoring.

---

## Table of Contents
1. [Features](#features)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Algorithm Explanation](#algorithm-explanation)
5. [Complexity Analysis](#complexity-analysis)
6. [Setup & Run](#setup--run)
7. [Docker & Deployment](#docker--deployment)
8. [Example CSV & Response](#example-csv--response)

---

## Features

- Multi-format file support: CSV, TSV, Excel (.xlsx, .xls)
- Flexible column name mapping with aliases
- Three core detection algorithms: cycle detection, smurfing, layered shell networks
- Weighted suspicion scoring with false-positive reduction
- CSV export functionality for analysis results
- Interactive API documentation (Swagger UI)
- Health check endpoints for monitoring
- CORS support for frontend integration

---

## Architecture

```
.
├── main.py                  # FastAPI app factory + CORS + router mount
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container build configuration
├── Procfile                # Deployment process configuration
├── railway.toml            # Railway deployment settings
├── nixpacks.toml           # Nixpacks build configuration
├── runtime.txt             # Python version specification
├── .env.example            # Environment variables template
├── test_transactions.csv   # Sample test data
├── validate_output.py      # Output validation script
└── app/
    ├── api/
    │   └── routes.py        # POST /analyze, GET /health, POST /export/csv
    ├── core/
    │   └── config.py        # All tunable constants & thresholds
    ├── models/
    │   └── schemas.py       # Pydantic v2 response schemas
    └── services/
        ├── csv_parser.py    # Multi-format file parser (CSV/TSV/Excel)
        ├── graph_builder.py # NetworkX DiGraph construction
        ├── pattern_detector.py  # Cycle / Smurfing / Shell detection
        ├── scoring_engine.py    # Weighted suspicion scoring + FP reduction
        └── json_formatter.py   # Assembles final AnalysisResponse
```

Data flow for a single request:

```
File Upload (CSV/TSV/Excel)
   │
   ▼
csv_parser.parse_csv()          ← validates columns, types, timestamps
   │                              supports CSV, TSV, XLSX, XLS formats
   │                              flexible column name mapping
   │ DataFrame
   ▼
graph_builder.build_graph()     ← DiGraph: nodes=accounts, edges=transactions
   │ nx.DiGraph + degree_map
   ▼
pattern_detector.run_all_detectors()
   ├── detect_cycles()          ← Johnson's algorithm, length 3–5
   ├── detect_smurfing()        ← two-pointer sliding window, 72 h
   └── detect_layered_shells()  ← DFS up to 5 hops, low-degree filter
   │ [RawRing, ...]
   ▼
scoring_engine.score_accounts() ← weighted model + FP heuristic
scoring_engine.compute_ring_risk_scores()
   │ score_map, pattern_map, ring_map
   ▼
json_formatter.build_response() ← Pydantic validation → JSON
```

---

## API Reference

### `POST /analyze`

Analyzes financial transactions for money muling patterns.

| Property       | Value                                           |
|----------------|-------------------------------------------------|
| URL            | `http://localhost:8000/analyze`                 |
| Method         | `POST`                                          |
| Content-Type   | `multipart/form-data`                           |
| Field name     | `file`                                          |
| Accepted types | `.csv`, `.tsv`, `.xlsx`, `.xls`                 |

#### Supported File Formats
- CSV (Comma-Separated Values)
- TSV (Tab-Separated Values)
- Excel (.xlsx, .xls)

#### Required Columns
The file must contain these columns (or their aliases):
- `transaction_id` (aliases: txn_id, tx_id, id, transaction_number)
- `sender_id` (aliases: from_account, source_id, sender, from_id, payer_id)
- `receiver_id` (aliases: to_account, destination_id, receiver, to_id, payee_id)
- `amount` (aliases: value, transaction_amount, sum)
- `timestamp` (aliases: date, datetime, transaction_date, time, created_at)

#### Supported Timestamp Formats
- `YYYY-MM-DD HH:MM:SS`
- `YYYY-MM-DD HH:MM:SS.ffffff`
- `YYYY/MM/DD HH:MM:SS`
- `DD-MM-YYYY HH:MM:SS`
- `DD/MM/YYYY HH:MM:SS`
- `YYYY-MM-DD`
- `DD-MM-YYYY`
- `DD/MM/YYYY`
- `MM/DD/YYYY`

#### Request (curl)
```bash
curl -X POST http://localhost:8000/analyze \
     -F "file=@transactions.csv"
```

#### Response schema (200 OK)
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
    "processing_time_seconds": 2.3
  },
  "transactions": []
}
```

#### Error (400)
```json
{ "detail": "Missing required columns: ['amount', 'timestamp']" }
```

### `GET /health`

Health check endpoint for monitoring and load balancers.

Returns:
```json
{
  "status": "healthy",
  "service": "Financial Forensics Engine",
  "version": "1.0.0"
}
```

### `POST /export/csv`

Exports analysis results as CSV format for download.

Request body: `AnalysisResponse` JSON object

Returns: CSV file with suspicious accounts, fraud rings, and summary data.

### `GET /docs`

Interactive Swagger UI playground for API testing and exploration.

### `GET /redoc`

Alternative API documentation using ReDoc.

---

## Algorithm Explanation

### 1. Cycle Detection (Circular Fund Routing)
Uses **Johnson's algorithm** (`networkx.simple_cycles`) which runs in
O((V + E)(C + 1)) time where C = number of elementary circuits.

Cycles of length 3–5 are kept.  Each unique cycle becomes a `RING_XXX` with:
- `pattern_type = "cycle"`
- per-account label `"cycle_length_N"`
- base suspicion contribution **+40 points**

### 2. Smurfing Detection (Fan-in / Fan-out)
A **two-pointer sliding window** scans each account's sorted transaction list.
If ≥ 10 unique counterparties appear within any 72-hour window the account is
flagged.

- Fan-in  (receiver side): label `"fan_in_smurfing"`
- Fan-out (sender side):   label `"fan_out_smurfing"`
- Base suspicion contribution: **+30 points**

### 3. Layered Shell Network Detection
A **DFS** from every source node explores chains up to 5 hops.  A chain is
flagged when:
- Length ≥ 3 hops
- All *intermediate* nodes have total degree ≤ 3 (shell / mule characteristics)

Label: `"layered_shell_chain"` | Base contribution: **+25 points**

### 4. False-Positive Merchant Reduction
Accounts are classified as **likely legitimate merchants** when:
1. Active for ≥ 30 days
2. Transaction amount CV ≤ 0.30 (consistent pricing)
3. Inter-arrival time CV ≤ 0.50 (regular cadence)

Matching accounts receive a **−25 point** reduction to minimise false positives.

### 5. Suspicion Scoring Model
```
Score = Σ(pattern weights) + velocity_burst + centrality_anomaly − merchant_fp
Clamped to [0, 100], rounded to 1 decimal place.
```

| Signal                      | Weight |
|-----------------------------|--------|
| Cycle participation         | +40    |
| Smurfing (fan-in/out)       | +30    |
| Layered shell chain         | +25    |
| High-velocity burst (24 h)  | +20    |
| Degree centrality anomaly   | +10    |
| Merchant FP reduction       | −25    |

---

## Complexity Analysis

| Component                | Time Complexity        | Notes                              |
|--------------------------|------------------------|------------------------------------|
| CSV parsing              | O(n)                   | Single Pandas read pass            |
| Graph construction       | O(n)                   | One edge per transaction row       |
| Cycle detection          | O((V+E)(C+1))          | Johnson's; C = circuit count       |
| Smurfing (sliding window)| O(n log n)             | Sort + two-pointer per account     |
| Shell detection (DFS)    | O(V · E^d)             | d = max depth (5); pruned early    |
| Scoring                  | O(A + R)               | A=accounts, R=rings                |
| **Total (typical)**      | **< 10 s @ 10k rows**  | Measured on M1 MacBook, 10k TX     |

---

## Setup & Run

### Prerequisites
- Python 3.10 or newer
- pip

### Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables (optional)

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Available variables:
- `PORT` – Server port (default: 8000)
- `ALLOWED_ORIGINS` – CORS allowed origins (default: *)

### Run (development)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server is available at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

Alternative docs: **http://localhost:8000/redoc**

### Run (production)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Docker & Deployment

### Docker

Build and run using Docker:

```bash
# Build image
docker build -t fintrace-backend .

# Run container
docker run -p 8000:8000 fintrace-backend
```

### Railway Deployment

This project is configured for Railway deployment with:
- `railway.toml` – Railway-specific configuration
- `nixpacks.toml` – Build configuration
- `Procfile` – Process definition
- `runtime.txt` – Python version specification

Deploy to Railway:
```bash
railway up
```

### Health Checks

The `/health` endpoint returns service status for monitoring:
```bash
curl http://localhost:8000/health
```

---

## Example CSV & Response

### `transactions.csv`
```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TX001,ACC_A,ACC_B,500.00,2025-01-01 09:00:00
TX002,ACC_B,ACC_C,490.00,2025-01-01 10:00:00
TX003,ACC_C,ACC_A,480.00,2025-01-01 11:00:00
TX004,ACC_D,ACC_A,1000.00,2025-01-02 08:00:00
TX005,ACC_E,ACC_A,1100.00,2025-01-02 08:30:00
```

### Response excerpt
```json
{
  "suspicious_accounts": [
    {"account_id": "ACC_A", "suspicion_score": 65.0,
     "detected_patterns": ["cycle_length_3"], "ring_id": "RING_001"},
    {"account_id": "ACC_B", "suspicion_score": 40.0,
     "detected_patterns": ["cycle_length_3"], "ring_id": "RING_001"},
    {"account_id": "ACC_C", "suspicion_score": 40.0,
     "detected_patterns": ["cycle_length_3"], "ring_id": "RING_001"}
  ],
  "fraud_rings": [
    {"ring_id": "RING_001", "member_accounts": ["ACC_A","ACC_B","ACC_C"],
     "pattern_type": "cycle", "risk_score": 48.3, "member_count": 3}
  ],
  "summary": {
    "total_accounts_analyzed": 5,
    "suspicious_accounts_flagged": 3,
    "fraud_rings_detected": 1,
    "processing_time_seconds": 0.042
  },
  "transactions": []
}
```

---

## Configuration

All detection thresholds and scoring weights are centralized in `app/core/config.py`:

### Graph Construction
- `MAX_CYCLE_LENGTH` = 5
- `MIN_CYCLE_LENGTH` = 3

### Smurfing Detection
- `SMURFING_MIN_ENDPOINTS` = 10 (minimum unique counterparties)
- `SMURFING_WINDOW_HOURS` = 72 (detection window)

### Layered Shell Detection
- `SHELL_MIN_HOPS` = 3 (minimum chain depth)
- `SHELL_MAX_HOPS` = 5 (maximum search depth)
- `SHELL_MAX_DEGREE` = 3 (max degree for shell nodes)

### Velocity Burst
- `VELOCITY_WINDOW_HOURS` = 24
- `VELOCITY_MIN_TX` = 10 (minimum transactions to trigger)

### Scoring Weights
- `SCORE_CYCLE` = 40.0
- `SCORE_SMURFING` = 30.0
- `SCORE_VELOCITY` = 20.0
- `SCORE_SHELL` = 25.0
- `SCORE_CENTRALITY` = 10.0
- `SCORE_FP_MERCHANT` = -25.0 (false-positive reduction)

### Merchant Heuristics
- `MERCHANT_MIN_LIFETIME_DAYS` = 30
- `MERCHANT_AMOUNT_CV_THRESHOLD` = 0.3
- `MERCHANT_SPACING_CV_THRESHOLD` = 0.5

---

## Dependencies

Core libraries (see `requirements.txt`):
- `fastapi>=0.111.0` – Web framework
- `uvicorn[standard]>=0.29.0` – ASGI server
- `networkx>=3.3` – Graph algorithms
- `pandas>=2.2.0` – Data processing
- `numpy>=1.26.0` – Numerical operations
- `pydantic>=2.7.0` – Data validation
- `python-multipart>=0.0.9` – File upload support
- `openpyxl>=3.1.0` – Excel file support
- `aiofiles>=23.2.1` – Async file operations

---

## Testing

Test the API with the included sample data:

```bash
curl -X POST http://localhost:8000/analyze \
     -F "file=@test_transactions.csv"
```

Validate output format:
```bash
python validate_output.py
```

---

## Project Structure Details

### Services Layer

#### `csv_parser.py`
- Multi-format file parsing (CSV, TSV, Excel)
- Flexible column name mapping with aliases
- Multiple timestamp format support
- Data validation and type coercion
- Automatic deduplication

#### `graph_builder.py`
- NetworkX DiGraph construction
- Transaction aggregation on edges
- Degree map computation
- Efficient sparse graph representation

#### `pattern_detector.py`
- Cycle detection using Johnson's algorithm
- Sliding window smurfing detection
- DFS-based layered shell network detection
- Unique ring ID generation

#### `scoring_engine.py`
- Weighted suspicion scoring model
- Velocity burst detection
- Degree centrality anomaly detection
- Merchant false-positive reduction
- Ring risk score computation

#### `json_formatter.py`
- Pydantic-based response assembly
- Schema validation
- JSON serialization

---

*Advanced Money Muling Detection Platform*
