import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci"
    }
    
    JWT_SECRET_KEY = os.getenv("JWT_SECRET","Default")
    
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    URL = os.getenv("URL")
    API_KEY = os.getenv("API_KEY")
    API_URL = os.getenv("API_URL")
    IP = os.getenv("IP")
    URL = os.getenv("URL")
