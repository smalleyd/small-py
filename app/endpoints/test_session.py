import unittest
from typing import Any
from ..main import app
from ..elastic.dao import Results
from ..dao.startup import session_dao
from parameterized import parameterized
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from ..models.session import Session, SessionSearchRequest

client = TestClient(app, headers={"X-Contextly-Key": "token-1"})
now = datetime.now()
minutes = timedelta(minutes=5)
minutesAgo = now - minutes
minutesAhead = now + minutes
expires_at = now + timedelta(minutes=10)

PERSON = {
    "id": "person-1",
    "email": "first@test.com",
    "first_name": "First 1",
    "last_name": "Last 1",
    "name": "Name 1",
    "type": "admin"
}

VALUE = {
    "id": "session-1",
    "person": PERSON,
    "duration": 10,
    "expires_at": expires_at.__str__()
}

class SessionEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scroll_id = None

    def setUp(self):
        self.scroll_id = SessionEndpointsTest.scroll_id

    def test_000_find(self):
        response = client.get("/sessions", params={})
        self.assertEqual(response.status_code, 200, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(0, results.total, "Check total")
        self.assertEquals(0, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(0, len(results.scores), "Check scores")

    def test_000_get(self):
        response = client.get("/sessions/session-1")
        self.assertEqual(404, response.status_code,"Check status_code")

    def test_010_post(self):
        response = client.post("/sessions", json=VALUE)
        self.assertEqual(201, response.status_code,"Check status_code")

        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-1", value.id, "Check ID")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual(10, value.duration, "Check duration")

    def test_010_post_get(self):
        response = client.get("sessions/session-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-1", value.id, "Check ID")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual("first@test.com", value.person.email, "Check person.email")
        self.assertEqual("First 1", value.person.first_name, "Check person.first_name")
        self.assertEqual(10, value.duration, "Check duration")
        self.assertEqual(expires_at, value.expires_at, "Check expires_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

    def test_020_put(self):
        value = VALUE.copy()
        value["duration"] = 11

        response = client.put("/sessions", json=value)
        self.assertEqual(200, response.status_code, "Check status_code")
        self.assertIsNotNone(Session(**response.json()), "Exists")

    def test_020_put_get(self):
        response = client.get("sessions/session-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-1", value.id, "Check ID")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual("first@test.com", value.person.email, "Check person.email")
        self.assertEqual("First 1", value.person.first_name, "Check person.first_name")
        self.assertEqual(11, value.duration, "Check duration")
        self.assertEqual(expires_at, value.expires_at, "Check expires_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    def test_030_patch(self):
        response = client.patch("/sessions/session-1", json={"person": {"first_name": "First One"}})
        self.assertEqual(200, response.status_code, "Check status_code")
        self.assertIsNotNone(Session(**response.json()), "Exists")

    def test_030_patch_get(self):
        response = client.get("sessions/session-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Session(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-1", value.id, "Check ID")
        self.assertIsNotNone(value.person, "Check person")
        self.assertEqual("first@test.com", value.person.email, "Check person.email")
        self.assertEqual("First One", value.person.first_name, "Check person.first_name")
        self.assertEqual(11, value.duration, "Check duration")
        self.assertEqual(expires_at, value.expires_at, "Check expires_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    @parameterized.expand([
        ({}, 1),
        ({"ids": ["session-0", "session-1", "session-2"]}, 1),
        ({"ids": ["session-0", "session-3", "session-2"]}, 0),
        ({"person_id": "person-1"}, 1),
        ({"person_id": "person-0"}, 0),
        ({"email": "FIRST@test.com"}, 1),
        ({"email": "first@test.co"}, 0),
        ({"name": "name"}, 1),
        ({"name": "First"}, 0),
        ({"type": "admin"}, 1),
        ({"type": "user"}, 0),
        ({"duration": 11}, 1),
        ({"duration": 10}, 0),
        ({"duration_from": 10}, 1),
        ({"duration_from": 12}, 0),
        ({"duration_to": 12}, 1),
        ({"duration_to": 10}, 0),
        ({"duration_from": 10, "duration_to": 12}, 1),
        ({"duration_from": 12, "duration_to": 20}, 0),
        ({"has_duration": True}, 1),
        ({"has_duration": False}, 0),
        ({"expires_at_from": expires_at - minutes}, 1),
        ({"expires_at_from": expires_at + minutes}, 0),
        ({"expires_at_to": expires_at + minutes}, 1),
        ({"expires_at_to": expires_at - minutes}, 0),
        ({"expires_at_from": expires_at - minutes, "expires_at_to": expires_at + minutes}, 1),
        ({"expires_at_from": expires_at + minutes, "expires_at_to": expires_at - minutes}, 0),
        ({"has_expires_at": True}, 1),
        ({"has_expires_at": False}, 0),
        ({"created_at_from": minutesAgo}, 1),
        ({"created_at_from": minutesAhead}, 0),
        ({"created_at_to": minutesAgo}, 0),
        ({"created_at_to": minutesAhead}, 1),
        ({"created_at_from": minutesAgo, "created_at_to": minutesAhead}, 1),
        ({"created_at_from": minutesAhead, "created_at_to": minutesAgo}, 0),
        ({"updated_at_from": minutesAgo}, 1),
        ({"updated_at_from": minutesAhead}, 0),
        ({"updated_at_to": minutesAgo}, 0),
        ({"updated_at_to": minutesAhead}, 1),
        ({"updated_at_from": minutesAgo, "updated_at_to": minutesAhead}, 1),
        ({"updated_at_from": minutesAhead, "updated_at_to": minutesAgo}, 0),
    ])
    def test_040_find(self, filter_: dict[str, Any], expected: int):
        response = client.get("/sessions", params=filter_)
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(expected, results.total, "Check total")
        self.assertEqual(expected, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(expected, len(results.scores), "Check scores")

    def test_050_load(self):
        session_dao.load([
            {
                "id": f"session-{i}",
                "person": {
                    "id": f"person-{i}",
                    "email": f"email-{i}@test.com",
                    "first_name": f"First {i}",
                    "last_name": f"Last {i}",
                    "name": f"Name {i}"
                },
                "duration": i * 10 if 0 == (i % 2) else None,
                "expires_at": (now + timedelta(minutes=i * 10)) if 0 == (i % 2) else None,
            }
            for i in range(2, 11)
        ])

        session_dao.refresh()

    @parameterized.expand([
        ({"has_duration": True}, 6),
        ({"has_duration": False}, 4),
        ({"has_expires_at": True}, 6),
        ({"has_expires_at": False}, 4)
    ])
    def test_050_load_find(self, filter_: dict[str, Any], expected: int):
        response = client.get("/sessions", params=filter_)
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(expected, results.total, "Check total")
        self.assertEqual(expected, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(expected, len(results.scores), "Check scores")

    def test_050_scroll_0(self):
        response = client.get("/sessions", params={"size": 5, "scroll": "30s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(5, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(5, len(results.scores), "Check scores")

        SessionEndpointsTest.scroll_id = results.scroll_id

    def test_050_scroll_1(self):
        response = client.get(f"/sessions/scroll/{self.scroll_id}", params={"time": "20s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(5, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(5, len(results.scores), "Check scores")

        SessionEndpointsTest.scroll_id = results.scroll_id

    def test_050_scroll_2(self):
        response = client.get(f"/sessions/scroll/{self.scroll_id}", params={"time": "10s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(0, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(0, len(results.scores), "Check scores")

    def test_999_delete(self):
        response = client.delete("/sessions/session-1")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_999_delete_get(self):
        response = client.get("/sessions/session-1")
        self.assertEqual(404, response.status_code, "Check status_code")

if __name__ == '__main__':
    unittest.main()

