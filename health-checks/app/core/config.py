# App settings in one place. Each one can be changed with an environment variable.
import os

# The SQLite file the app reads and writes.
DB_PATH = os.getenv("DB_PATH", "app.db")

# An outside API the app calls. Here it's GitHub's public API, but in a real
# project it would be a payments API, an LLM API, an email service...
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "https://api.github.com")

# No single check is allowed to take longer than this.
# A health check that hangs is almost as bad as one that lies.
CHECK_TIMEOUT_SECONDS = float(os.getenv("CHECK_TIMEOUT_SECONDS", "2"))
