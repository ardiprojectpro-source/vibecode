from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class Outputs:
    """Structured outputs for generated content."""

    summary_points: List[str] = field(default_factory=list)
    outline: List[str] = field(default_factory=list)
    script_text: str = ""
    titles: List[str] = field(default_factory=list)
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)


@dataclass
class Job:
    id: str
    url: str
    language: str
    niche: str
    persona: str
    originality_level: int
    target_duration_min: int
    model_selected: Optional[str] = None
    status: str = "queued"  # queued, running, done, error
    outputs: Outputs = field(default_factory=Outputs)


@dataclass
class ModelInfo:
    id: str
    name: str
    pricing_input: float
    pricing_output: float
    context_length: int
    latency_ms: Optional[int]
    available: bool
    popularity: Optional[float]


@dataclass
class ModelsCache:
    models: List[ModelInfo] = field(default_factory=list)
    fetched_at: Optional[datetime] = None
    ttl_minutes: int = 30
    favorites: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        if not self.fetched_at:
            return False
        return datetime.utcnow() - self.fetched_at < timedelta(minutes=self.ttl_minutes)

    def update(self, models: List[ModelInfo]) -> None:
        self.models = models
        self.fetched_at = datetime.utcnow()
