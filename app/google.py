import requests
from pydantic import BaseModel, ConfigDict

URL = "https://www.googleapis.com"
PATH_OAUTH = "/oauth2/v3"
URL_OAUTH_USER = URL + PATH_OAUTH + "/userinfo"

class OAuthUser(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)    # MUST ignore an extra properties that comeback in the payload. DLS on 6/29/2026.

    sub: str
    name: str
    email: str
    locale: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email_verified: bool | None = None

    @property
    def names(self) -> tuple[str, str]:
        fn: str
        ln: str
        n: list[str] = self.name.split(" ")
        if self.given_name:
            fn = self.given_name
        else:
            fn = n[0]

        if self.family_name:
            ln = self.family_name
        else:
            ln = n[-1]

        return fn, ln

def get_oauth_user(token: str) -> OAuthUser:
    with requests.get(
        URL_OAUTH_USER,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    ) as resp:
        if 400 <= resp.status_code:
            resp.raise_for_status()

        return OAuthUser(**resp.json())
