import os
from dotenv import load_dotenv

load_dotenv()


class config:
    SECRET_KEY=os.getenv("SECRET_KEY")


    DB_USER=os.getenv("DB_USER")
    DB_PASSWORD=os.getenv("DB_PASSWORD")
    DB_HOST=os.getenv("DB_HOST")
    DB_NAME=os.getenv("DB_NAME")
    DB_PORT=os.getenv("DB_PORT","3306")
    PORT=os.getenv("PORT","5000")


    SQLALCHEMY_DATABASE_URI=(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
                             f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    SQLALCHEMY_TRACK_MODIFICATIONS=False

    DEBUG = os.getenv("DEBUG", "False") == "True"


    
    UPLOAD_FOLDER = os.path.join('app', 'static', 'images', 'products')
    BANNER_FOLDER = os.path.join('app', 'static', 'images', 'banners')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}



    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB