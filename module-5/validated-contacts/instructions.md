# Validated Contacts

**Module:** 5 — FastAPI Development
**Estimated time:** 40 minutes

## Objective

Build a contact book API with Pydantic v2 schemas that enforce field validation, custom validators, and enum-based categories. Practice using separate schemas for create, update, and response.

## What You'll Do

1. In `app/schemas/contact.py`, define:
   - A `ContactCategory` enum with values: personal, work, family.
   - A `ContactCreate` schema with validated fields (first_name, last_name, email, phone, category) and a `@field_validator` that checks email contains "@".
   - A `ContactUpdate` schema with all fields optional (for PATCH requests).
   - A `ContactResponse` schema that extends `ContactCreate` with id and created_at.
2. In `app/routers/contacts.py`, implement the endpoint bodies:
   - `POST /` — create a contact with auto-assigned ID and timestamp, return 201.
   - `GET /` — list all contacts with optional category query filter.
   - `GET /{contact_id}` — get a single contact or 404.
   - `PATCH /{contact_id}` — partially update a contact using `model_dump(exclude_unset=True)`.
3. In `app/main.py`, import and include the contacts router with `prefix="/contacts"`.

## Starter Code

```
app/
  __init__.py
  main.py                — FastAPI app; needs router inclusion
  schemas/
    __init__.py
    contact.py           — Pydantic schema stubs with TODO guidance
  routers/
    __init__.py
    contacts.py          — Endpoint stubs with in-memory storage
```

## Running

```bash
uvicorn app.main:app --reload
```

## Deliverable

A contact book API where invalid data (missing "@" in email, out-of-range phone length, invalid category) is automatically rejected with 422 errors and descriptive messages.
