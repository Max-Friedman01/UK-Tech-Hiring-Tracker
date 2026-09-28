from dataclasses import dataclass, field

@dataclass
class Job:
    job_id: str
    platform: str
    board_id: str

    title: str
    location: str | None = None
    departments: list[str] = field(default_factory=list)
    offices: list[str] = field(default_factory=list)
    url: str | None = None

    updated_at: str | None = None
    first_published: str | None = None

    content: str | None = None
    raw_json: str | None = None