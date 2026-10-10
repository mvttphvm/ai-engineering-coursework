from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Welcome to Hello FastAPI!"}


@app.get("/hello")
def say_hello():
    return "Hello, FastAPI!"


@app.get("/info")
def get_info():
    return {
        "name": "Hello FastAPI",
        "version": str(fastapi.__version__),
        "description": "A FastAPI application.",
    }


@app.get("/items")
def list_items():
    return [
        {"id": 1, "name": "Widget"},
        {"id": 2, "name": "Gadget"},
        {"id": 3, "name": "Widget Pro"},
    ]


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {
        "id": item_id,
        "name": f"Item {item_id}",
        "description": f"This is the description for item {item_id}.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
