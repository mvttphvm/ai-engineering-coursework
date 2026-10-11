from fastapi import FastAPI
from app.routers import recipes

app = FastAPI()

app.include_router(recipes.router, prefix="/recipes", tags=["recipes"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
