class ConfigSettings:
    DB_URL = "postgresql://fastapi_user:password@localhost:5432/fastapi_db"
    TOKENS = {"token", "token1", "token2"}

config_settings = ConfigSettings()