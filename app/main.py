from typing import Any
from urllib.error import HTTPError
from fastapi import FastAPI, Request
from pydantic import ValidationError
from elasticsearch import NotFoundError
from fastapi.responses import JSONResponse
from .endpoints import person, mcp, session

app = FastAPI(title="My Context", version="0.0.1")

app.include_router(person.router)
app.include_router(mcp.router)

app.include_router(session.router)

@app.exception_handler(HTTPError)
async def handle_http_error(request: Request, exc: HTTPError) -> JSONResponse:
  return JSONResponse(status_code=exc.code, content={"message": exc.msg})

@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
  id = exc.body["_id"]
  index = exc.body["_index"]
  return JSONResponse(status_code=404, content={"message": f"Could not find {index} with identifier - {id}."})

@app.exception_handler(ValidationError) # Needed for BaseModel.model_validate calls in PATCH methods.
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
  return JSONResponse(status_code=422, content={"detail": exc.errors(), "title": exc.title})

@app.get("/", response_model_exclude_unset=True, tags=["Main"])
async def root() -> dict[str, Any]:
  return {"message": "Hello World"}
