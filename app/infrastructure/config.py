import os

from dotenv import load_dotenv

load_dotenv()
EVENTS_API_KEY = os.getenv("EVENTS_API_KEY")
CLIENT_HOST = os.getenv("EVENTS_HOST")
CAPASHINO_HOST = os.getenv("CAPASHINO_HOST")
SENTRY = os.getenv("SENTRY_DSN")
