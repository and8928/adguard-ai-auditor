from datetime import datetime, timezone


class AuditCache:
    """Stores the last fetched & cleaned data so that LLM analysis can be
    re-run without hitting the AdGuard API again."""

    def __init__(self):
        self.cleaned_data: dict | None = None
        self.fetch_time: datetime | None = None
        self.allowed_count: int = 0
        self.blocked_count: int = 0

    def store(self, cleaned: dict, allowed: int, blocked: int):
        self.cleaned_data = cleaned
        self.fetch_time = datetime.now(timezone.utc)
        self.allowed_count = allowed
        self.blocked_count = blocked

    def clear(self):
        self.cleaned_data = None
        self.fetch_time = None
        self.allowed_count = 0
        self.blocked_count = 0

    def has_data(self) -> bool:
        return self.cleaned_data is not None

    def status(self) -> dict:
        if not self.has_data():
            return {"has_data": False}
        return {
            "has_data": True,
            "fetch_time": self.fetch_time.isoformat() if self.fetch_time else None,
            "allowed_count": self.allowed_count,
            "blocked_count": self.blocked_count,
        }


audit_cache = AuditCache()
