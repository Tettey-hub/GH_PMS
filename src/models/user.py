from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


USER_ROLES = {"admin", "officer", "supervisor", "medical_officer", "records_officer", "visitor_officer"}
USER_SHIFTS = {"morning", "afternoon", "night"}
USER_STATUSES = {"active", "inactive", "suspended"}


@dataclass(frozen=True)
class User:
    id: int | None
    officer_id: str
    first_name: str
    last_name: str
    email: str
    password: str
    phone: str | None
    badge_number: str
    rank: str
    department: str
    role: str
    shift: str
    status: str
    date_joined: date
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "officer_id": self.officer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "badge_number": self.badge_number,
            "rank": self.rank,
            "department": self.department,
            "role": self.role,
            "shift": self.shift,
            "status": self.status,
            "date_joined": self.date_joined.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "User":
        return cls(
            id=row.get("id"),
            officer_id=row["officer_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            password=row["password"],
            phone=row.get("phone"),
            badge_number=row["badge_number"],
            rank=row["rank"],
            department=row["department"],
            role=row["role"],
            shift=row["shift"],
            status=row["status"],
            date_joined=row["date_joined"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
