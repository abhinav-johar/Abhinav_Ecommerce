import os
from dotenv import load_dotenv
import ssl
from pathlib import Path
from sqlalchemy.engine import URL

load_dotenv()


class Config:
    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() == "true"



    SECRET_KEY=os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is missing . Set it in your .env file."
        )


    DB_USER=os.getenv("DB_USER")
    DB_PASSWORD=os.getenv("DB_PASSWORD")
    DB_HOST=os.getenv("DB_HOST")
    DB_NAME=os.getenv("DB_NAME")
    DB_PORT=os.getenv("DB_PORT","3306")
    PORT=os.getenv("PORT","5000")

    if not all( [DB_USER , DB_PASSWORD , DB_HOST , DB_NAME] ):
        raise RuntimeError(
            "Database configuration is incomplete."
            "Check DB_USER , DB_PASSWORD , DB_HOST , DB_NAME."
        )


    SQLALCHEMY_DATABASE_URI = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


    BASE_DIR = Path(__file__).resolve().parent.parent
    CA_CERT_PATH = BASE_DIR / "ca.pem"

    SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {
        "ssl": {
            "ca": str(CA_CERT_PATH),
            "check_hostname": True,
            "verify_mode": ssl.CERT_REQUIRED,
        }
    }
}

    SQLALCHEMY_TRACK_MODIFICATIONS=False

    DEBUG = os.getenv("DEBUG", "False") == "True"


    
    UPLOAD_FOLDER = os.path.join('app', 'static', 'images', 'products')
    BANNER_FOLDER = os.path.join('app', 'static', 'images', 'banners')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}



    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB