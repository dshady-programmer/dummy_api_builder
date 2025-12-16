"""
Full tests for api_table_entry_endpoints.py
Testing CRUD operations on table entries/data
"""
from tests import TestConfig
from models.user import User
from models.api import Api
from models.table import Table
from models.tableparameter import TableParameter
from models.constraints import Constraint
from models.entry import Entry
from models.entrylist import EntryList
from models.reference import ForeignKeyFieldReferenceTable


class TestEntryEndpoints(TestConfig):
    """Base class for entry endpoint tests"""
    
    def setUp(self):
        super().setUp()
        # Create and login user
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        
        # Get user and api_token
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api_token = user.api_token
            
            # Create API and Table
            api = Api(name="BlogApi", description="Blog API", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            
            table = Table(name="User", description="User table", api_id=api.id)
            self.db.session.add(table)
            self.db.session.commit()
            
            # Add table parameters with constraints
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", dataType_length=50, table_id=table.id)
            tb_email = TableParameter(name="email", data_type="string", dataType_length=100, table_id=table.id)
            tb_age = TableParameter(name="age", data_type="integer", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_email, tb_age])
            self.db.session.commit()
            
            # Add constraints
            pk_const = Constraint.query.filter_by(name="primary_key").first()
            if not pk_const:
                pk_const = Constraint(name="primary_key")
            unique_const = Constraint.query.filter_by(name="unique").first()
            if not unique_const:
                unique_const = Constraint(name="unique")
            nullable_const = Constraint.query.filter_by(name="nullable").first()
            if not nullable_const:
                nullable_const = Constraint(name="nullable")
            
            self.db.session.add_all([pk_const, unique_const, nullable_const])
            self.db.session.commit()
            
            tb_id.constraints.extend([pk_const, unique_const])
            tb_email.constraints.append(unique_const)
            tb_age.constraints.append(nullable_const)
            
            self.db.session.commit()
            
            self.api_name = api.name
            self.table_name = table.name


class TestAddListEntry(TestEntryEndpoints):
    """Test POST/GET /<api_token>/my_api/<api_name>/model/<model_name>"""
    
    def setUp(self):
        super().setUp()
        self.endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}"
    
    def test_add_entry_without_api_token(self):
        """Test adding entry without valid api token"""
        resp = self.client.post(
            f"api/v1/invalid_token/my_api/{self.api_name}/model/{self.table_name}",
            json={"entries": {}}
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("invalid token", resp.text.lower())
    
    def test_add_entry_with_non_existent_api(self):
        """Test adding entry to non-existent API"""
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/NonExistentApi/model/{self.table_name}",
            json={"entries": {}}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("does not exists", resp.text)
    
    def test_add_entry_with_non_existent_model(self):
        """Test adding entry to non-existent model"""
        resp = self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/NonExistentModel",
            json={"entries": {}}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("doesn't exist", resp.text)
    
    def test_add_entry_with_invalid_entries_type(self):
        """Test adding entry with invalid entries type"""
        # Test with string instead of dict/list
        resp = self.client.post(self.endpoint, json={"entries": "invalid"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("object or a an array", resp.json["error"])
        
        # Test with number
        resp2 = self.client.post(self.endpoint, json={"entries": 123})
        self.assertEqual(resp2.status_code, 400)
    
    def test_add_entry_without_primary_key(self):
        """Test adding entry without primary key field"""
        entry = {
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("primary key", resp.json["error"])
    
    def test_add_entry_with_missing_required_fields(self):
        """Test adding entry with missing required (non-nullable) fields"""
        entry = {
            "_id": 1,
            "name": "John Doe"
            # Missing email (unique, non-nullable)
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Incomplete field", resp.json["error"])
    
    def test_add_entry_with_extra_fields(self):
        """Test adding entry with non-declared fields"""
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25,
            "extra_field": "should fail"
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Incomplete field or a non declared field", resp.json["error"])
    
    def test_add_entry_with_wrong_datatype(self):
        """Test adding entry with wrong data type"""
        entry = {
            "_id": "not_an_integer",  # Should be integer
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Wrong data type", resp.json["error"])
    
    def test_add_entry_with_duplicate_primary_key(self):
        """Test adding entry with duplicate primary key"""
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        
        # First entry should succeed
        resp1 = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp1.status_code, 200)
        
        # Duplicate should fail
        entry2 = {
            "_id": 1,
            "name": "Jane Doe",
            "email": "jane@test.com",
            "age": 30
        }
        resp2 = self.client.post(self.endpoint, json={"entries": entry2})
        self.assertEqual(resp2.status_code, 400)
        self.assertIn(f"{entry2.get('_id')} already exists in the database. It must be unique", resp2.json["error"])
    
    def test_add_entry_with_duplicate_unique_field(self):
        """Test adding entry with duplicate unique field value"""
        entry1 = {
            "_id": 1,
            "name": "John Doe",
            "email": "duplicate@test.com",
            "age": 25
        }
        
        resp1 = self.client.post(self.endpoint, json={"entries": entry1})
        self.assertEqual(resp1.status_code, 200)
        
        entry2 = {
            "_id": 2,
            "name": "Jane Doe",
            "email": "duplicate@test.com",  # Duplicate email
            "age": 30
        }
        
        resp2 = self.client.post(self.endpoint, json={"entries": entry2})
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("already exists", resp2.json["error"])
    
    def test_add_entry_with_field_length_exceeded(self):
        """Test adding entry with field value exceeding max length"""
        entry = {
            "_id": 1,
            "name": "J" * 100,  # Exceeds max length of 50
            "email": "john@test.com",
            "age": 25
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("max length", resp.json["error"])
    
    def test_add_entry_success_with_nullable_field_missing(self):
        """Test successfully adding entry with nullable field omitted"""
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com"
            # age is nullable, so omitting it should work
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("_id", resp.json)
        self.assertIn("name", resp.json)
        self.assertIn("email", resp.json)
        self.assertIn("age", resp.json)
        self.assertIsNone(resp.json["age"])
    
    def test_add_entry_success_single_object(self):
        """Test successfully adding single entry"""
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        
        resp = self.client.post(self.endpoint, json={"entries": entry})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["_id"], 1)
        self.assertEqual(resp.json["name"], "John Doe")
        self.assertEqual(resp.json["email"], "john@test.com")
        self.assertEqual(resp.json["age"], 25)
        
        # Verify in database
        with self.app.app_context():
            entrylist = EntryList.query.first()
            self.assertIsNotNone(entrylist)
            self.assertEqual(entrylist.primary_key_value, "1")
    
    def test_add_entry_success_multiple_objects(self):
        """Test successfully adding multiple entries"""
        entries = [
            {"_id": 1, "name": "John Doe", "email": "john@test.com", "age": 25},
            {"_id": 2, "name": "Jane Doe", "email": "jane@test.com", "age": 30},
            {"_id": 3, "name": "Bob Smith", "email": "bob@test.com", "age": 35}
        ]
        
        resp = self.client.post(self.endpoint, json={"entries": entries})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["status"], "success")
        self.assertEqual(len(resp.json["results"]), 3)
        
        # Verify in database
        with self.app.app_context():
            entrylists = EntryList.query.all()
            self.assertEqual(len(entrylists), 3)
    
    def test_add_entry_partial_success_with_error(self):
        """Test adding multiple entries where one fails"""
        entries = [
            {"_id": 1, "name": "John Doe", "email": "john@test.com", "age": 25},
            {"_id": 2, "name": "Jane Doe", "email": "john@test.com", "age": 30},  # Duplicate email
        ]
        
        resp = self.client.post(self.endpoint, json={"entries": entries})
        
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["status"], "error")
        self.assertIn("entry", resp.json["error"])
        self.assertIn("successful_entries", resp.json)
        self.assertEqual(len(resp.json["successful_entries"]), 1)


class TestListEntries(TestEntryEndpoints):
    """Test GET /<api_token>/my_api/<api_name>/model/<model_name> (list entries)"""
    
    def setUp(self):
        super().setUp()
        self.endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}"
        
        # Add some test entries
        entries = [
            {"_id": 1, "name": "John Doe", "email": "john@test.com", "age": 25},
            {"_id": 2, "name": "Jane Smith", "email": "jane@test.com", "age": 30},
            {"_id": 3, "name": "Bob Johnson", "email": "bob@test.com", "age": 35},
            {"_id": 4, "name": "Alice Brown", "email": "alice@test.com", "age": 28}
        ]
        
        for entry in entries:
            self.client.post(self.endpoint, json={"entries": entry})
    
    def test_list_entries_without_filters(self):
        """Test listing all entries without filters"""
        resp = self.client.get(self.endpoint)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("data", resp.json)
        self.assertEqual(len(resp.json["data"]), 4)
    
    def test_list_entries_with_exact_match_filter(self):
        """Test listing entries with exact match filter"""
        resp = self.client.get(f"{self.endpoint}?name=John Doe")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertEqual(resp.json["data"][0]["name"], "John Doe")
    
    def test_list_entries_with_integer_exact_match(self):
        """Test filtering by integer field"""
        resp = self.client.get(f"{self.endpoint}?age=30")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertEqual(resp.json["data"][0]["age"], 30)
    
    def test_list_entries_with_lt_filter(self):
        """Test listing entries with less than filter"""
        resp = self.client.get(f"{self.endpoint}?age__lt=30")
        
        self.assertEqual(resp.status_code, 200)
        # Should return entries with age < 30 (25, 28)
        self.assertEqual(len(resp.json["data"]), 2)
        ages = [entry["age"] for entry in resp.json["data"]]
        self.assertTrue(all(age < 30 for age in ages))
    
    def test_list_entries_with_lte_filter(self):
        """Test listing entries with less than or equal filter"""
        resp = self.client.get(f"{self.endpoint}?age__lte=30")
        
        self.assertEqual(resp.status_code, 200)
        # Should return entries with age <= 30
        self.assertEqual(len(resp.json["data"]), 3)
    
    def test_list_entries_with_gt_filter(self):
        """Test listing entries with greater than filter"""
        resp = self.client.get(f"{self.endpoint}?age__gt=30")
        
        self.assertEqual(resp.status_code, 200)
        # Should return entries with age > 30
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertEqual(resp.json["data"][0]["age"], 35)
    
    def test_list_entries_with_gte_filter(self):
        """Test listing entries with greater than or equal filter"""
        resp = self.client.get(f"{self.endpoint}?age__gte=30")
        
        self.assertEqual(resp.status_code, 200)
        # Should return entries with age >= 30
        self.assertEqual(len(resp.json["data"]), 2)
    
    def test_list_entries_with_startswith_filter(self):
        """Test listing entries with startswith filter"""
        resp = self.client.get(f"{self.endpoint}?name__startswith=John")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertTrue(resp.json["data"][0]["name"].startswith("John"))
    
    def test_list_entries_with_endswith_filter(self):
        """Test listing entries with endswith filter"""
        resp = self.client.get(f"{self.endpoint}?name__endswith=Doe")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertTrue(resp.json["data"][0]["name"].endswith("Doe"))
    
    def test_list_entries_with_like_filter(self):
        """Test listing entries with like (contains) filter"""
        resp = self.client.get(f"{self.endpoint}?name__like=o")
        
        self.assertEqual(resp.status_code, 200)
        # Should return John, Bob, Johnson, Brown (all containing 'o')
        self.assertGreater(len(resp.json["data"]), 0)
        for entry in resp.json["data"]:
            self.assertIn("o", entry["name"])
    
    def test_list_entries_with_ilike_filter(self):
        """Test listing entries with case-insensitive like filter"""
        resp = self.client.get(f"{self.endpoint}?name__ilike=JOHN")
        
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.json["data"]), 0)
        for entry in resp.json["data"]:
            self.assertIn("john", entry["name"].lower())
    
    def test_list_entries_with_istartswith_filter(self):
        """Test listing entries with case-insensitive startswith"""
        resp = self.client.get(f"{self.endpoint}?name__istartswith=john")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
    
    def test_list_entries_with_iendswith_filter(self):
        """Test listing entries with case-insensitive endswith"""
        resp = self.client.get(f"{self.endpoint}?name__iendswith=DOE")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
    
    def test_list_entries_with_iexact_filter(self):
        """Test listing entries with case-insensitive exact match"""
        resp = self.client.get(f"{self.endpoint}?name__iexact=JOHN DOE")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 1)
        self.assertEqual(resp.json["data"][0]["name"], "John Doe")
    
    def test_list_entries_with_multiple_filters(self):
        """Test listing entries with multiple filters"""
        resp = self.client.get(f"{self.endpoint}?age__gte=28&name__like=o")
        
        self.assertEqual(resp.status_code, 200)
        # Should return entries matching both conditions
        for entry in resp.json["data"]:
            self.assertGreaterEqual(entry["age"], 28)
            self.assertIn("o", entry["name"])
    
    def test_list_entries_with_invalid_filter_returns_all(self):
        """Test that invalid filter names return all entries"""
        resp = self.client.get(f"{self.endpoint}?invalid_field=value")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json["data"]), 4)


class TestRetrieveEntry(TestEntryEndpoints):
    """Test GET /<api_token>/my_api/<api_name>/model/<model_name>/<model_id>"""
    
    def setUp(self):
        super().setUp()
        # Add a test entry
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}",
            json={"entries": entry}
        )
        
        self.endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/1"
    
    def test_retrieve_entry_without_token(self):
        """Test retrieving entry without valid api token"""
        resp = self.client.get(f"api/v1/invalid_token/my_api/{self.api_name}/model/{self.table_name}/1")
        self.assertEqual(resp.status_code, 401)
    
    def test_retrieve_entry_non_existent_id(self):
        """Test retrieving entry with non-existent primary key"""
        resp = self.client.get(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/999"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("primary key value doesn't match", resp.json["error"])
    
    def test_retrieve_entry_success(self):
        """Test successfully retrieving entry"""
        resp = self.client.get(self.endpoint)
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["_id"], 1)
        self.assertEqual(resp.json["name"], "John Doe")
        self.assertEqual(resp.json["email"], "john@test.com")
        self.assertEqual(resp.json["age"], 25)
        self.assertIn("relationships", resp.json)


class TestUpdateEntry(TestEntryEndpoints):
    """Test PUT /<api_token>/my_api/<api_name>/model/<model_name>/<model_id>"""
    
    def setUp(self):
        super().setUp()
        # Add a test entry
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}",
            json={"entries": entry}
        )
        
        self.endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/1"
    
    def test_update_entry_without_token(self):
        """Test updating entry without valid api token"""
        resp = self.client.put(
            f"api/v1/invalid-token/my_api/{self.api_name}/model/{self.table_name}/1",
            json={"entries": {}}
        )
        self.assertEqual(resp.status_code, 401)
    
    def test_update_entry_non_existent_id(self):
        """Test updating entry with non-existent primary key"""
        resp = self.client.put(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/999",
            json={"entries": {"name": "Updated"}}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("primary key value doesn't match", resp.json["error"])
    
    def test_update_entry_with_invalid_entries_type(self):
        """Test updating entry with invalid entries type"""
        resp = self.client.put(self.endpoint, json={"entries": ["dummy"]})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Entries must be an object", resp.json["error"])
    
    def test_update_entry_single_field(self):
        """Test updating single field"""
        resp = self.client.put(self.endpoint, json={"entries": {"name": "Jane Doe"}})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Jane Doe")
        self.assertEqual(resp.json["email"], "john@test.com")  # Unchanged
        self.assertEqual(resp.json["age"], 25)  # Unchanged
    
    def test_update_entry_multiple_fields(self):
        """Test updating multiple fields"""
        updates = {
            "name": "Jane Smith",
            "email": "jane@test.com",
            "age": 30
        }
        resp = self.client.put(self.endpoint, json={"entries": updates})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Jane Smith")
        self.assertEqual(resp.json["email"], "jane@test.com")
        self.assertEqual(resp.json["age"], 30)
    
    def test_update_entry_with_wrong_datatype(self):
        """Test updating entry with wrong data type"""
        resp = self.client.put(self.endpoint, json={"entries": {"age": "not_an_int"}})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Wrong data type", resp.json["error"])
    
    def test_update_entry_with_non_existent_field(self):
        """Test updating with non-existent field (should be ignored)"""
        resp = self.client.put(
            self.endpoint,
            json={"entries": {"name": "Updated", "fake_field": "value"}}
        )
        # Should succeed, ignoring fake_field
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Updated")
    
    def test_update_entry_violate_unique_constraint(self):
        """Test updating entry to violate unique constraint"""
        # Add another entry
        entry2 = {
            "_id": 2,
            "name": "Jane Doe",
            "email": "jane@test.com",
            "age": 30
        }
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}",
            json={"entries": entry2}
        )
        
        # Try to update first entry with duplicate email
        resp = self.client.put(
            self.endpoint,
            json={"entries": {"email": "jane@test.com"}}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already exists", resp.json["error"])
    
    def test_update_entry_exceed_max_length(self):
        """Test updating entry with value exceeding max length"""
        resp = self.client.put(
            self.endpoint,
            json={"entries": {"name": "x" * 100}}  # Exceeds 50 char limit
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("max length", resp.json["error"])


class TestDeleteEntry(TestEntryEndpoints):
    """Test DELETE /<api_token>/my_api/<api_name>/model/<model_name>/<model_id>"""
    
    def setUp(self):
        super().setUp()
        # Add a test entry
        entry = {
            "_id": 1,
            "name": "John Doe",
            "email": "john@test.com",
            "age": 25
        }
        self.client.post(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}",
            json={"entries": entry}
        )
        
        self.endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/1"
    
    def test_delete_entry_without_token(self):
        """Test deleting entry without valid api token"""
        resp = self.client.delete(f"api/v1/invalid_token/my_api/{self.api_name}/model/{self.table_name}/1")
        self.assertEqual(resp.status_code, 401)
    
    def test_delete_entry_non_existent_id(self):
        """Test deleting entry with non-existent primary key"""
        resp = self.client.delete(
            f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}/999"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("primary key value doesn't match", resp.json["error"])
    
    def test_delete_entry_success(self):
        """Test successfully deleting entry"""
        resp = self.client.delete(self.endpoint)
        
        self.assertEqual(resp.status_code, 204)
        
        # Verify entry is deleted
        with self.app.app_context():
            entrylist = EntryList.query.filter_by(primary_key_value="1").first()
            self.assertIsNone(entrylist)
    
    def test_delete_entry_cascades_to_entries(self):
        """Test that deleting entry also deletes associated Entry records"""
        with self.app.app_context():
            entrylist = EntryList.query.filter_by(primary_key_value="1").first()
            entry_count = len(entrylist.entries)
            self.assertGreater(entry_count, 0)
        
        resp = self.client.delete(self.endpoint)
        self.assertEqual(resp.status_code, 204)
        
        with self.app.app_context():
            # All entries should be deleted
            entries = Entry.query.all()
            self.assertEqual(len(entries), 0)


class TestEntriesWithDefaultConstraint(TestConfig):
    """Test entries with default constraint values"""
    
    def setUp(self):
        super().setUp()
        # Create user and setup
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api_token = user.api_token
            
            api = Api(name="TestApi", description="Test", user_id=user.id)
            self.db.session.add(api)
            self.db.session.commit()
            
            table = Table(name="Product", description="Products", api_id=api.id)
            self.db.session.add(table)
            self.db.session.commit()
            
            # Add fields with default values
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, default_value=None, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            tb_status = TableParameter(name="status", data_type="string", default_value="active", table_id=table.id)
            tb_price = TableParameter(name="price", data_type="integer", default_value="100", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_status, tb_price])
            self.db.session.commit()
            
            # Add constraints
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            default = Constraint.query.filter_by(name="default").first() or Constraint(name="default")
            
            self.db.session.add_all([pk, default])
            self.db.session.commit()
            
            tb_id.constraints.extend([pk, default])
            tb_status.constraints.append(default)
            tb_price.constraints.append(default)
            self.db.session.commit()
            
            self.api_name = api.name
            self.table_name = table.name
    
    def test_add_entry_with_auto_generated_primary_key(self):
        """Test adding entry with auto-generated primary key"""
        endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}"
        entry = {
            "_id": None,  # Should auto-generate
            "name": "Product 1"
        }
        
        resp = self.client.post(endpoint, json={"entries": entry})
        
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.json["_id"])
        self.assertEqual(resp.json["status"], "active")  # Default value
        self.assertEqual(resp.json["price"], 100)  # Default value
    
    def test_add_entry_without_default_fields(self):
        """Test that default fields are populated when omitted"""
        endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}"
        entry = {
            "_id": None,
            "name": "Product 2"
            # status and price omitted - should use defaults
        }
        
        resp = self.client.post(endpoint, json={"entries": entry})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["status"], "active")
        self.assertEqual(resp.json["price"], 100)
    
    def test_add_entry_override_default_values(self):
        """Test overriding default values"""
        endpoint = f"api/v1/{self.api_token}/my_api/{self.api_name}/model/{self.table_name}"
        entry = {
            "_id": None,
            "name": "Product 3",
            "status": "inactive",
            "price": 200
        }
        
        resp = self.client.post(endpoint, json={"entries": entry})
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["status"], "inactive")
        self.assertEqual(resp.json["price"], 200)
        self.assertIsNotNone(resp.json["_id"])