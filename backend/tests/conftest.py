import os

# Must be set before app modules read settings. Test-only value, not a real credential.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test")
