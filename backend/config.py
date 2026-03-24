from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    supabase_url: str = "http://localhost:54321"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # local dev default
    supabase_service_key: str = ""
    supabase_jwt_secret: str = "super-secret-jwt-token-with-at-least-32-characters-long"  # Supabase project JWT secret
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    database_url: str = "postgresql://postgres:postgres@localhost:54322/postgres"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
