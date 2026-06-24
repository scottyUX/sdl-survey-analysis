"""Shared SDLC stage keys and Qualtrics column prefixes."""

from __future__ import annotations

STAGE_PREFIX: dict[str, str] = {
    "plan": "Planning",
    "design": "Design",
    "implementation": "Impl",
    "testing": "Testing",
    "deployment": "Deployment",
    "maintenance": "Maintenance",
}

STAGES: list[str] = list(STAGE_PREFIX.keys())

MIN_DURATION_SECONDS = 120
MAX_DURATION_SECONDS = 7200
