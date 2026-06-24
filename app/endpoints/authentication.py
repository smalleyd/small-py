from typing import Annotated
from ..datasource import mailer
from ..models.session import Session
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from ..models.person import Person, Source, Type
from pydantic import BaseModel, Field, ValidationError
from ..dao.startup import otp_dao, person_dao, session_dao

router = APIRouter(prefix="/auth", tags=["authentication"])
expiration = timedelta(minutes=30)

def expire_when() -> datetime:
    return datetime.now() + expiration

class OtpCompleteRequest(BaseModel):
    email: Annotated[str, Field(min_length=1, max_length=200)]
    token: Annotated[str, Field(min_length=1, max_length=100)]

class OtpStartResponse(BaseModel):
    exists: bool

@router.get("/otp", summary="Start OTP")
async def start_otp(email: Annotated[str, Query(pattern="^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$")]) -> OtpStartResponse:
    token = otp_dao.generate(email)
    person = person_dao.get_by_email_(email)

    mailer.send_otp_message(email, token, person)

    return OtpStartResponse(exists=person is not None)

@router.post("/otp", summary="Complete OTP")
async def complete_otp(request: OtpCompleteRequest) -> Session:
    if not otp_dao.check(request.email, request.token):
        raise ValidationError.from_exception_data(title="Invalid request", line_errors=[])

    person = person_dao.auth(request.email)
    return session_dao.upsert(Session(person=person, duration=30, expires_at=expire_when()))

@router.post("/register", summary="Register")
async def register(
    token: Annotated[str, Query(min_length=1, max_length=100)],
    value: Person
) -> Session:
    if not otp_dao.check(value.email, token):
        raise ValidationError.from_exception_data(title="Invalid request", line_errors=[])

    value.type = Type.USER  # Make sure that the Person is created as a User - not Admin. DLS on 6/24/2026.
    value.source = Source.EMAIL
    value.auth_at = datetime.now()
    person = person_dao.upsert(value)
    return session_dao.upsert(Session(person=person, duration=30, expires_at=expire_when()))