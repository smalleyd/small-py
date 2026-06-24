import unittest
from ..main import app
from ..endpoints import test_person
from ..models.session import Session
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from ..models.person import Person, Source
from .authentication import OtpStartResponse
from ..dao.startup import otp_dao, person_dao, session_dao

client = TestClient(app)

FIRST = test_person.VALUE.copy()
FIRST["email"] = "first@test.com"

SECOND = {
    "email": "second@test.com",
    "first_name": "First 2",
    "last_name": "Last 2",
    "name": "Name 2"
}

class AuthenticationEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.person = person_dao.upsert(Person(**FIRST))

    @classmethod
    def tearDownClass(cls):
        person_dao.remove(cls.person.id)

    def test_000_start_otp_existing_person(self):
        response = client.get("/auth/otp", params={"email": "first@test.com"})
        self.assertEqual(response.status_code, 200, "Check status_code")

        results = OtpStartResponse(**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertTrue(results.exists, "Check exists")

    def test_000_start_otp_new_person(self):
        response = client.get("/auth/otp", params={"email": "second@test.com"})
        self.assertEqual(response.status_code, 200, "Check status_code")

        results = OtpStartResponse(**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertFalse(results.exists, "Check exists")

    def test_010_complete_otp_invalid_token(self):
        response = client.post("/auth/otp", json={"email": "second@test.com", "token": "invalid"})
        self.assertEqual(422, response.status_code, "Check status_code")

    def test_010_complete_otp_new_person(self):
        response = client.post("/auth/otp", json={"email": "second@test.com", "token": otp_dao.get("second@test.com").value})
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_020_start_otp_new_person(self):
        response = client.get("/auth/otp", params={"email": "second@test.com"})
        self.assertEqual(response.status_code, 200, "Check status_code")

    def test_030_complete_otp(self):
        response = client.post("/auth/otp", json={"email": "first@test.com", "token": otp_dao.get("first@test.com").value})
        self.assertEqual(response.status_code, 200, "Check status_code")

        now = datetime.now()
        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertIsNotNone(value.id, "Check id")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual("first@test.com", value.person.email, "Check person.email")
        self.assertEqual(Source.GITHUB, value.person.source, "Check person.source")
        self.assertLess(now - timedelta(minutes=1), value.person.auth_at, "Check person.auth_at")
        self.assertGreater(now + timedelta(minutes=1), value.person.auth_at, "Check person.auth_at")
        self.assertEqual(30, value.duration, "Check duration")
        self.assertIsNotNone(value.expires_at, "Check expires_at")
        self.assertLess(now + timedelta(minutes=28), value.expires_at, "Check expires_at")
        self.assertGreater(now + timedelta(minutes=32), value.expires_at, "Check expires_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

        session_dao.remove(value.id)

    def test_030_register_fail(self):
        response = client.post("/auth/register", json=SECOND, params={"token": "invalid"})
        self.assertEqual(response.status_code, 422, "Check status_code")


    def test_030_register_success(self):
        response = client.post("/auth/register", json=SECOND, params={"token": otp_dao.get("second@test.com").value})
        self.assertEqual(response.status_code, 200, "Check status_code")

        now = datetime.now()
        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertIsNotNone(value.id, "Check id")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual("second@test.com", value.person.email, "Check person.email")
        self.assertEqual(Source.EMAIL, value.person.source, "Check person.source")
        self.assertLess(now - timedelta(minutes=1), value.person.auth_at, "Check person.auth_at")
        self.assertGreater(now + timedelta(minutes=1), value.person.auth_at, "Check person.auth_at")
        self.assertEqual(30, value.duration, "Check duration")
        self.assertIsNotNone(value.expires_at, "Check expires_at")
        self.assertLess(now + timedelta(minutes=28), value.expires_at, "Check expires_at")
        self.assertGreater(now + timedelta(minutes=32), value.expires_at, "Check expires_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

        session_dao.remove(value.id)
        person_dao.remove(value.person.id)

if __name__ == "__main__":
    unittest.main()
