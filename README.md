# Prison Management System API

Flask API foundation for the Ghana Prison Service prison management system.

## Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Replace every placeholder in `.env` with local or deployment values.
5. Run the database connection check:

```powershell
python scripts\test_db.py
```

## Configuration

Application settings are loaded from environment variables, authorize_roles in `src/config/settings.py`.
Database connections are configured in `src/config/database_config.py` and use a lazy MySQL connection pool sized by `DB_POOL_SIZE`.

The real `.env` file must stay local and must not be committed.

## Add Admin JSON Payload

Endpoint: `POST /api/v1/auth/register`

Requires an authenticated `admin` or `supervisor` access token with `users_create` permission.

```json
{
  "officer_id": "OFF001",
  "first_name": "FirstName",
  "middle_name": "MiddleName",
  "last_name": "LastName",
  "gender": "male",
  "dob": "1990-01-01",
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "phone": "+233000000000",
  "national_id": "GHA-000000000-0",
  "address": "Residential address",
  "profile_image": "profile-image-path-or-url",
  "staff_id": "STAFF001",
  "badge_number": "BADGE001",
  "rank": "Officer title",
  "department": "Administration",
  "position": "Officer title",
  "employment_date": "2026-05-14",
  "branch": "Branch or facility name",
  "username": "username",
  "role": "admin",
  "status": "active",
  "shift": "morning",
  "date_joined": "2026-05-14"
}
```

Allowed values:

- `gender`: `male`, `female`
- `role`: `admin`, `officer`, `supervisor`, `medical_officer`, `records_officer`, `visitor_officer`
- `status`: `active`, `inactive`
- `shift`: `morning`, `afternoon`, `night`

## Login

Endpoint: `POST /api/v1/auth/login` (Accepts `email` or `username` for authentication)

### Login with Email

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

Or:

```json
{
  "username": "username",
  "password": "StrongPassword123!"
}
```

### Login with Identifier (Email or Username)

```json
{
  "identifier": "user@example.com",
  "password": "StrongPassword123!"
}
```

```json
{
  "identifier": "username",
  "password": "StrongPassword123!"
}
```
```
