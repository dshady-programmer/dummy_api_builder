"""
Comprehensive tests for foreign key relationships
Testing foreign key constraints, validations, and relationships
"""
from tests import TestConfig
from models.user import User
from models.api import Api
from models.table import Table
from models.tableparameter import TableParameter
from models.constraints import Constraint
from models.entry import Entry
from models.entrylist import EntryList
from models.relationship import Relationship
from models.reference import ForeignKeyFieldReferenceTable


class TestForeignKeySetup(TestConfig):
    """Test foreign key field creation and setup"""
    
    def setUp(self):
        super().setUp()
        # Create user and login
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        self.token = session.json["token"]
        
        # Create API
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api_token = user.api_token
            api = Api(name="BlogApi", description="Blog API", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            self.api_id = api.id
            self.api_name = api.name
        
        # Create parent table (User)
        parent_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key", "unique"]},
            {"name": "username", "datatype": "string", "dt_length": 50},
            {"name": "email", "datatype": "string", "dt_length": 100}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "User", "description": "User model", "tbl_params": parent_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 200)
    
    def test_create_table_with_foreign_key(self):
        """Test creating a table with foreign key reference"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string", "dt_length": 200},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": "BlogApi.User"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "description": "Post model", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        # Verify foreign key reference is set
        with self.app.app_context():
            post_table = Table.query.filter_by(name="Post").first()
            author_param = [p for p in post_table.table_parameters if p.name == "author_id"][0]
            self.assertIsNotNone(author_param.foreign_key_reference_id)
    
    def test_create_fk_with_invalid_reference_format(self):
        """Test creating FK with invalid reference format"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": "InvalidFormat"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
    
    def test_create_fk_with_non_existent_api(self):
        """Test creating FK referencing non-existent API"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": "NonExistentApi.User"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Api name referenced", resp.json["error"])
    
    def test_create_fk_with_non_existent_table(self):
        """Test creating FK referencing non-existent table"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": "BlogApi.NonExistentTable"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Table name referenced", resp.json["error"])
    
    def test_create_fk_with_invalid_datatype(self):
        """Test creating FK with invalid datatype (must be string, text, or integer)"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "author_id", "datatype": "boolean", "constraints": ["foreign_key"], "foreign_key_rf": "BlogApi.User"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Foreign key data type", resp.json["error"])
    
    def test_create_fk_without_reference_field(self):
        """Test creating FK without providing foreign_key_rf"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"]}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Expected a foreign key reference field", resp.json["error"])


class TestForeignKeyEntries(TestConfig):
    """Test creating entries with foreign key constraints"""
    
    def setUp(self):
        super().setUp()
        # Setup user and API
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        self.token = session.json["token"]
        
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api_token = user.api_token
            api = Api(name="BlogApi", description="Blog API", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            self.api_id = api.id
            self.api_name = api.name
        
        # Create User table
        user_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "username", "datatype": "string", "dt_length": 50}
        ]
        self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "User", "tbl_params": user_params},
            headers={'x-access-token': self.token}
        )
        
        # Create Post table with FK
        post_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {"name": "author_id", "datatype": "integer", "constraints": ["foreign_key"], "foreign_key_rf": "BlogApi.User"}
        ]
        self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Post", "tbl_params": post_params},
            headers={'x-access-token': self.token}
        )
        
        # Create a user entry
        user_entry = {"_id": 1, "username": "johndoe"}
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/User",
            json={"entries": user_entry}
        )
    
    def test_add_entry_with_valid_foreign_key(self):
        """Test adding entry with valid foreign key reference"""
        post_entry = {
            "_id": 1,
            "title": "First Post",
            "author_id": 1  # References existing user
        }
        
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Post",
            json={"entries": post_entry}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["author_id"], 1)
        
        # Verify relationship is created
        with self.app.app_context():
            user_table = Table.query.filter_by(name="User").first()
            fk_ref = ForeignKeyFieldReferenceTable.query.filter_by(table_id=user_table.id).first()
            relationships = Relationship.query.filter_by(foreign_key_rel_id=fk_ref.id).all()
            self.assertGreater(len(relationships), 0)
    
    def test_add_entry_with_invalid_foreign_key(self):
        """Test adding entry with non-existent foreign key reference"""
        post_entry = {
            "_id": 1,
            "title": "First Post",
            "author_id": 999  # References non-existent user
        }
        
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Post",
            json={"entries": post_entry}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("doesn't exist on the parent table", resp.json["error"])
    
    def test_add_entry_fk_with_wrong_datatype(self):
        """Test adding entry with FK field having wrong datatype"""
        post_entry = {
            "_id": 1,
            "title": "First Post",
            "author_id": "not_an_integer"
        }
        
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Post",
            json={"entries": post_entry}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Primary key", resp.json["error"])
        self.assertIn("not_an_integer", resp.json["error"])
    
    def test_retrieve_entry_includes_relationships(self):
        """Test that retrieving parent entry includes child relationships"""
        # Add a post
        post_entry = {"_id": 1, "title": "First Post", "author_id": 1}
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Post",
            json={"entries": post_entry}
        )
        
        # Retrieve user
        resp = self.client.get(f"api/v1/{self.api_token}/my_api/{self.api_name}/model/User/1")
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("relationships", resp.json)
        
        # Should have relationship key like "blogapi_posts"
        rel_keys = list(resp.json["relationships"].keys())
        self.assertGreater(len(rel_keys), 0)
        
        # Check if posts are in relationships
        for key in rel_keys:
            if "post" in key.lower():
                posts = resp.json["relationships"][key]
                self.assertEqual(len(posts), 1)
                self.assertEqual(posts[0]["title"], "First Post")
    
    def test_delete_parent_with_existing_children(self):
        """Test deleting parent entry when children exist"""
        # Add a post
        post_entry = {"_id": 1, "title": "First Post", "author_id": 1}
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Post",
            json={"entries": post_entry}
        )
        
        # Try to delete user
        resp = self.client.delete(f"api/v1/{self.api_token}/my_api/{self.api_name}/model/User/1")
        
        # Should succeed and clean up relationships
        self.assertEqual(resp.status_code, 204)
        
        # Verify relationships are cleaned up
        with self.app.app_context():
            post_entrylist = EntryList.query.filter_by(primary_key_value="1").first()
            # Post entry should still exist but relationship should be cleaned
            self.assertIsNotNone(post_entrylist)


class TestForeignKeyWithDefaultValue(TestConfig):
    """Test foreign keys with default values"""
    
    def setUp(self):
        super().setUp()
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        self.token = session.json["token"]
        
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api_token = user.api_token
            api = Api(name="TestApi", description="Test", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            self.api_id = api.id
            self.api_name = api.name
        
       
        # Create parent table
        parent_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "name", "datatype": "string"}
        ]
        self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Category", "tbl_params": parent_params},
            headers={'x-access-token': self.token}
        )
        
        # Create parent entry
        category_entry = {"_id": 1, "name": "General"}
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Category",
            json={"entries": category_entry}
        )

    def test_create_fk_with_default_value(self):
        """Test creating FK field with default value"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "category_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "default"],
                "foreign_key_rf": "TestApi.Category",
                "default_value": "1"
            }
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Article", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
    
    def test_add_entry_uses_fk_default_value(self):
        """Test that omitted FK field uses default value"""
        # Create table with default FK
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "category_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "default"],
                "foreign_key_rf": "TestApi.Category",
                "default_value": "1"
            }
        ]
        resp=self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Article", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        # Add entry without category_id
        article_entry = {
            "_id": 1,
            "title": "Test Article"
            # category_id omitted - should use default
        }
        
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/Article",
            json={"entries": article_entry}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["category_id"], 1)
    
    def test_fk_default_value_invalid_reference(self):
        """Test that invalid FK default value fails at table creation"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "category_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "default"],
                "foreign_key_rf": "TestApi.Category",
                "default_value": "999"  # Non-existent category
            }
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Article", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("does not reference a valid primary key", resp.json["error"])

    def test_fk_default_value_of_none(self):
        """Test fk default with none value"""
        
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "category_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "default"],
                "foreign_key_rf": "TestApi.Category",
                "default_value": None
            }
        ]
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Article", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)

    def test_fk_default_value_with_default_omitted(self):
        """Test fk default constraint while omitting default value"""
        
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "category_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "default"],
                "foreign_key_rf": "TestApi.Category",
            }
        ]
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Article", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)

class TestForeignKeyConstraintsCombinations(TestConfig):
    """Test FK with various constraint combinations"""
    
    def setUp(self):
        super().setUp()
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        self.token = session.json["token"]
        
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            api = Api(name="TestApi", description="Test", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            self.api_id = api.id
        
        # Create parent
        parent_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "name", "datatype": "string"}
        ]
        self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Parent", "tbl_params": parent_params},
            headers={'x-access-token': self.token}
        )
    
    def test_fk_with_primary_key_and_default_fails(self):
        """Test that FK + primary_key + default combination fails"""
        child_params = [
            {
                "name": "_id",
                "datatype": "integer",
                "constraints": ["primary_key", "foreign_key", "default"],
                "foreign_key_rf": "TestApi.Parent",
                "default_value": "1"
            },
            {"name": "title", "datatype": "string"}
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Child", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("can't also have a foreign key constraint", resp.json["error"])
    
    def test_fk_with_nullable(self):
        """Test FK with nullable constraint"""
        child_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "title", "datatype": "string"},
            {
                "name": "parent_id",
                "datatype": "integer",
                "constraints": ["foreign_key", "nullable"],
                "foreign_key_rf": "TestApi.Parent"
            }
        ]
        
        resp = self.client.post(
            f"api/v1/my_api/{self.api_id}/create_model",
            json={"name": "Child", "tbl_params": child_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)