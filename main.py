"""
Financial Forensics Engine – FastAPI application entry point
"""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Fintrace – Graph-Based Financial Forensics Engine",
    description=(
        "Money Muling Detection API using graph theory, temporal analysis, "
        "and intelligent suspicion scoring. "
        "Detects circular fund routing, smurfing, and layered shell networks."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow the existing frontend dashboard to connect) ───────────────────
# For Railway + Vercel: Set ALLOWED_ORIGINS env var to your Vercel domain
# Example: ALLOWED_ORIGINS=https://yourapp.vercel.app,https://yourapp-preview.vercel.app
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ── Register routes ───────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    return {"status": "ok", "service": "fraudai-backend"}
