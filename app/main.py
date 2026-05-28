from fastapi import FastAPI 
from .endpoints import person, thing

app = FastAPI(title="My Context", version="0.0.1")
app.include_router(person.router)
app.include_router(thing.router)

@app.get("/", response_model_exclude_unset=True, tags=["Main"])
async def root() -> dict:
  return {"message":"Hello World"}
