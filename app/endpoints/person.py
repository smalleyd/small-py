from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from ..security import auth
from ..models.person import *

router = APIRouter(prefix="/people", tags=["People"])

@router.post("/auth")
async def authenticate(value: Annotated[OAuth2PasswordRequestForm, Depends()]) -> AccessToken:
  username = value.username
  password = value.password
  if not username or username != "api" or not password:
    raise HTTPException(status_code=422, detail="Invalid credentials")

  return AccessToken(access_token=password)
