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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    return {"status": "ok", "service": "fraudai-backend"}
