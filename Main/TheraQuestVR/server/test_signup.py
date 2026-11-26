import unittest

from testsupport import ServerTestCase, TEST_USER, TEST_PASSWORD


class SignupTests(ServerTestCase):

    def signup(self, **over):
        body = {"name": "Dr New", "username": "newdoc", "password": "new-doc-pass-1",
                "approver_username": TEST_USER, "approver_password": TEST_PASSWORD}
        body.update(over)
        return self.call("POST", "/api/auth/signup", body)

    def test_approved_signup_creates_login_that_can_sign_in(self):
        status, body = self.signup()
        self.assertEqual(status, 201, body)
        self.assertEqual(body["therapist"]["username"], "newdoc")
        status, _ = self.call("POST", "/api/auth/login", {"username": "NewDoc", "password": "new-doc-pass-1"})
        self.assertEqual(status, 200)
        status, _ = self.call("GET", "/api/patients", headers={"Authorization": f"Bearer {body['token']}"})
        self.assertEqual(status, 200)

    def test_wrong_or_missing_approver_is_refused_and_creates_nothing(self):
        status, _ = self.signup(username="sneaky", approver_password="wrong-password-1")
        self.assertEqual(status, 401)
        status, _ = self.signup(username="sneaky", approver_username="", approver_password="")
        self.assertEqual(status, 400)
        status, _ = self.call("POST", "/api/auth/login", {"username": "sneaky", "password": "new-doc-pass-1"})
        self.assertEqual(status, 401)

    def test_duplicate_username_and_weak_password_are_refused(self):
        status, _ = self.signup(username=TEST_USER.upper())
        self.assertEqual(status, 409)
        status, _ = self.signup(username="shorty", password="short")
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
