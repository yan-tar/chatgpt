from fastapi import FastAPI
from pydantic import BaseModel

class Nums(BaseModel):
    first: int
    second: int

# создаем объект приложения
app = FastAPI()

@app.get("/sum/{first}/{second}")
def get_sum(first:int, second:int):
    sum = first + second
    return {"sum": sum}

@app.post("/sum") 
def post_sum(item: Nums): 
    sum = item.first + item.second
    return {"sum": sum}


@app.get("/subtraction/{first}/{second}")
def get_subtraction(first:int, second:int):
    subtraction = first - second
    return {"subtraction": subtraction}

@app.post("/subtraction") 
def post_subtraction(item: Nums): 
    subtraction = item.first - item.second
    return {"subtraction": subtraction}


@app.get("/multiplication/{first}/{second}")
def get_multiplication(first:int, second:int):
    multiplication = first * second
    return {"multiplication": multiplication}

@app.post("/multiplication") 
def post_multiplication(item: Nums): 
    multiplication = item.first * item.second
    return {"multiplication": multiplication}

@app.get("/division/{first}/{second}")
def get_division(first:int, second:int):
    if second != 0:
        division = first / second
        return {"division": division}
    else: 
        return {"error": "На ноль делить нельзя"}

@app.post("/division") 
def post_division(item: Nums): 
    if item.second != 0:
        division = item.first / item.second
        return {"division": division}
    else: 
        return {"error": "На ноль делить нельзя"}
    