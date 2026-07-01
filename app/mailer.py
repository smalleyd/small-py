import os
import json
from .dao.otp import Token
# from typing import override
from mailgun.client import Client
from .models.person import Person
from urllib.error import HTTPError

DOMAIN = "mg.shredly.io"
BASE_URL = "https://shredly.io/"
REPLY_TO = "Shredly<noreply@shredly.io>"
LOGIN_OTP = """
<html><body><p>Hi {name}, here is your one-time-password (OTP) to continue with your login - <b>{token}</b>.</p>
<p>Click this <a href=\"{url}\">link</a> if the OTP is not picked up automatically.</p></body></html>
"""
REGISTRATION_OTP = """
<html><body><p>Hi, here is your one-time-password (OTP) to continue with your registration - <b>{token}</b>.</p>
<p>Click this <a href=\"{url}\">link</a> if the OTP is not picked up automatically.</p></body></html>
"""

class Mailer:
    last_inputs:dict | None = None # Needed for FakeMailer

    def __init__(self, key_name: str = "MAILGUN_API_KEY"):
        key = os.getenv(key_name)
        if not key:
            raise Exception(f"The {key_name} environment variable is missing.")

        self.client = Client(auth=("api", key), api_url="https://api.mailgun.net/")
        self.otp_url = BASE_URL + "{path}?token={token}&email={email}"

    def send_otp_message(self, email: str, token: Token, person: Person | None = None):
        has_person = person is not None
        name = person.name if has_person else email
        path = "login" if has_person else "register"
        title = "Login" if has_person else "Registration"
        url = self.otp_url.format(path=path, email=email, token=token.value)
        response = self.client.messages.create(data={
            "to": email,
            "from": REPLY_TO,
            "reply_to": REPLY_TO,
            # template="otp_authentication",
            "html": (LOGIN_OTP if has_person else REGISTRATION_OTP).format(name=name, token=token.value, email=email, url=url),
            "subject": f"Your Shredly.io {title} Token",
            "t:variables": json.dumps({ # NOT needed until we create actual templates.
                "token": token.value,
                "has_person": has_person,
                "name": name,
                "url": url
            })
        }, domain = DOMAIN)

        if 400 <= response.status_code:
            print("MAILER:", response.text)
            raise HTTPError(code=response.status_code, msg=response.text, url="ES:exists", hdrs={}, fp=None)

class FakeMailer(Mailer):
    # @override
    def send_otp_message(self, email: str, token: Token, person: Person | None = None):
        self.last_inputs = {"email": email, "token": token, "person": person}
