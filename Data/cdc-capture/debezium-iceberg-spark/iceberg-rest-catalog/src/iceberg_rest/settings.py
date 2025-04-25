from pydantic import (
    Field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # General settings
    CATALOG_NAME: str = Field(default="default")
    CATALOG_WAREHOUSE: str = Field(
        default="s3://warehouse/rest", examples=["s3://warehouse/rest"]
    )

    # JDBC settings
    CATALOG_JDBC_URI: str = Field(
        default="sqlite:////tmp/warehouse/pyiceberg_catalog.db",
        examples=[
            "postgresql://pguser:password@postgres:5432/iceberg_db",
            "mysql://dbuser:password@mysql:3306/iceberg_db",
        ],
    )
    CATALOG_JDBC_USER: str = Field(default="user")
    CATALOG_JDBC_PASSWORD: str = Field(default="password")

    # S3 settings
    AWS_ACCESS_KEY_ID: str = Field(default="admin")
    AWS_SECRET_ACCESS_KEY: str = Field(default="password")
    AWS_REGION: str = Field(default="us-east-1")
    CATALOG_S3_ENDPOINT: str = Field(default="http://127.0.0.1:9000")


settings = Settings()
