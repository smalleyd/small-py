import unittest
from typing import Any
from urllib.error import HTTPError

from .dao import BaseDAO
from ..elastic import tester
from datetime import datetime, timedelta
from elasticsearch import (
    Elasticsearch,
    NotFoundError
)
from parameterized import parameterized
from ..models.person import Person, PersonSearchRequest, Role

minute = timedelta(minutes=1)

class TestBaseDAO(BaseDAO[Person, PersonSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(es, "person", Person,{"properties":{
            "id": {"type": "keyword"},
            "email": {"type": "keyword","normalizer": "lowercase"},
            "name": {"type": "text"},
            "role": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "created_at":{"type":"date"},
            "updated_at":{"type":"date"}
        }})
        self.before_save_exists:bool | None = None

    def before_save(self, id:str, value: dict[str, Any], exists: bool) -> dict[str, Any]:
        self.before_save_exists = exists
        return value

    def _build_query(self, f: PersonSearchRequest) -> dict[str, Any]:
        o = []
        if f.ids:
            o.append({"ids": {"values": f.ids}})
        if f.name:
            o.append({"match": {"name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.email:
            o.append({"term": {"email": f.email}})
        if f.role:
            o.append({"term": {"role": f.role.value}})
        if f.tags:
            o.append({"terms": {"tags": f.tags}})

        self.range_query(o, "created_at", f.created_at_from, f.created_at_to)

        return {"bool": {"must": o}}

class BaseDAOTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = None
        cls.scroll_id = None
        cls.initial_count = 0
        cls.es = tester.client
        cls.dao = TestBaseDAO(tester.client)

        TestBaseDAO(tester.client)  # Do a second time to test the update of the index mappings.

    def setUp(self):
        self.dao = BaseDAOTest.dao
        self.value = BaseDAOTest.value
        self.scroll_id = BaseDAOTest.scroll_id
        self.initial_count = BaseDAOTest.initial_count

    @classmethod
    def tearDownClass(cls):
        """Do NOT close anything as these Elastic components can be used by other tests."""
        pass
        # if cls.es: cls.es.close()
        # if tester.container: tester.container.stop() Do NOT stop because it can be used in other tests.

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
        self.assertEqual(0, self.dao.count(PersonSearchRequest()), "Check intial count");

        value = BaseDAOTest.value = self.dao.add(Person(id="test-person-1", name="First Person", email="first@test.com", role=Role.ADMIN, tags={"monday", "tuesday", "wednesday"}))

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertEqual(Role.ADMIN, value.role, "Check role")
        self.assertEqual({"monday", "tuesday", "wednesday"}, value.tags, "Check tags")
        self.assertIsNone(value.created_at, "Check created_at")
        self.assertIsNone(value.updated_at, "Check updated_at")
        self.assertIsNone(self.dao.before_save_exists, "Check dao_before_save_exists")

    def test_00_create_check(self):
        value = self.dao.get("test-person-1")
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")
        self.assertEqual(Role.ADMIN, value.role, "Check role")
        self.assertEqual({"monday", "tuesday", "wednesday"}, value.tags, "Check tags")
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

    def test_00_load(self):
        self.dao.load([{"id": f"test-people-{i}", "name": f"People {i}", "email": f"{i}@test.com"} for i in range(1, 11)])
        self.dao.refresh()
        BaseDAOTest.initial_count = 10

    def test_00_ping(self):
        self.assertTrue(self.dao.ping())

    def test_00_total_size_in_bytes(self):
        bytes = self.dao.total_size_in_bytes()
        self.assertLess(10000, bytes)
        self.assertGreater(20000, bytes)

    @parameterized.expand([
        ({"match_all":{}}, 5, 5),
        ({"ids":{"values":["test-people-3", "test-people-100", "test-people-6", "test-people-200", "test-people-9"]}}, 100, 3),
        ({"ids": {"values": ["test-people-300", "test-people-100", "test-people-600", "test-people-200", "test-people-900"]}}, 100, 0)
    ])
    def test_10_ids(self, query: dict[str, Any], size: int, expected: int):
        value = self.dao.ids(query, size)
        self.assertEqual(expected, len(value), "Check length")

    @parameterized.expand([
        (PersonSearchRequest(ids=["test-person-1"]), 1, 1),
        (PersonSearchRequest(ids=["test-person-1"], page=2), 0, 1),
        (PersonSearchRequest(ids=["test-person-1-invalid"]), 0, 0),
        (PersonSearchRequest(name="\"First Person\""), 1, 1),
        (PersonSearchRequest(name="totally-invalid"), 0, 0),
        (PersonSearchRequest(email="first@test.com"), 1, 1),
        (PersonSearchRequest(email="invalid@test.com"), 0, 0),
        (PersonSearchRequest(role=Role.ADMIN), 1, 1),
        (PersonSearchRequest(role=Role.USER), 0, 0),
        (PersonSearchRequest(tags=["sunday","tuesday","thursday"]), 1, 1),
        (PersonSearchRequest(tags=["sunday","Tuesday","thursday"]), 0, 0)
    ])
    def test_10_search(self, f: PersonSearchRequest, expected: int, total: int):
        results = self.dao.search(f)
        self.assertIsNotNone(results, "Check results")
        self.assertEqual(total, results.total, "Check results.total")
        self.assertIsNone(results.scroll_id, "Check results.scroll_id")
        self.assertIsNotNone(results.scores, "Check results.scores")
        self.assertEqual(expected, len(results.scores), "Check results.scores.size")

        values = results.data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(expected, len(values), "Check size")

    def test_10_search_exclude(self):
        values = self.dao.search(PersonSearchRequest(ids=["test-person-1"]),
            source_excludes=["name"]).data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(1, len(values), "Check size")

        value = values[0]
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertIsNone(value.name, "Check name")
        self.assertEqual("first@test.com", value.email, "Check email")

    def test_10_search_include(self):
        values = self.dao.search(PersonSearchRequest(ids=["test-person-1"]),
            source_includes=["name"]).data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(1, len(values), "Check size")

        value = values[0]
        self.assertIsNone(value.id, "Check id")
        self.assertEqual("First Person", value.name, "Check name")
        self.assertIsNone(value.email, "Check email")

    def test_10_search_paging(self):
        results = self.dao.search(PersonSearchRequest(page=1, size=5, sort=["created_at:Desc", "name:Asc"]))
        self.assertIsNotNone(results, "Check results")
        self.assertEqual(self.initial_count + 1, results.total, "Check results.total")
        self.assertIsNone(results.scroll_id, "Check results.scroll_id")
        self.assertIsNotNone(results.scores, "Check results.scores")
        self.assertEqual(5, len(results.scores), "Check results.scores.size")

        values = results.data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(5, len(values), "Check size")

    def test_10_search_scroll(self):
        results = self.dao.search(PersonSearchRequest(size=5, scroll="30s", sort=["created_at:Desc"]))
        self.assertIsNotNone(results, "Check results")
        self.assertEqual(self.initial_count + 1, results.total, "Check results.total")
        self.assertIsNotNone(results.scroll_id, "Check results.scroll_id")
        self.assertIsNotNone(results.scores, "Check results.scores")
        self.assertEqual(5, len(results.scores), "Check results.scores.size")

        values = results.data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(5, len(values), "Check size")

        BaseDAOTest.scroll_id = results.scroll_id

    def test_10_search_scroll_next(self):
        results = self.dao.scroll(self.scroll_id, "10s")
        self.assertIsNotNone(results, "Check results")
        self.assertEqual(self.initial_count + 1, results.total, "Check results.total")
        self.assertIsNotNone(results.scroll_id, "Check results.scroll_id")
        self.assertIsNotNone(results.scores, "Check results.scores")
        self.assertEqual(5, len(results.scores), "Check results.scores.size")

        values = results.data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(5, len(values), "Check size")

    def test_20_remove(self):
        self.dao.remove("test-person-1")
        self.assertIsNone(self.dao.before_save_exists, "Check dao_before_save_exists")

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
        self.assertFalse(self.dao.before_save_exists, "Check dao_before_save_exists")

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
        self.assertTrue(self.dao.before_save_exists, "Check dao_before_save_exists")

        BaseDAOTest.value = value

    @parameterized.expand([
        (PersonSearchRequest(created_at_from=datetime.now() + minute), 0),
        (PersonSearchRequest(created_at_from=datetime.now() - minute), 1),
        (PersonSearchRequest(created_at_to=datetime.now() + minute), 1),
        (PersonSearchRequest(created_at_to=datetime.now() - minute), 0),
        (PersonSearchRequest(created_at_from=datetime.now() - minute, created_at_to=datetime.now() + minute), 1),
        (PersonSearchRequest(created_at_from=datetime.now() + minute, created_at_to=datetime.now() - minute), 0)
    ])
    def test_30_upsert_search(self, f: PersonSearchRequest, expected: int):
        results = self.dao.search(f)
        self.assertIsNotNone(results, "Check results")
        self.assertEqual(expected, results.total, "Check results.total")
        self.assertIsNone(results.scroll_id, "Check results.scroll_id")
        self.assertIsNotNone(results.scores, "Check results.scores")
        self.assertEqual(expected, len(results.scores), "Check results.scores.size")

        values = results.data
        self.assertIsNotNone(values, "Exists")
        self.assertEqual(expected, len(values), "Check size")

    def test_40_patch(self):
        self.dao.patch("test-person-1", {"name": "Person First X"})
        self.assertTrue(self.dao.before_save_exists, "Check dao_before_save_exists")

    def test_40_patch_a(self):
        self.dao.patch("test-person-1",
            {"id": "test-person-0", "name": "Person First", "created_at": datetime.now()})
        self.assertTrue(self.dao.before_save_exists, "Check dao_before_save_exists")

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

        BaseDAOTest.value = value

    def test_50_set(self):
        self.dao.set("test-person-1", "email", "first@test.org")

    def test_50_set_fail(self):
        self.assertRaises(HTTPError, lambda: self.dao.set("test-person-0", "email", "first@test.net"))

    def test_50_set_get(self):
        value = self.dao.get("test-person-1")

        self.assertIsNotNone(value, "Exists")
        self.assertEqual("test-person-1", value.id, "Check id")
        self.assertEqual("Person First", value.name, "Check name")
        self.assertEqual("first@test.org", value.email, "Check email")
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