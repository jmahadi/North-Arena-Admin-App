import os
import secrets

class Settings:
    database_url: str = 'postgresql+asyncpg://postgres.gmutjptigzeoqaweuffv:northarena2021!@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
    SECRET_KEY: str = secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI: str = os.getenv('DATABASE_URL', database_url)

settings = Settings()
