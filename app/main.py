from typing import Any
from .endpoints import person, mcp
from fastapi import FastAPI, Request
from elasticsearch import NotFoundError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI(title="My Context", version="0.0.1")

app.include_router(person.router)
app.include_router(mcp.router)

@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
  id = exc.body["_id"]
  index = exc.body["_index"]
  return JSONResponse(status_code=404, content={"message": f"Could not find {index} with identifier - {id}."})

@app.exception_handler(ValidationError) # Needed for BaseModel.model_validate calls in PATCH methods.
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
  return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.get("/", response_model_exclude_unset=True, tags=["Main"])
async def root() -> dict[str, Any]:
  return {"message": "Hello World"}
