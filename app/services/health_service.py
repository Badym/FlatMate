"""Stan aplikacji dla healthchecka Dockera i monitoringu."""

from __future__ import annotations

from dataclasses import dataclass

from app.repositories.health_repository import HealthRepository


@dataclass(frozen=True)
class HealthStatus:
    database: bool

    @property
    def healthy(self) -> bool:
        return self.database

    def as_dict(self) -> dict[str, str]:
        return {
            "status": "ok" if self.healthy else "degraded",
            "database": "ok" if self.database else "error",
        }


class HealthService:
    def __init__(self, repository: HealthRepository | None = None) -> None:
        self._repository = repository or HealthRepository()

    def check(self) -> HealthStatus:
        return HealthStatus(database=self._repository.ping())
