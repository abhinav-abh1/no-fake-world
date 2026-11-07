from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local dev default: the Docker database on host port 5433.
    database_url: str = "postgresql+psycopg://nfw:nfw_dev_password@127.0.0.1:5433/nfw"

    # Duplicate detection. Starting guesses: tune them on labelled pairs (evals/dedup_pairs.csv).
    dedup_min_cosine: float = 0.95
    dedup_min_jaccard: float = 0.3

    # Meaning-only matches below this similarity are not shown. Placeholder: tune on real queries.
    search_min_vector_score: float = 0.83

    # Story grouping: average cosine similarity needed inside a story, time window, history length.
    story_min_similarity: float = 0.85
    story_window_hours: float = 72.0
    story_days: int = 7

    # Near copies must also be close in time (see mark_duplicates).
    dedup_same_outlet_minutes: float = 30.0
    dedup_cross_outlet_hours: float = 6.0


settings = Settings()
