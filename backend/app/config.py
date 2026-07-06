import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


def parse_cors_origins(v) -> List[str]:
    if isinstance(v, list):
        return [str(item) for item in v]
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        return [item.strip() for item in v.split(",") if item.strip()]
    return []


class Settings(BaseSettings):
    # MySQL Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "MYSQL"
    mysql_database: str = "ds_platform"

    # JWT
    secret_key: str = "ds-platform-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7

    # CORS
    backend_cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://dataset.agi-fbhc.com",
        "http://dataset.agi-fbhc.com",
    ]

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Alibaba Cloud image segmentation
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    aliyun_imageseg_endpoint: str = "imageseg.cn-shanghai.aliyuncs.com"
    aliyun_imageseg_region: str = "cn-shanghai"

    # Storage
    storage_root: str = ""  # 外部存储路径，如 /mnt/data/storage，留空则用代码默认路径

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _validate_cors(cls, v):
        return parse_cors_origins(v)

    @property
    def database_url(self) -> str:
        return (
            "mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
