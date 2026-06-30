import unittest
from typing import Any
from ..main import app
from ..elastic.dao import Results
from urllib.error import HTTPError
from ..models.session import Session
from pydantic import ValidationError
from parameterized import parameterized
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from ..models.common import HEADER_API_KEY
from ..dao.startup import person_dao, session_dao
from ..models.person import Person, PersonSearchRequest, Source, Type

client = TestClient(app, headers={HEADER_API_KEY: "token-1"})
sources = list(Source)
minutesAgo = datetime.now() - timedelta(minutes=5)
minutesAhead = datetime.now() + timedelta(minutes=5)

VALUE = {
    "id": "person-1",
    "email": "first@test.com",
    "first_name": "First 1",
    "last_name": "Last 1",
    "name": "Name 1",
    "source": "GitHub"
}

class PersonEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scroll_id = None
        session_dao.add(Session(id="token-1", person=Person(id="person-1", email="one@test.com", name="Name", first_name="First", last_name="Last", type=Type.ADMIN), duration=None))
        session_dao.add(Session(id="token-2", person=Person(id="person-1", email="one@test.com", name="Name", first_name="First", last_name="Last", type=Type.USER), duration=None))

    def setUp(self):
        self.scroll_id = PersonEndpointsTest.scroll_id

    @classmethod
    def tearDownClass(cls):
        session_dao.remove("token-1")
        session_dao.remove("token-2")

    @parameterized.expand([
        (None, 401, {"detail": "Not authenticated"}),
        ({HEADER_API_KEY: "token-2"}, 403, {"message": "Not authorized"})
    ])
    def test_000_auth_fail(self, headers: dict[str, str], status_code: int, output: dict[str, Any]):
        with TestClient(app) as client_:
            response = client_.get("/sessions", headers=headers)
            self.assertEqual(status_code, response.status_code, "Check status_code")
            self.assertEqual(output, response.json(), "Check json")

    @parameterized.expand([
        (Person(email="1@test.com", name="Name", first_name="First", last_name="Last", type=Type.ADMIN), True, False),
        (Person(email="1@test.com", name="Name", first_name="First", last_name="Last", type=Type.USER), False, True),
    ])
    def test_000_check_properties(self, value: Person, admin: bool, user: bool):
        self.assertEqual(admin, value.admin(), "Check admin()")
        self.assertEqual(user, value.user(), "Check user()")

    def test_000_find(self):
        response = client.get("/people")
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(0, results.total, "Check total")
        self.assertEqual(0, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")

    def test_000_get(self):
        response = client.get("/people/person-1")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_010_post(self):
        response = client.post("/people", json=VALUE)
        self.assertEqual(201, response.status_code, "Check status_code")

        value = Person(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNone(value.auth_at, "Check auth_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

    def test_010_post_dupe(self):
        value = VALUE.copy()
        value["id"] = "person-0"
        response = client.post("/people", json=value)
        self.assertEqual(422, response.status_code, "Check status_code")

        results = response.json()
        self.assertIsNotNone(results, "Check results")
        self.assertEqual({"detail":[], "title": "The email is already in use by another person_."}, results, "Check results")

    def test_010_post_get(self):
        response = client.get("/people/person-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Person(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertEqual("First 1", value.first_name, "Check first_name")
        self.assertEqual("Last 1", value.last_name, "Check last_name")
        self.assertEqual("Name 1", value.name, "Check name")
        self.assertEqual(Type.USER, value.type, "Check type")
        self.assertEqual(Source.GITHUB, value.source, "Check source")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNone(value.auth_at, "Check auth_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

    def test_010_post_get_by_email_fail(self):
        self.assertRaises(HTTPError, lambda: person_dao.get_by_email("first@test.co"))

    def test_010_post_get_by_email_success(self):
        value = person_dao.get_by_email("FIRST@test.com")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")

    def test_010_post_get_by_email__fail(self):
        self.assertIsNone(person_dao.get_by_email_("first@test.co"))

    def test_010_post_get_by_email__success(self):
        value = person_dao.get_by_email_("FIRST@test.com")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")

    def test_010_post_put(self):
        value = VALUE.copy()
        value["first_name"] = "First One"

        response = client.put("/people", json=value)
        self.assertEqual(200, response.status_code, "Check status_code")

    def test_010_post_put_get(self):
        response = client.get("/people/person-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Person(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertEqual("First One", value.first_name, "Check first_name")
        self.assertEqual("Last 1", value.last_name, "Check last_name")
        self.assertEqual("Name 1", value.name, "Check name")
        self.assertEquals(Type.USER, value.type, "Check type")
        self.assertEqual(Source.GITHUB, value.source, "Check source")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNone(value.auth_at, "Check auth_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    def test_020_patch(self):
        response = client.patch("/people/person-1", json={"last_name": "Last One", "type": "admin", "source": "Google"})
        self.assertEqual(200, response.status_code, "Check status_code")

    def test_020_patch_get(self):
        response = client.get("/people/person-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Person(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("person-1", value.id, "Check ID")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertEqual("First One", value.first_name, "Check first_name")
        self.assertEqual("Last One", value.last_name, "Check last_name")
        self.assertEqual("Name 1", value.name, "Check name")
        self.assertEqual(Type.ADMIN, value.type, "Check type")
        self.assertEqual(Source.GOOGLE, value.source, "Check source")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNone(value.auth_at, "Check auth_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    @parameterized.expand([
        ({}, 1),
        ({"ids": ["person-0", "person-1", "person-2"]}, 1),
        ({"ids": ["person-0", "person-3", "person-2"]}, 0),
        ({"email": "FIRST@test.com"}, 1),
        ({"email": "first@test.co"}, 0),
        ({"first_name": "one"}, 1),
        ({"first_name": "Two"}, 0),
        ({"last_name": "one"}, 1),
        ({"last_name": "Two"}, 0),
        ({"name": "name"}, 1),
        ({"name": "test"}, 0),
        ({"type": "admin"}, 1),
        ({"type": "user"}, 0),
        ({"source": "GitHub"}, 0),
        ({"source": "Google"}, 1),
        ({"source": "Email"}, 0),
        ({"archived_at_from": minutesAgo}, 0),
        ({"archived_at_to": minutesAhead}, 0),
        ({"has_archived_at": True}, 0),
        ({"has_archived_at": False}, 1),
        ({"auth_at_from": minutesAgo}, 0),
        ({"auth_at_to": minutesAhead}, 0),
        ({"has_auth_at": True}, 0),
        ({"has_auth_at": False}, 1),
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
    def test_030_find(self, filter_: dict[str, Any], expected: int):
        response = client.get("/people", params=filter_)
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(expected, results.total, "Check total")
        self.assertEqual(expected, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(expected, len(results.scores), "Check scores")

    def test_035_auth(self):
        person_dao.auth("FIRST@test.com")

    def test_035_auth_get(self):
        value = Person(**client.get("/people/person-1").json())
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.auth_at, "Check auth_at")
        self.assertLess(value.created_at, value.updated_at, "Check created_at")
        self.assertEqual(value.auth_at, value.updated_at, "Check updated_at")

    def test_040_archive(self):
        response = client.delete("/people/person-1/archive")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_040_archive_get(self):
        value = Person(**client.get("/people/person-1").json())
        self.assertIsNotNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.auth_at, "Check auth_at")
        self.assertLess(value.created_at, value.updated_at, "Check created_at")
        self.assertEqual(value.archived_at, value.updated_at, "Check updated_at")
        self.assertLess(value.auth_at, value.updated_at, "Check updated_at")

    def test_050_auth(self):
        self.assertRaises(ValidationError, lambda: person_dao.auth("first@test.com"))

    @parameterized.expand([
        ({"archived_at_from": minutesAgo}, 1),
        ({"archived_at_from": minutesAhead}, 0),
        ({"archived_at_to": minutesAhead}, 1),
        ({"archived_at_to": minutesAgo}, 0),
        ({"has_archived_at": True}, 1),
        ({"has_archived_at": False}, 0),
        ({"auth_at_from": minutesAgo}, 1),
        ({"auth_at_from": minutesAhead}, 0),
        ({"auth_at_to": minutesAhead}, 1),
        ({"auth_at_to": minutesAgo}, 0),
        ({"has_auth_at": True}, 1),
        ({"has_auth_at": False}, 0),
    ])
    def test_060_find(self, filter_: dict[str, Any], expected: int):
        response = client.get("/people", params=filter_)
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(expected, results.total, "Check total")
        self.assertEqual(expected, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(expected, len(results.scores), "Check scores")

    def test_070_load(self):
        person_dao.load([
            {
                "id": f"person-{i}",
                "email": f"email{i}@test.com",
                "first_name": f"First {i}",
                "last_name": f"Last {i}",
                "name": f"Name {i}",
                "type": Type.ADMIN.value if 0 == (i % 2) else Type.USER.value,
                "source": sources[i % 3].value
            }
            for i in range(2, 11)
        ])

        person_dao.refresh()

    @parameterized.expand([
        (PersonSearchRequest(type=Type.USER), 4),
        (PersonSearchRequest(type=Type.ADMIN), 6),
        (PersonSearchRequest(source=Source.GITHUB), 3),
        (PersonSearchRequest(source=Source.GOOGLE), 4),
        (PersonSearchRequest(source=Source.EMAIL), 3)
    ])
    def test_070_load_count(self, filter_: PersonSearchRequest, expected: int):
        self.assertEqual(expected, person_dao.count(filter_))

    def test_070_load_find(self):
        response = client.get("/people", params={"size": 5, "scroll": "30s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(5, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(5, len(results.scores), "Check scores")

        PersonEndpointsTest.scroll_id = results.scroll_id

    def test_070_load_scroll_0(self):
        response = client.get(f"/people/scroll/{self.scroll_id}")
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(5, len(results.data), "Check data")
        self.assertIsNotNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(5, len(results.scores), "Check scores")

        PersonEndpointsTest.scroll_id = results.scroll_id

    def test_070_load_scroll_1(self):
        response = client.get(f"/people/scroll/{self.scroll_id}")
        self.assertEqual(200, response.status_code, "Check status_code")

        results = Results[Person](**response.json())
        self.assertIsNotNone(results, "Exists")
        self.assertEqual(10, results.total, "Check total")
        self.assertEqual(0, len(results.data), "Check data")
        self.assertIsNone(results.scroll_id, "Check scroll_id")
        self.assertEqual(0, len(results.scores), "Check scores")

    def test_999_delete(self):
        response = client.delete("/people/person-1")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_999_delete_get(self):
        response = client.get("/people/person-1")
        self.assertEqual(404, response.status_code, "Check status_code")

if __name__ == '__main__':
    unittest.main()
