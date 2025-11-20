import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = FastAPI()


class Payload(BaseModel):
    x: float
    y: float


@app.post("/add")
def add_numbers(p: Payload):
    result = p.x + p.y
    logging.info(f"Received x={p.x}, y={p.y} -> z={result}")
    return {"z": result}
