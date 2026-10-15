# App settings in one place.
DATABASE_URL = "sqlite:///./links.db"

# What gets put in front of the code when we hand a short link back.
BASE_URL = "http://127.0.0.1:8000"

# Database ids start at 1, which would give 1 character codes like "1", "2", "3".
# Adding a big offset before encoding makes every code start at 6 characters.
ID_OFFSET = 1_000_000_000

# How many code -> URL lookups to keep in memory (stand-in for Redis).
CACHE_SIZE = 10_000

# Custom aliases that would clash with real routes.
RESERVED_ALIASES = {"docs", "redoc", "openapi.json", "shorten", "stats", "health"}
