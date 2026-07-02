import os
from dotenv import load_dotenv

# Load env variables from root directory
load_dotenv()

class Settings:
    # Business Central OAuth & Base URL settings
    BC_CLIENT_ID: str = os.getenv("BC_CLIENT_ID", "")
    BC_CLIENT_SECRET: str = os.getenv("BC_CLIENT_SECRET", "")
    BC_ACCESS_TOKEN_URL: str = os.getenv("BC_ACCESS_TOKEN_URL", "")
    BC_SCOPE: str = os.getenv("BC_SCOPE", "https://api.businesscentral.dynamics.com/.default")
    BC_BASE_URL: str = os.getenv("BC_BASE_URL", "")

    # PostgreSQL Database settings
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "1234")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "orient_analytics")

    @property
    def database_url(self) -> str:
        import urllib.parse
        escaped_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"postgresql+psycopg2://{self.DB_USER}:{escaped_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
