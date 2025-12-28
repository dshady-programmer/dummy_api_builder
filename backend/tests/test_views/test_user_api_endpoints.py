"""
Full tests for user_api_endpoints.py
Testing CRUD operations on user APIs
"""
from tests import TestConfig
from models.user import User
from models.api import Api
from models.table import Table


class TestUserApiEndpoints(TestConfig):
    """Test suite for user API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create test users
        self.user1_data = {"email": "user1@test.com", "password": "password123"}
        self.user2_data = {"email": "user2@test.com", "password": "password123"}
        
        self.client.post("api/v1/signup", json={**self.user1_data, "confirm_password": "password123"})
        self.client.post("api/v1/signup", json={**self.user2_data, "confirm_password": "password123"})
        
        # Login to get tokens
        self.user1_session = self.client.post("api/v1/login", json=self.user1_data)
        self.user2_session = self.client.post("api/v1/login", json=self.user2_data)
        
        self.user1_token = self.user1_session.json["token"]
        self.user2_token = self.user2_session.json["token"]


class TestMyApisList(TestUserApiEndpoints):
    """Test GET /my_apis endpoint"""
    
    def setUp(self):
        super().setUp()
        self.endpoint = "api/v1/my_apis"
    
    def test_my_apis_with_wrong_method(self):
        """Test my_apis endpoint with wrong HTTP methods"""
        resp1 = self.client.post(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_my_apis_without_token(self):
        """Test my_apis without authentication token"""
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json["error"], "Token is missing")
    
    def test_my_apis_with_invalid_token(self):
        """Test my_apis with invalid token"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': 'invalid_token'})
        self.assertEqual(resp.status_code, 401)
    
    def test_my_apis_empty_list(self):
        """Test my_apis returns empty list when user has no APIs"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.user1_token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, [])
    
    def test_my_apis_with_existing_apis(self):
        """Test my_apis returns correct APIs for user"""
        endpoint_url = "/api/v1/create_new_api"
        data1 = {
            "name": "TestApi",
            "description": "Test API Description"
        }
        data2 = {
            "name": "AnotherApi",
            "description": "Another API Description"
        }
        self.client.post(endpoint_url, headers={'x-access-token':self.user1_token}, json=data1)
        self.client.post(endpoint_url, headers={'x-access-token':self.user1_token}, json=data2)

        
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.user1_token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 2)
        
        api_names = [api["name"] for api in resp.json]
        self.assertIn("TestApi", api_names)
        self.assertIn("AnotherApi", api_names)
    
    def test_my_apis_isolation_between_users(self):
        """Test that users only see their own APIs"""

        endpoint_url = "/api/v1/create_new_api"
        data1 = {
            "name": "User1Api",
            "description": "User 1 API"
        }
        data2 = {
            "name": "User2Api",
            "description": "User 2 API"
        }
        self.client.post(endpoint_url, headers={'x-access-token':self.user1_token}, json=data1)
        self.client.post(endpoint_url, headers={'x-access-token':self.user2_token}, json=data2)


        resp1 = self.client.get(self.endpoint, headers={'x-access-token': self.user1_token})
        resp2 = self.client.get(self.endpoint, headers={'x-access-token': self.user2_token})
        
        self.assertEqual(len(resp1.json), 1)
        self.assertEqual(resp1.json[0]["name"], "User1Api")
        
        self.assertEqual(len(resp2.json), 1)
        self.assertEqual(resp2.json[0]["name"], "User2Api")


class TestMyApiDetail(TestUserApiEndpoints):
    """Test GET /my_api/<api_id> endpoint"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User.query.filter_by(email=self.user1_data["email"]).first()
            self.api = Api(name="TestApi", description="Test API", user_id=user.id)
            self.db.session.add(self.api)
            self.db.session.commit()
            self.api_id = self.api.id
        
        self.endpoint = f"api/v1/my_api/{self.api_id}"
    
    def test_api_detail_with_wrong_method(self):
        """Test api detail with wrong HTTP methods"""
        resp1 = self.client.post(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_api_detail_without_token(self):
        """Test api detail without authentication"""
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 401)
    
    def test_api_detail_with_non_existent_api(self):
        """Test api detail with non-existent API ID"""
        resp = self.client.get("api/v1/my_api/99999", headers={'x-access-token': self.user1_token})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Api doesn't exist")
    
    def test_api_detail_with_other_users_api(self):
        """Test that user cannot access another user's API"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.user2_token})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Api doesn't exist")
    
    def test_api_detail_success(self):
        """Test successful API detail retrieval"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.user1_token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["id"], self.api_id)
        self.assertEqual(resp.json["name"], "TestApi")
        self.assertEqual(resp.json["description"], "Test API")
        self.assertIn("tables", resp.json)
        self.assertEqual(resp.json["tables"], [])
    
    def test_api_detail_with_tables(self):
        """Test API detail includes associated tables"""
        url = f"/api/v1/my_api/{self.api_id}/create_model"
        data1 = {
            "name": "Users",
            "description": "Users table",
            "tbl_params": [{"name":"_id", "datatype": "integer", "constraints": ["primary_key"]}]

        }
        data2 = {
            "name": "Posts",
            "description": "Posts table",
            "tbl_params": [{"name":"_id", "datatype": "integer", "constraints": ["primary_key"]}, {"name":"author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": f"{self.api.name}.Users"}]

        }
        self.client.post(url, headers={'x-access-token': self.user1_token}, json=data1)
        self.client.post(url, headers={'x-access-token': self.user1_token}, json=data2)
   
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.user1_token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["tables"]), 2)
        
        table_names = [table["name"] for table in resp.json["tables"]]
        self.assertIn("Users", table_names)
        self.assertIn("Posts", table_names)


class TestCreateNewApi(TestUserApiEndpoints):
    """Test POST /create_new_api endpoint"""
    
    def setUp(self):
        super().setUp()
        self.endpoint = "api/v1/create_new_api"
    
    def test_create_api_with_wrong_method(self):
        """Test create API with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_create_api_without_token(self):
        """Test create API without authentication"""
        resp = self.client.post(self.endpoint, json={"name": "TestApi"})
        self.assertEqual(resp.status_code, 401)
    
    def test_create_api_without_name(self):
        """Test create API without name field"""
        resp = self.client.post(
            self.endpoint,
            json={"description": "Test"},
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "name of the api must be provided")
    
    def test_create_api_with_empty_name(self):
        """Test create API with empty name"""
        resp = self.client.post(
            self.endpoint,
            json={"name": ""},
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "name of the api must be provided")
    
    def test_create_api_with_invalid_name(self):
        """Test create API with invalid names (not valid Python identifiers)"""
        invalid_names = ["123api", "api-name", "for", "class", "if", "ab"]
        
        for name in invalid_names:
            resp = self.client.post(
                self.endpoint,
                json={"name": name},
                headers={'x-access-token': self.user1_token}
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn("valid python identifier", resp.json["error"].lower())
    
    def test_create_api_with_duplicate_name(self):
        """Test creating API with name that already exists for user"""
        api_data = {"name": "UniqueApi", "description": "First API"}
        
        # Create first API
        resp1 = self.client.post(
            self.endpoint,
            json=api_data,
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp1.status_code, 200)
        
        # Try to create duplicate
        resp2 = self.client.post(
            self.endpoint,
            json=api_data,
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertEqual(resp2.json["error"], "name with api already exists for this user")
    
    def test_create_api_duplicate_name_different_users(self):
        """Test that different users can create APIs with same name"""
        api_data = {"name": "SharedName", "description": "Test"}
        
        resp1 = self.client.post(
            self.endpoint,
            json=api_data,
            headers={'x-access-token': self.user1_token}
        )
        resp2 = self.client.post(
            self.endpoint,
            json=api_data,
            headers={'x-access-token': self.user2_token}
        )
        
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertNotEqual(resp1.json["id"], resp2.json["id"])
    
    def test_create_api_success(self):
        """Test successful API creation"""
        api_data = {"name": "MyNewApi", "description": "This is a test API"}
        
        resp = self.client.post(
            self.endpoint,
            json=api_data,
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("id", resp.json)
        self.assertEqual(resp.json["name"], "MyNewApi")
        self.assertEqual(resp.json["desc"], "This is a test API")
        
        # Verify in database
        with self.app.app_context():
            api = Api.query.filter_by(name="MyNewApi").first()
            self.assertIsNotNone(api)
            self.assertEqual(api.description, "This is a test API")
    
    def test_create_api_without_description(self):
        """Test creating API without description (should succeed)"""
        resp = self.client.post(
            self.endpoint,
            json={"name": "NoDescApi"},
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "NoDescApi")


class TestUpdateApi(TestUserApiEndpoints):
    """Test PUT /update_api/<id> endpoint"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User.query.filter_by(email=self.user1_data["email"]).first()
            self.api = Api(name="OriginalApi", description="Original description", user_id=user.id)
            self.db.session.add(self.api)
            self.db.session.commit()
            self.api_id = self.api.id
        
        self.endpoint = f"api/v1/update_api/{self.api_id}"
    
    def test_update_api_with_wrong_method(self):
        """Test update API with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.post(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_update_api_without_token(self):
        """Test update API without authentication"""
        resp = self.client.put(self.endpoint, json={"name": "NewName"})
        self.assertEqual(resp.status_code, 401)
    
    def test_update_api_non_existent(self):
        """Test updating non-existent API"""
        resp = self.client.put(
            "api/v1/update_api/99999",
            json={"name": "NewName"},
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "api with id 99999 doesn't exist")
    
    def test_update_api_other_users_api(self):
        """Test user cannot update another user's API"""
        resp = self.client.put(
            self.endpoint,
            json={"name": "HackedName"},
            headers={'x-access-token': self.user2_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], f"api with id {self.api_id} doesn't exist")
    
    def test_update_api_name_only(self):
        """Test updating only the API name"""
        resp = self.client.put(
            self.endpoint,
            json={"name": "UpdatedApi"},
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "UpdatedApi")
        self.assertEqual(resp.json["desc"], "Original description")
        
        with self.app.app_context():
            api = self.db.session.get(Api, self.api_id)
            self.assertEqual(api.name, "UpdatedApi")
    
    def test_update_api_description_only(self):
        """Test updating only the API description"""
        resp = self.client.put(
            self.endpoint,
            json={"description": "Updated description"},
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "OriginalApi")
        self.assertEqual(resp.json["desc"], "Updated description")
    
    def test_update_api_both_fields(self):
        """Test updating both name and description"""
        resp = self.client.put(
            self.endpoint,
            json={"name": "NewApi", "description": "New description"},
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "NewApi")
        self.assertEqual(resp.json["desc"], "New description")
    
    def test_update_api_with_invalid_name(self):
        """Test updating API with invalid name"""
        invalid_names = ["123invalid", "for", "class", "ab"]
        
        for name in invalid_names:
            resp = self.client.put(
                self.endpoint,
                json={"name": name},
                headers={'x-access-token': self.user1_token}
            )
            # Should return success but name shouldn't change
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json["name"], "OriginalApi")


class TestDeleteApi(TestUserApiEndpoints):
    """Test DELETE /delete_api/<id> endpoint"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User.query.filter_by(email=self.user1_data["email"]).first()
            self.api = Api(name="ApiToDelete", description="Will be deleted", user_id=user.id)
            self.db.session.add(self.api)
            self.db.session.commit()
            self.api_id = self.api.id
        
        self.endpoint = f"api/v1/delete_api/{self.api_id}"
    
    def test_delete_api_with_wrong_method(self):
        """Test delete API with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.post(self.endpoint)
        resp3 = self.client.put(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_delete_api_without_token(self):
        """Test delete API without authentication"""
        resp = self.client.delete(self.endpoint)
        self.assertEqual(resp.status_code, 401)
    
    def test_delete_api_non_existent(self):
        """Test deleting non-existent API"""
        resp = self.client.delete(
            "api/v1/delete_api/99999",
            headers={'x-access-token': self.user1_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "api doesn't exist")
    
    def test_delete_api_other_users_api(self):
        """Test user cannot delete another user's API"""
        resp = self.client.delete(
            self.endpoint,
            headers={'x-access-token': self.user2_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "api doesn't exist")
    
    def test_delete_api_success(self):
        """Test successful API deletion"""
        resp = self.client.delete(
            self.endpoint,
            headers={'x-access-token': self.user1_token}
        )
        
        self.assertEqual(resp.status_code, 204)
        
        # Verify deleted from database
        with self.app.app_context():
            api = self.db.session.get(Api, self.api_id)
            self.assertIsNone(api)
    
    def test_delete_api_cascades_to_tables(self):
        """Test that deleting API also deletes associated tables"""
        with self.app.app_context():
            api = self.db.session.get(Api, self.api_id)
            table = Table(name="TestTable", api_id=api.id)
            self.db.session.add(table)
            self.db.session.commit()
            table_id = table.id
        
        resp = self.client.delete(
            self.endpoint,
            headers={'x-access-token': self.user1_token}
        )
    
        
        self.assertEqual(resp.status_code, 204)
        
        with self.app.app_context():
            # Verify API is deleted
            api = self.db.session.get(Api, self.api_id)
            self.assertIsNone(api)
            
            # Verify table is also deleted (cascade)
            table = self.db.session.get(Table, table_id)
            
            self.assertIsNone(table)