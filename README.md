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

Application settings are loaded from environment variables in `src/config/settings.py`.
Database connections are configured in `src/config/database_config.py` and use a lazy MySQL connection pool sized by `DB_POOL_SIZE`.

The real `.env` file must stay local and must not be committed.
