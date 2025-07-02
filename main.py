from typing import Union
import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0" if bool(os.environ.get("CONTAINER", None)) else "127.0.0.1"

    uvicorn.run(app, host=host)
