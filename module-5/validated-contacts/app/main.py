from fastapi import FastAPI
from app.routers import contacts

app = FastAPI(title="Contact Book API")

app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
