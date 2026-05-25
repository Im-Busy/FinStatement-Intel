"""Project configuration constants and defaults."""

from pathlib import Path

DEFAULT_PERIODS = 5
DEFAULT_SOURCE = "edgar"
DEFAULT_UNIT = "millions"
DEFAULT_CURRENCY = "USD"

OUTPUT_DIR = Path("output")
DATA_DIR = Path("data")
MAPPING_DIR = DATA_DIR / "mapping"
SAMPLES_DIR = DATA_DIR / "samples"

SEC_BASE_URL = "https://data.sec.gov/api"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions"
SEC_USER_AGENT = "reading-cfs-is-bs/0.1.0 (contact@example.com)"

ACCOUNTING_EQ_TOLERANCE = 0.001
CF_RECONCILIATION_TOLERANCE = 0.005
VOLATILITY_THRESHOLD = 0.20

RATELIMIT_DELAY = 0.1
SURGING_DETECTION_THRESHOLD = 0.2
MARGIN_STABLE_BAND = 0.01

FUZZY_MATCH_THRESHOLD = 0.85
LOW_CONFIDENCE_THRESHOLD = 0.6
