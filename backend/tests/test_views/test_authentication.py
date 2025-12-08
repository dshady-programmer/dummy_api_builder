"""
Full test on user authentication, signup, login, logout, user details(me)
"""
from tests import TestConfig
from models.user import User
from datetime import timedelta

def dummy_jwt(secret=False):
    import uuid
    from datetime import datetime, timedelta, timezone
    import jwt
    from api.v1.app import app
    token = jwt.encode(
        {
            "public_id": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
            "jti": str(uuid.uuid4())
        },
        "test_secret" if secret else app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return token


class TestSignUp(TestConfig):
    """
    Testing the api/v1/signup endpoint
    """
    def setUp(self):
        self.endpoint = "api/v1/signup"
        super().setUp()
    
    

    def test_signup_with_incorrect_method(self):
        """
        Testing sign up with methods other than post method
        """
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)

        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
            self.assertRegex(res.data.decode('utf-8'), r".*Method Not Allowed.*")

    def test_signup_with_none_passed_as_json(self):
        """
        Tests that the application doesn't break when none is passed as json value
        """
        resp = self.client.post(self.endpoint, json=None, headers={"content-type": "application/json"})
        self.assertEqual(resp.status_code, 400)

    def test_signup_with_incomplete_credentials(self):
        """
        Testing signp with incomplete credentials
        """
        expected_err_msg = "email, password, confirm_password fields are all required"
        # test without an email

        resp = self.client.post(self.endpoint, json={"password": "134", "confirm_password": "134"})

        # test without password
        resp2 = self.client.post(self.endpoint, json={"email":"johndoe@mail.com"})

        #test without confirm password
        resp3 = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": "142"})

        
        for res in [resp, resp2, resp3]:

            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json["error"], expected_err_msg)
        

    def test_signup_with_complete_credentials_but_with_short_passwords(self):
        """
        Testing signup with short password, password must atleast be 8 characters to pass this test
        """
        expected_err_msg = "Password validation failed"
        resp = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": "1235", "confirm_password": "1235"})
        resp2 = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": "1235353", "confirm_password": "1235353"})
        resp3 = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": None, "confirm_password": None})
        
        for res in [resp, resp2]:
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json["error"], expected_err_msg)
        self.assertEqual(resp3.status_code, 401)
        self.assertEqual(resp3.json["error"], "email, password, confirm_password fields are all required")


    def test_signup_with_complete_credentials_but_with_non_matching_passwords(self):
        """
        Tests signup endpoint with non matching password and confirm password field
        """
        expected_err_msg = "Password validation failed"
        resp = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": "282802503985", "confirm_password": "0250852708522"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json["error"], expected_err_msg)

    def test_signup_with_complete_and_correct_credentials(self):
        """
        Test signup when the user provides complete and correct credentials
        """

        expected_success_msg = "Account registered successfully"
        resp = self.client.post(self.endpoint, json={"email":"johndoe@mail.com", "password": "123456789", "confirm_password": "123456789"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json["message"], expected_success_msg)
        # confirm user was created
        with self.app.app_context():
            q = User.query.all()
            self.assertEqual(len(q), 1)
            self.assertEqual(q[0].email, "johndoe@mail.com")

    def test_signup_with_already_existing_email(self):
        """
        Test signup with already existing email
        """
        expected_success_msg = "Account registered successfully"
        expected_err_msg = "Account already exists, please login"
        resp = self.client.post(self.endpoint, json={"email":"johndoe@mail.com", "password": "123456789", "confirm_password": "123456789"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json["message"], expected_success_msg)

       
        # attempt to create another user with same email
        resp2 = self.client.post(self.endpoint, json={"email":"johndoe@mail.com", "password": "password", "confirm_password": "password"})
        self.assertEqual(resp2.status_code, 202)
        self.assertEqual(resp2.json["message"], expected_err_msg)

         # confirm we still have only one user in the database
        with self.app.app_context():
            q = User.query.all()
            self.assertEqual(len(q), 1)
            self.assertEqual(q[0].email, "johndoe@mail.com")
 

class TestLogin(TestConfig):
    """
    Testing the login endpoint
    """
    def setUp(self):
        self.endpoint = "api/v1/login"
        super().setUp()
        self.user1 = self.client.post("api/v1/signup", json={"email":"johndoe@mail.com", "password": "123456789", "confirm_password": "123456789"})
        self.user2 = self.client.post("api/v1/signup", json={"email":"testuser@mail.com", "password": "password", "confirm_password": "password"})

    def test_login_with_incorrect_method(self):
        """
        Testing login with methods other than post method
        """
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)

        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
            self.assertRegex(res.data.decode('utf-8'), r".*Method Not Allowed.*")

    def test_login_with_none_passed_as_json(self):
        """
        Tests that the application doesn't break when none is passed as json value
        """
        resp = self.client.post(self.endpoint, json=None, headers={"content-type": "application/json"})
        self.assertEqual(resp.status_code, 400)
    
    def test_login_with_incomplete_credentials(self):
        """
        Testing login with incomplete credentials
        """
        expected_err_msg = "email and password fields are required"
        # test without an email

        resp = self.client.post(self.endpoint, json={"password": "134"})

        # test without password
        resp2 = self.client.post(self.endpoint, json={"email":"johndoe@mail.com"})

        # test with None value
        resp3 = self.client.post(self.endpoint, json={"email": "johndoe@mail.com", "password": None})
        for res in [resp, resp2]:
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json["error"], expected_err_msg)

    def test_login_with_non_existing_email(self):
        """
        Test the login route with non-existing email
        """
        expected_err_msg = "Incorrect email or password"
        res = self.client.post(self.endpoint, json={"email": "example@mail.com", "password": "2342442422"})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)

    def test_login_with_wrong_password(self):
        """
        Test login with correct email but wrong password
        """
        expected_err_msg = "Incorrect email or password"
        data1 = {"email": "johndoe@mail.com", "password": "200942820840"}
        data2 = {"email": "testuser@mail.com", "password": "password123"}
        resp1 = self.client.post(self.endpoint, json=data1)
        resp2 = self.client.post(self.endpoint, json=data2)

        for res in [resp1,resp2]:
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json["error"], expected_err_msg)

    def test_login_with_correct_credentials(self):
        """
        Test login with correct credentials
        """
        data1 = {"email":"johndoe@mail.com", "password": "123456789"}
        data2 = {"email":"testuser@mail.com", "password": "password"}
        user1 = self.client.post(self.endpoint, json=data1)
        user2 = self.client.post(self.endpoint, json=data2)
        for user in [user1, user2]:
            self.assertEqual(user.status_code, 200)
            self.assertTrue(user.json["token"])

        # confirm tokens are different
        self.assertNotEqual(user1.json["token"], user2.json["token"])
        with self.app.app_context():

            users = User.query.all()
            for user in users:
                self.assertIsNotNone(user.public_id)

    def test_login_same_account_with_multiple_sessions(self):
        """
        Test Login same account with multiple sessions
        """
        with self.app.app_context():
            data = {"email":"johndoe@mail.com", "password": "123456789"}
            session1 = self.client.post(self.endpoint, json=data)
            # capture public_id for first session
            p_id1 = User.query.filter_by(email="johndoe@mail.com").first().public_id
            
            session2 = self.client.post(self.endpoint, json=data)
            # capture public_id for second session
            p_id2 = User.query.filter_by(email="johndoe@mail.com").first().public_id


            for session in [session1, session2]:
                self.assertEqual(session.status_code, 200)
                self.assertTrue(session.json["token"])

            
            # Confirm tokens are different
            self.assertNotEqual(session2.json["token"], session1.json["token"])
            
            
            #confirm public ids are same
            self.assertEqual(p_id1, p_id2)

    
    def test_public_id_rotation_after_a_while(self):
        """
        Test that public id is rotated after the last_created time as elapse
        """
        with self.app.app_context():
            data = {"email":"johndoe@mail.com", "password": "123456789"}
            session1 = self.client.post(self.endpoint, json=data)
            # capture public_id for first session
            u1 = User.query.filter_by(email="johndoe@mail.com").first()
            p_id1 = u1.public_id
            #making the public_id expire
            u1.last_public_id_created -= timedelta(days=2)
            self.db.session.add(u1)
            self.db.session.commit()

            # now logging in again
            session2 = self.client.post(self.endpoint, json=data)
            # capture public_id for second session
            u2 = User.query.filter_by(email="johndoe@mail.com").first()
            p_id2 = u2.public_id

            for session in [session1, session2]:
                self.assertEqual(session.status_code, 200)
                self.assertTrue(session.json["token"])
            # confirm tokens are different
            self.assertNotEqual(session2.json["token"], session1.json["token"])
            
            #confirm public ids are different
            self.assertNotEqual(p_id1, p_id2)






class TestLoginRequiredAndUserDetails(TestConfig):
    """
    Testing the login required util function and getting user detail endpoint
    """
    def setUp(self):
        self.endpoint = "api/v1/me"
        super().setUp()
        self.data1 = {"email":"johndoe@mail.com", "password": "123456789"}
        self.data2 = {"email":"testuser@mail.com", "password": "password"}
        self.user1 = self.client.post("api/v1/signup", json={"email":"johndoe@mail.com", "password": "123456789", "confirm_password": "123456789"})
        self.user2 = self.client.post("api/v1/signup", json={"email":"testuser@mail.com", "password": "password", "confirm_password": "password"})
        self.session1 = self.client.post("api/v1/login", json=self.data1)
        self.session2 = self.client.post("api/v1/login", json=self.data2)
    

    def test_user_detail_endpoint_with_wrong_method(self):
        """
         Testing the user detail endpoint with the wrong the request method
        """

        resp1 = self.client.post(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        resp4 = self.client.patch(self.endpoint)

        for res in [resp1, resp2, resp3, resp4]:
            self.assertEqual(res.status_code, 405)
            self.assertRegex(res.data.decode('utf-8'), r".*Method Not Allowed.*")

    def test_user_detail_endpoint_without_tokens(self):
        """
        Test the user detail endpoint without token, this test indirectly tests the login_required util function
        """
        expected_err_msg = "Token is missing"
        res = self.client.get(self.endpoint)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)

    def test_user_detail_endpoint_with_invalid_token(self):
        """
        Test user detail endpoint with a token, but invalid token!!!
        """
        expected_err_msg = "Token is invalid !!"
        res = self.client.get(self.endpoint, headers={'x-access-token': dummy_jwt(True)})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)
    
    def test_user_detail_endpoint_with_wrong_token(self):
        """
        Test user detail endpoint with a token that is valid jwt but wrong
        """
        expected_err_msg = "invalid credentials, please log in or create an account"
        res = self.client.get(self.endpoint, headers={'x-access-token': dummy_jwt()})
        self.assertEqual(res.status_code, 401)
        print("user detail with wrong token", res.json['error'])
        self.assertEqual(res.json["error"], expected_err_msg)

    
    def test_user_detail_endpoint_with_correct_token(self):
        """
        Getting user details succesfully with the correct token
        """
        resp1 = self.client.get(self.endpoint, headers={'x-access-token': self.session1.json["token"]})
        resp2 = self.client.get(self.endpoint, headers={'x-access-token': self.session2.json["token"]})
        for res in [resp1, resp2]:
            self.assertEqual(res.status_code, 200)
        self.assertEqual(resp1.json["email"], self.data1["email"])
        self.assertEqual(resp2.json["email"], self.data2["email"])

        with self.app.app_context():
            u1 = User.query.filter_by(email=self.data1["email"]).first()
            u2 = User.query.filter_by(email=self.data2["email"]).first()
            self.assertEqual(u1.api_token, resp1.json["api_token"])
            self.assertEqual(u2.api_token, resp2.json["api_token"])


class TestLogoutView(TestConfig):
    """
    Testing the logout view
    """
    def setUp(self):
        self.endpoint = "api/v1/logout"
        super().setUp()
        self.data1 = {"email":"johndoe@mail.com", "password": "123456789"}
        self.data2 = {"email":"testuser@mail.com", "password": "password"}
        self.user1 = self.client.post("api/v1/signup", json={"email":"johndoe@mail.com", "password": "123456789", "confirm_password": "123456789"})
        self.user2 = self.client.post("api/v1/signup", json={"email":"testuser@mail.com", "password": "password", "confirm_password": "password"})
        self.session1 = self.client.post("api/v1/login", json=self.data1)
        self.session2 = self.client.post("api/v1/login", json=self.data2)
    

    def test_user_detail_endpoint_with_wrong_method(self):
        """
         Testing the logout endpoint with the wrong the request method
        """

        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        resp4 = self.client.patch(self.endpoint)

        for res in [resp1, resp2, resp3, resp4]:
            self.assertEqual(res.status_code, 405)
            self.assertRegex(res.data.decode('utf-8'), r".*Method Not Allowed.*")

    def test_logout_endpoint_without_tokens(self):
        """
        Test the logout endpoint without token, this test indirectly tests the login_required util function
        """
        expected_err_msg = "Token is missing"
        res = self.client.post(self.endpoint)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)

    def test_logout_endpoint_with_invalid_token(self):
        """
        Test logout endpoint with a token, but invalid token!!!
        """
        expected_err_msg = "Token is invalid !!"
        res = self.client.post(self.endpoint, headers={'x-access-token': dummy_jwt(True)})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)
    
    def test_logout_endpoint_with_wrong_token(self):
        """
        Test logout endpoint with a token that is valid jwt but wrong i.e no user associated
        """
        expected_err_msg = "invalid credentials, please log in or create an account"

        res = self.client.post(self.endpoint, headers={'x-access-token': dummy_jwt()})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json["error"], expected_err_msg)
    
    def test_logout_endpoint_with_correct_token(self):
        """
        Test logging out succesfully with the correct token
        """
        resp1 = self.client.post(self.endpoint, headers={'x-access-token': self.session1.json["token"]})
        resp2 = self.client.post(self.endpoint, headers={'x-access-token': self.session2.json["token"]})
        for res in [resp1, resp2]:
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json["message"], "Logged out")
        

        with self.app.app_context():
            u1 = User.query.filter_by(email=self.data1["email"]).first()
            u2 = User.query.filter_by(email=self.data2["email"]).first()
            self.assertIsNone(u1.public_id)
            self.assertIsNone(u2.public_id)

    