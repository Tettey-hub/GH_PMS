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
    middle_name: str | None = None
    gender: str | None = None
    dob: date | None = None
    national_id: str | None = None
    address: str | None = None
    profile_image: str | None = None
    staff_id: str | None = None
    position: str | None = None
    employment_date: date | None = None
    branch: str | None = None
    username: str | None = None
    role_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def full_name(self) -> str:
        names = [self.first_name, self.middle_name, self.last_name]
        return " ".join(name for name in names if name).strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "officer_id": self.officer_id,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "email": self.email,
            "phone": self.phone,
            "national_id": self.national_id,
            "address": self.address,
            "profile_image": self.profile_image,
            "staff_id": self.staff_id,
            "badge_number": self.badge_number,
            "rank": self.rank,
            "department": self.department,
            "position": self.position,
            "employment_date": self.employment_date.isoformat() if self.employment_date else None,
            "branch": self.branch,
            "username": self.username,
            "role_id": self.role_id,
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
            middle_name=row.get("middle_name"),
            last_name=row["last_name"],
            gender=row.get("gender"),
            dob=row.get("dob"),
            email=row["email"],
            password=row["password"],
            phone=row.get("phone"),
            national_id=row.get("national_id"),
            address=row.get("address"),
            profile_image=row.get("profile_image"),
            staff_id=row.get("staff_id"),
            badge_number=row["badge_number"],
            rank=row["rank"],
            department=row["department"],
            position=row.get("position"),
            employment_date=row.get("employment_date"),
            branch=row.get("branch"),
            username=row.get("username"),
            role_id=row.get("role_id"),
            role=row["role"],
            shift=row["shift"],
            status=row["status"],
            date_joined=row["date_joined"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
