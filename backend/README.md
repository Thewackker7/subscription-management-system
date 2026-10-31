# Django backend

This is the API foundation for the Subscription Management System. It uses Django 5.2.18, Django REST Framework 3.15.2, Simple JWT 5.5.1, and PostgreSQL through Psycopg 3.2.13.

## Local setup

1. Create `backend/.env` from `backend/.env.example` and replace only the local placeholder values. Do not commit it.
2. Create the PostgreSQL database/user named in the environment file.
3. Install dependencies: `python -m pip install -r backend/requirements.txt`.
4. Run migrations: `python backend/manage.py migrate`.
5. Create the first Admin: `python backend/manage.py createsuperuser`. Superusers are assigned the `ADMIN` role automatically.
6. Run the server: `python backend/manage.py runserver`.

For dependency-free local test execution only, set `USE_SQLITE_FOR_TESTS=True`. This must not be used for the shared development or production database:

```bash
USE_SQLITE_FOR_TESTS=True python backend/manage.py test apps.accounts apps.catalog
```

The API contract is in `docs/API_CONTRACTS.md`.
