from .mailer import Mailer
from .dao.otp import Token
from unittest import TestCase
from .dao.person import Person
from urllib.error import HTTPError

mailer = Mailer()

class MailerTest(TestCase):
    def test_creation_failure(self):
        self.assertRaises(Exception, lambda: Mailer(key_name="INVALID"))

    def test_send_otp_message__invalid(self):
        self.assertRaises(HTTPError, lambda: mailer.send_otp_message(
            email="invalid",
            token=Token(value="token-1"),
            person=Person(id="person-1", email="bokenrunner@gmail.com", name="First Person", first_name="First", last_name="Person")
        ))

    def test_send_otp_message__login(self):
        mailer.send_otp_message(
            email="bokenrunner@gmail.com",
            token=Token(value="token-1"),
            person=Person(id="person-1", email="bokenrunner@gmail.com", name="First Person", first_name="First", last_name="Person")
        )

    def test_send_otp_message__register(self):
        mailer.send_otp_message(
            email="bokenrunner@gmail.com",
            token=Token(value="token-2")
        )
