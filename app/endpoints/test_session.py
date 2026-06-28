import unittest
from typing import Any
from ..main import app
from ..elastic.dao import Results
from urllib.error import HTTPError
from ..models.session import Session
from ..dao.startup import session_dao
from parameterized import parameterized
from ..models.person import Person, Type
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

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

PERSON_ = Person(**PERSON)

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
        session_dao.add(Session(id="token-1", person=Person(id="admin-0", email="admin@test.com", name="Admin", first_name="Admin", last_name="Worker", type=Type.ADMIN), duration=None))

    def setUp(self):
        self.scroll_id = SessionEndpointsTest.scroll_id

    @classmethod
    def tearDownClass(cls):
        session_dao.remove("token-1")

    def test_000_can_update(self):  # CanNOT use parameterized tests because the updated_at fields is calculated at creation of the module. DLS on 6/27/2026.
        self.assertFalse(Session(person=PERSON_, duration=None, updated_at=datetime.now()).can_update())
        self.assertFalse(Session(person=PERSON_, duration=None, updated_at=datetime.now() - timedelta(seconds=2)).can_update())
        self.assertTrue(Session(person=PERSON_, duration=None, updated_at=datetime.now() - timedelta(seconds=6)).can_update())
        self.assertTrue(Session(person=PERSON_, duration=None, updated_at=datetime.now() - timedelta(seconds=10)).can_update())

    @parameterized.expand([
        (Session(person=PERSON_, duration=None, expires_at=None), False),
        (Session(person=PERSON_, duration=None, expires_at=minutesAgo), True),
        (Session(person=PERSON_, duration=None, expires_at=minutesAhead), False)
    ])
    def test_000_expired(self, value: Session, expected: bool):
        self.assertEqual(expected, value.expired())

    @parameterized.expand([
        (Session(person=Person(email="1@test.com", name="Name", first_name="First", last_name="Last", type=Type.ADMIN)), True, False),
        (Session(person=Person(email="1@test.com", name="Name", first_name="First", last_name="Last", type=Type.USER)), False, True),
    ])
    def test_000_check_properties(self, value: Session, admin: bool, user: bool):
        self.assertEqual(admin, value.admin(), "Check admin()")
        self.assertEqual(user, value.user(), "Check user()")

    def test_000_find(self):
        response = client.get("/sessions", params={})
        self.assertEqual(response.status_code, 200, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(1, results.total, "Check total")   # Admin user
        self.assertEquals(1, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(1, len(results.scores), "Check scores")

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
        ({}, 2),
        ({"ids": ["session-0", "session-1", "session-2"]}, 1),
        ({"ids": ["session-0", "session-3", "session-2"]}, 0),
        ({"person_id": "person-1"}, 1),
        ({"person_id": "person-0"}, 0),
        ({"email": "FIRST@test.com"}, 1),
        ({"email": "first@test.co"}, 0),
        ({"name": "name"}, 1),
        ({"name": "First"}, 0),
        ({"type": "admin"}, 2),
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
        ({"has_duration": False}, 1),
        ({"expires_at_from": expires_at - minutes}, 1),
        ({"expires_at_from": expires_at + minutes}, 0),
        ({"expires_at_to": expires_at + minutes}, 1),
        ({"expires_at_to": expires_at - minutes}, 0),
        ({"expires_at_from": expires_at - minutes, "expires_at_to": expires_at + minutes}, 1),
        ({"expires_at_from": expires_at + minutes, "expires_at_to": expires_at - minutes}, 0),
        ({"has_expires_at": True}, 1),
        ({"has_expires_at": False}, 1),
        ({"created_at_from": minutesAgo}, 1),   # Excludes the ADMIN session because it does not have a created_at/updated_at.
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
        ({"has_duration": False}, 5),
        ({"has_expires_at": True}, 6),
        ({"has_expires_at": False}, 5)
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
        response = client.get("/sessions", params={"size": 6, "scroll": "30s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(11, results.total, "Check total")
        self.assertEqual(6, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(6, len(results.scores), "Check scores")

        SessionEndpointsTest.scroll_id = results.scroll_id

    def test_050_scroll_1(self):
        response = client.get(f"/sessions/scroll/{self.scroll_id}", params={"time": "20s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(11, results.total, "Check total")
        self.assertEqual(5, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(5, len(results.scores), "Check scores")

        SessionEndpointsTest.scroll_id = results.scroll_id

    def test_050_scroll_2(self):
        response = client.get(f"/sessions/scroll/{self.scroll_id}", params={"time": "10s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Session](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(11, results.total, "Check total")
        self.assertEqual(0, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(0, len(results.scores), "Check scores")

    def test_100_check_not_found(self):
        try:
            session_dao.check("session-invalid")
        except HTTPError as ex:
            self.assertEqual(401, ex.code, "Check code")
            self.assertEqual("Session not found", ex.msg, "Check msg")
        except BaseException:
            self.fail("Expected HTTPError")

    def test_110_check_expired(self):
        session_dao.update("session-2", {"expires_at": datetime.now()})

        try:
            session_dao.check("session-2")
        except HTTPError as ex:
            self.assertEqual(401, ex.code, "Check code")
            self.assertEqual("Session expired", ex.msg, "Check msg")
        except BaseException:
            self.fail("Expected HTTPError")

    def test_110_check_expired_after(self):
        response = client.get("/session/session-2")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_110_check_no_expiration(self):
        value = session_dao.check("session-3")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-3", value.id, "Check ID")

    def test_110_check_not_expired(self):
        now_ = datetime.now()
        expires_at_ = now_ + timedelta(minutes=1)
        session_dao.update("session-4", {"expires_at": expires_at_, "updated_at": now_})
        value = session_dao.check("session-4")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-4", value.id, "Check ID")
        self.assertEqual(expires_at_, value.expires_at, "Check expires_at")
        self.assertEqual(now_, value.updated_at, "Check updated_at")

    def test_110_check_not_expired_updates(self):
        now_ = datetime.now()
        expires_at_ = now_ + timedelta(minutes=5)
        updated_at = now_ - timedelta(seconds=6)
        session_dao.update("session-4", {"duration": 5, "expires_at": expires_at_, "updated_at": updated_at})
        value = session_dao.check("session-4")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("session-4", value.id, "Check ID")
        self.assertEqual(5, value.duration, "Check duration")
        self.assertLess(expires_at_, value.expires_at, "Check expires_at")
        self.assertLess(now_, value.updated_at, "Check updated_at")

    def test_999_delete(self):
        response = client.delete("/sessions/session-1")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_999_delete_get(self):
        response = client.get("/sessions/session-1")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_999_delete_rest(self):
        for i in range(3, 11):  # session-2 was deleted because it was expired.
            response = client.delete(f"/sessions/session-{i}")
            self.assertEqual(204, response.status_code, f"Check status_code: {i}")

if __name__ == '__main__':
    unittest.main()

