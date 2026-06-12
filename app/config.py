from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/dollargate"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24       # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Payment (Paystack)
    PAYSTACK_SECRET_KEY: str = "sk_test_your_paystack_key"
    PAYSTACK_PUBLIC_KEY: str = "pk_test_your_paystack_key"

    # App
    APP_NAME: str = "DollarGate"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
