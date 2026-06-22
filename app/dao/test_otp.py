import unittest
from .otp import OtpDao
from ..myredis.tester import pool
from datetime import datetime, timedelta

dao = OtpDao(pool, 1)
now = datetime.now()
ago = now + timedelta(minutes=9)
ahead = now + timedelta(minutes=12)

class OtpDaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = None

    def setUp(self):
        self.token = OtpDaoTest.token

    def test_000_generate(self):
        token = dao.generate("first@test.com")
        self.assertIsNotNone(token, "Exists")
        self.assertEqual(6, len(token.value), "Check value")
        self.assertLess(ago, token.expires_at, "Check expires_at")
        self.assertGreater(ahead, token.expires_at, "Check expires_at")
        self.assertEqual(0, token.failures, "Check failures")

        OtpDaoTest.token = token

    def test_010_ttl_invalid(self):
        self.assertEqual(-2, dao.ttl("second@test.com"))

    def test_010_ttl_valid(self):
        ttl = dao.ttl("first@test.com")
        self.assertLess(595, ttl)
        self.assertGreaterEqual(600, ttl)

    def test_020_check_fail(self):
        self.assertFalse(dao.check("first@test.com", "invalid"))
        self.assertLess(535, dao.ttl("first@test.com"))

    def test_020_check_invalid(self):
        self.assertFalse(dao.check("second@test.com", self.token.value))
        self.assertLess(535, dao.ttl("first@test.com"))

    def test_020_check_success(self):
        self.assertTrue(dao.check("first@test.com", self.token.value))
        self.assertEqual(-2, dao.ttl("first@test.com"))

    def test_030_generate(self):
        token = dao.generate("first@test.com")
        self.assertIsNotNone(token, "Exists")
        self.assertEqual(6, len(token.value), "Check value")
        self.assertNotEqual(self.token.value, token.value, "Check value")
        self.assertEqual(0, token.failures, "Check failures")

        OtpDaoTest.token = token

    def test_030_generate_fail(self):
        for i in range(0, 5):
            minutes = i * 60
            ttl = dao.ttl("first@test.com")
            self.assertLess(595 - minutes, ttl, "Check ttl")
            self.assertGreaterEqual(600 - minutes, ttl, "Check ttl")
            self.assertFalse(dao.check("first@test.com", "invalid"), "Check results")

        self.assertEqual(-2, dao.ttl("first@test.com"), "Check ttl")

    def test_030_generate_too_many_failures(self):
        self.assertFalse(dao.check("first@test.com", self.token.value))
