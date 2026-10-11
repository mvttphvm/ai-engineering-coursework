# Structured Recipe API

**Module:** 5 — FastAPI Development
**Estimated time:** 30 minutes

## Objective

Organize a FastAPI application using APIRouter to separate endpoint logic into its own module, and implement basic CRUD operations with an in-memory data store.

## What You'll Do

1. In `app/routers/recipes.py`, add route decorators to the existing functions and implement each endpoint:
   - `GET /` — return all recipes from the in-memory list.
   - `GET /{recipe_id}` — return a single recipe by ID, or raise a 404.
   - `POST /` — create a new recipe with an auto-incremented ID, return it with status 201.
2. In `app/main.py`, import the recipes router and include it with `prefix="/recipes"` and `tags=["recipes"]`.

## Starter Code

```
app/
  __init__.py
  main.py              — FastAPI app; needs router inclusion
  routers/
    __init__.py
    recipes.py          — APIRouter with in-memory recipe list and function stubs
```

The recipes router already has a pre-populated list of two recipes and a `_next_id` counter.

## Running

```bash
uvicorn app.main:app --reload
```

## Deliverable

A working API at `/recipes` with GET (list), GET (by ID), and POST endpoints. Recipes are stored in memory and new ones receive auto-incremented IDs.
