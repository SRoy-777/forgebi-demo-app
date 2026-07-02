import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = None
connection = None

if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    import urllib.parse
    escaped_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{escaped_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("PostgreSQL Connected Successfully!")
else:
    # STANDALONE DEMO MODE FALLBACK
    DATABASE_URL = "sqlite:///./demo_database.db"
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("Demo Mode: Standalone SQLite Database Connected Successfully!")
