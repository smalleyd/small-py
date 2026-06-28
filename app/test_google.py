import unittest
from . import google    # MUST access get_oauth_user from the module because it is mocked in other tests. DLS on 6/28/2026.
from typing import Any
from .google import OAuthUser
from parameterized import parameterized
from requests.exceptions import HTTPError

class OAuthUserTest(unittest.TestCase):
    @parameterized.expand([
        ({"sub": "sub-1", "name": "Tester Monday", "email": "monday@test.com"}, "sub-1", "Tester Monday", "monday@test.com", "Tester", "Monday"),
        ({"sub": "sub-1", "name": "Tester Monday Tuesday", "email": "monday@test.com"}, "sub-1", "Tester Monday Tuesday", "monday@test.com", "Tester", "Tuesday"),
        ({"sub": "sub-1", "name": "Wednesday", "email": "monday@test.com"}, "sub-1", "Wednesday", "monday@test.com", "Wednesday", "Wednesday"),
        ({"sub": "sub-1", "name": "Tester Monday", "email": "monday@test.com", "given_name": "Giver"}, "sub-1", "Tester Monday", "monday@test.com", "Giver", "Monday"),
        ({"sub": "sub-1", "name": "Tester Monday", "email": "monday@test.com", "family_name": "Family"}, "sub-1", "Tester Monday", "monday@test.com", "Tester", "Family"),
        ({"sub": "sub-1", "name": "Tester Monday", "email": "monday@test.com", "given_name": "Giver", "family_name": "Family"}, "sub-1", "Tester Monday", "monday@test.com", "Giver", "Family"),
    ])
    def test_create(
        self,
        input_: dict[str, Any],
        sub: str,
        name: str,
        email: str,
        first_name: str,
        last_name: str
    ):
        value = OAuthUser(**input_)
        self.assertIsNotNone(value, "Exists")
        self.assertEqual(value.sub, sub, "Check sub")
        self.assertEqual(value.name, name, "Check name")
        self.assertEqual(value.email, email, "Check email")

        names = value.names
        self.assertEqual(2, len(names), "Check names")
        self.assertEqual(first_name, names[0], "Check first name")
        self.assertEqual(last_name, names[1], "Check last name")

    def test_get_oauth_user(self):
        try:
            google.get_oauth_user("token-1")
        except HTTPError as ex:
            self.assertIsNotNone(ex, "Exists")
            self.assertEqual(401, ex.response.status_code, "Check status_code")
            self.assertEqual(
                {"error": "invalid_request", "error_description": "Invalid Credentials"},
                ex.response.json(),
                "Check json")
