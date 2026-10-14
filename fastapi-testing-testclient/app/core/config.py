# Settings the whole app reads from one place.
import os

APP_NAME = "Task Tracker API"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
API_KEY = os.getenv("API_KEY", "dev-key")  # write endpoints need this in the X-API-Key header
MAX_OPEN_TASKS = 5
