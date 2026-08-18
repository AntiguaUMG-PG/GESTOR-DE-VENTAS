import os
from typing import Optional

class Settings:
    # Base de datos
    DB_HOST: str = os.getenv("DB_HOST", "dpg-d3pcushr0fns73ahqf10-a.oregon-postgres.render.com")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "gestor_pedidos")
    DB_USER: str = os.getenv("DB_USER", "manager_sebaot")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "ovRHNzwztDohjnzPWt70QwLxBwf7bEAc")
    
    # Aplicación
    SECRET_KEY: str = os.getenv("SECRET_KEY", "Natha0908I45")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()