"""
Core configuration and constants for the Financial Forensics Engine.
"""

# ─── Graph construction limits ────────────────────────────────────────────────
MAX_CYCLE_LENGTH = 5
MIN_CYCLE_LENGTH = 3

# ─── Smurfing detection parameters ────────────────────────────────────────────
SMURFING_MIN_ENDPOINTS = 10       # minimum unique senders (fan-in) or receivers (fan-out)
SMURFING_WINDOW_HOURS  = 72       # look-back / look-forward window in hours

# ─── Layered-shell detection parameters ───────────────────────────────────────
SHELL_MIN_HOPS        = 3         # minimum chain depth to flag
SHELL_MAX_HOPS        = 5         # maximum depth for path search
SHELL_MAX_DEGREE      = 3         # max degree for "intermediate/shell" node

# ─── Velocity burst parameters ────────────────────────────────────────────────
VELOCITY_WINDOW_HOURS = 24        # burst window
VELOCITY_MIN_TX       = 10        # minimum transactions in window to trigger burst flag

# ─── Scoring weights ──────────────────────────────────────────────────────────
SCORE_CYCLE            = 40.0
SCORE_SMURFING         = 30.0
SCORE_VELOCITY         = 20.0
SCORE_SHELL            = 25.0
SCORE_CENTRALITY       = 10.0
SCORE_FP_MERCHANT      = -25.0    # false-positive reduction

SCORE_MAX = 100.0
SCORE_MIN = 0.0

# ─── False-positive merchant heuristics ───────────────────────────────────────
MERCHANT_MIN_LIFETIME_DAYS   = 30   # account must be active for at least N days
MERCHANT_AMOUNT_CV_THRESHOLD = 0.3  # coefficient of variation ≤ this → evenly spaced amounts
MERCHANT_SPACING_CV_THRESHOLD = 0.5 # TX inter-arrival-time CV ≤ this → evenly spaced timing

# ─── Ring ID generation ────────────────────────────────────────────────────────
RING_ID_PREFIX = "RING"
