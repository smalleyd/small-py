import requests
from urllib.error import HTTPError
from fastapi import FastAPI, Request
from pydantic import ValidationError
from elasticsearch import NotFoundError
from typing import Any, Awaitable, Callable
from fastapi.middleware.cors import CORSMiddleware    # It did not work as documented so built my own version. DLS on 6/26/2026.
from fastapi.responses import JSONResponse, Response
from .endpoints import authentication, mcp, person, session

app = FastAPI(title="Shredly", version="0.0.1")
app.include_router(authentication.router)
app.include_router(person.router)
app.include_router(mcp.router)
app.include_router(session.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
@app.middleware("http")
async def add_cors_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    response.headers["access-control-allow-origin"] = "*"
    response.headers["access-control-allow-methods"] = "*"
    response.headers["access-control-allow-credentials"] = "true"
    response.headers["access-control-allow-headers"] = f"Origin,X-Requested-With,Accept,Accept-Language,Authorization,Content-Type,{HEADER_API_KEY}}"

    return response
"""

@app.exception_handler(HTTPError)
async def handle_http_error(request: Request, exc: HTTPError) -> JSONResponse:
  return JSONResponse(status_code=exc.code, content={"message": exc.msg})

@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
  id = exc.body["_id"]
  index = exc.body["_index"]
  return JSONResponse(status_code=404, content={"message": f"Could not find {index} with identifier - {id}."})

@app.exception_handler(requests.exceptions.HTTPError)
async def handle_requests_http_error(request: Request, exc: requests.exceptions.HTTPError) -> JSONResponse:
  return JSONResponse(status_code=exc.response.status_code, content={"message": exc.response.json()["error_description"]})

@app.exception_handler(ValidationError) # Needed for BaseModel.model_validate calls in PATCH methods.
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
  return JSONResponse(status_code=422, content={"detail": exc.errors(), "title": exc.title})

@app.get("/", tags=["Main"])
async def root() -> dict[str, Any]:
  return {"message": "Hello World"}
