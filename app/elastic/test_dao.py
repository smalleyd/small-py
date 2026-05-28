import unittest
from typing import Any
from urllib.error import HTTPError

from .dao import BaseDAO
from datetime import datetime, timedelta
from elasticsearch import (
    Elasticsearch,
    NotFoundError
)
from parameterized import parameterized
from ..models.person import Person, PersonSearchRequest

class TestBaseDAO(BaseDAO[Person, PersonSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(es, "person", Person)

    def _build_query(self, f: PersonSearchRequest) -> dict[str, Any]:
        o = []
        if f.ids:
            o.append({"ids": {"values": f.ids}})
        if f.name:
            o.append({"match": {"name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.email:
            o.append({"term": {"email.keyword": f.email}})

        return {"bool": {"must": o}}

class BaseDAOTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = cls.es = BaseDAO.connect()
        # cls.dao = BaseDAO[Person, PersonSearchRequest](client, "person", Person)
        cls.dao = TestBaseDAO(client)

        cls.value = None
        cls.initial_count = 0

    def setUp(self):
        self.dao = BaseDAOTest.dao
        self.value = BaseDAOTest.value
        self.initial_count = BaseDAOTest.initial_count

    @classmethod
    def tearDownClass(cls):
        if cls.es: cls.es.close()

    def tearDown(self):
        self.dao.refresh()

    @parameterized.expand([
        ({"envCreds":"invalid"}, Exception),
        ({"envCreds": "HOME"}, Exception),
    ])
    def test_00_connect_fail(self, args: dict[str, Any], exception: type[BaseException]):
        self.assertRaises(exception, lambda: BaseDAO.connect(**args))

    @parameterized.expand([
        ({"envHost":"invalid.com"}, NotFoundError)
    ])
    def test_00_connect_invalid(self, args: dict[str, Any], exception: type[BaseException]):
        self.assertFalse(BaseDAO.connect(**args).ping())

    def test_00_create(self):
        BaseDAOTest.initial_count = self.dao.count(PersonSearchRequest())
        value = BaseDAOTest.value = self.dao.add(Person(id="test-person-1", name="First Person", email="first@test.com"))

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNone(value.created_at, "Check created_at")
        self.assertIsNone(value.updated_at, "Check updated_at")

    def test_00_create_check(self):
        value = self.dao.get("test-person-1")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNone(value.created_at, "Check created_at")
        self.assertIsNone(value.updated_at, "Check updated_at")

        self.assertEqual(self.initial_count + 1, self.dao.count(PersonSearchRequest()), "Check count")

    def test_00_create_doesExist(self):
        self.assertIsNone(self.dao.does_exist("test-person-1"))

    def test_00_create_doesNotExist(self):
        self.assertRaises(HTTPError, lambda: self.dao.does_exist("test-person-2"))

    def test_00_create_exists(self):
        self.assertTrue(self.dao.exists("test-person-1"), "Check exists")

    @parameterized.expand(
        [(PersonSearchRequest(), True), (PersonSearchRequest(ids=["one"]), False)]
    )
    def test_00_empty(self, f: PersonSearchRequest, expected: bool):
        self.assertEqual(expected, self.dao.empty(f))

    def test_00_field_created_at(self):
        self.assertEqual("created_at", self.dao.field_created_at)

    def test_00_field_updated_at(self):
        self.assertEqual("updated_at", self.dao.field_updated_at)

    @parameterized.expand([
        ("test-person-1", None),
        ("test-person-2", None)
    ])
    def test_00_get_created_at(self, id:str, expected: datetime | None):
        self.assertEqual(expected, self.dao.get_created_at(id))

    def test_00_ping(self):
        self.assertTrue(self.dao.ping())

    @parameterized.expand([
        (PersonSearchRequest(ids=["test-person-1"]), 1),
        (PersonSearchRequest(ids=["test-person-1-invalid"]), 0),
        (PersonSearchRequest(name="\"First Person\""), 1),
        (PersonSearchRequest(name="totally-invalid"), 0),
        (PersonSearchRequest(email="first@test.com"), 1),
        (PersonSearchRequest(email="invalid@test.com"), 0)
    ])
    def test_10_search(self, f: PersonSearchRequest, expected: int):
        values = self.dao.search(f)
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(expected, len(values), "Check size")

    def test_20_remove(self):
        self.dao.remove("test-person-1")

    def test_20_remove_exists(self):
        self.assertFalse(self.dao.exists("test-person-1"))

    def test_30_upsert(self):
        now = datetime.now()
        delta = timedelta(seconds=5)
        value = self.dao.upsert(Person(id="test-person-1", name="First Person", email="first@test.com"))

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertGreater(value.created_at, now, "Check created_at")
        self.assertLess(value.created_at, now + delta, "Check created_at")
        self.assertIsNotNone(value.updated_at, "Check updated_at")
        self.assertGreater(value.updated_at, now, "Check updated_at")
        self.assertLess(value.updated_at, now + delta, "Check updated_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

    def test_30_upsert_again(self):
        now = datetime.now()
        delta = timedelta(seconds=5)
        value = self.dao.upsert(Person(id="test-person-1", name="First Person", email="first@test.com"))

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertIsNotNone(value.updated_at, "Check updated_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

        BaseDAOTest.value = value

    def test_40_patch(self):
        self.dao.patch("test-person-1", {"name": "Person First X"})

    def test_40_patch_a(self):
        self.dao.patch("test-person-1",
            {"id": "test-person-0", "name": "Person First", "created_at": datetime.now()})

    def test_40_patch_fail(self):
        self.assertRaises(HTTPError, lambda: self.dao.patch("test-person-0", {"name": "X First"}))

    def test_40_patch_get(self):
        value = self.dao.get("test-person-1")

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("Person First", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertIsNotNone(value.updated_at, "Check updated_at")
        self.assertEqual(self.value.created_at, value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")
        self.assertLess(self.value.updated_at, value.updated_at, "Check updated_at")

    def test_99_remove(self):
        self.dao.remove("test-person-1")

    def test_99_remove_count(self):
        self.assertEqual(self.initial_count, self.dao.count(PersonSearchRequest()), "Check count")

    def test_99_remove_exists(self):
        self.assertFalse(self.dao.exists("test-person-1"), "Check exists")

    def test_99_remove_get(self):
        self.assertRaises(NotFoundError, lambda: self.dao.get("test-person-1"))

if __name__ == "__main__":
    unittest.main()