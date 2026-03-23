"""
Full tests for api_table_endpoints.py
Testing CRUD operations on tables/models
"""
from tests import TestConfig
from models.user import User
from models.api import Api
from models.table import Table
from models.tableparameter import TableParameter
from models.entry import Entry
from models.entrylist import EntryList
from models.constraints import Constraint

class TestTableEndpoints(TestConfig):
    """Base class for table endpoint tests"""
    
    def setUp(self):
        super().setUp()
        # Create and login user
        user_data = {"email": "test@test.com", "password": "password123"}
        self.client.post("api/v1/signup", json={**user_data, "confirm_password": "password123"})
        session = self.client.post("api/v1/login", json=user_data)
        self.token = session.json["token"]
        
        # Create API
        with self.app.app_context():
            user = User.query.filter_by(email="test@test.com").first()
            self.api = Api(name="TestApi", description="Test API", user_id=user.id)
            self.db.session.add(self.api)
            self.db.session.commit()
            self.api_id = self.api.id


class TestCreateModel(TestTableEndpoints):
    """Test POST /my_api/<api_id>/create_model endpoint"""
    
    def setUp(self):
        super().setUp()
        self.endpoint = f"api/v1/my_api/{self.api_id}/create_model"
    
    def test_create_model_with_wrong_method(self):
        """Test create model with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_create_model_without_token(self):
        """Test create model without authentication"""
        resp = self.client.post(self.endpoint, json={"name": "User"})
        self.assertEqual(resp.status_code, 401)
    
    def test_create_model_without_name(self):
        """Test create model without name"""
        resp = self.client.post(
            self.endpoint,
            json={"tbl_params": []},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "name of the model is required")
    
    def test_create_model_without_table_parameters(self):
        """Test create model without table parameters"""

        # note: if no table param is passed an empty list is created and fails because table parameters 
        # expect that you pass atleast one field with a primary key constraints.. every create/update attempt to a table
        # always expect a table parameter.
        resp = self.client.post(
            self.endpoint,
            json={"name": "User"},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table must contain atleast one primary key")
    
    def test_create_model_with_empty_table_parameters(self):
        """Test create model with empty table parameters list"""
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": []},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table must contain atleast one primary key")
    
    def test_create_model_with_invalid_name(self):
        """Test create model with invalid name"""
        invalid_names = ["123User", "for", "class", "ab", "user-name"]
        tbl_params = [{"name": "_id", "datatype": "integer", "constraints": ["primary_key"]}]
        
        for name in invalid_names:
            resp = self.client.post(
                self.endpoint,
                json={"name": name, "tbl_params": tbl_params},
                headers={'x-access-token': self.token}
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn("valid python identifier", resp.json["error"].lower())
    
    def test_create_model_with_duplicate_name(self):
        """Test creating model with name that already exists"""
        tbl_params = [{"name": "_id", "datatype": "integer", "constraints": ["primary_key"]}]
        
        # Create first model
        resp1 = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp1.status_code, 200)
        
        # Try duplicate
        resp2 = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertEqual(resp2.json["error"], "Table already exists")
    
    def test_create_model_without_primary_key(self):
        """Test creating model without primary key field"""
        tbl_params = [
            {"name": "name", "datatype": "string"},
            {"name": "age", "datatype": "integer"}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table must contain atleast one primary key")
    
    def test_create_model_with_duplicate_field_names(self):
        """Test creating model with duplicate field names"""
        tbl_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"name": "name", "datatype": "string"},
            {"name": "name", "datatype": "text"}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Duplicate name", resp.json["error"])
    
    def test_create_model_with_invalid_datatype(self):
        """Test creating model with invalid datatype"""
        tbl_params = [
            {"name": "_id", "datatype": "int", "constraints": ["primary_key"]}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "invalid data type")
    
    def test_create_model_with_invalid_field_name(self):
        """Test creating model with invalid field name"""
        tbl_params = [
            {"name": "for", "datatype": "integer", "constraints": ["primary_key"]}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid name", resp.json["error"].lower())
    
    def test_create_model_success_basic(self):
        """Test successful model creation with basic fields"""
        tbl_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key", "unique"]},
            {"name": "name", "datatype": "string", "dt_length": 50},
            {"name": "age", "datatype": "integer", "constraints": ["nullable"]}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "description": "User model", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("id", resp.json)
        self.assertEqual(resp.json["name"], "User")
        self.assertEqual(resp.json["desc"], "User model")
        
        # Verify in database
        with self.app.app_context():
            table = Table.query.filter_by(name="User").first()
            self.assertIsNotNone(table)
            self.assertEqual(len(table.table_parameters), 3)
    
    def test_create_model_with_default_constraint(self):
        """Test creating model with default constraint"""
        tbl_params = [
            {"name": "_id", "datatype": "integer", "constraints": ["primary_key", "default"]},
            {"name": "status", "datatype": "string", "constraints": ["default"], "default_value": "active"}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = Table.query.filter_by(name="User").first()
            status_param = [p for p in table.table_parameters if p.name == "status"][0]
            self.assertEqual(status_param.default_value, "active")
    
    def test_create_model_with_primary_key_wrong_datatype(self):
        """Test creating primary key with invalid datatype"""
        tbl_params = [
            {"name": "_id", "datatype": "boolean", "constraints": ["primary_key"]}
        ]
        
        resp = self.client.post(
            self.endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("primary key data type", resp.json["error"].lower())
    
    def test_create_model_for_non_existent_api(self):
        """Test creating model for API that doesn't exist"""
        endpoint = "api/v1/my_api/99999/create_model"
        tbl_params = [{"name": "_id", "datatype": "integer", "constraints": ["primary_key"]}]
        
        resp = self.client.post(
            endpoint,
            json={"name": "User", "tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "no api of such is associated with the user")


class TestUpdateModel(TestTableEndpoints):
    """Test PUT /my_api/<api_id>/update_model/<model_name> endpoint"""
    
    def setUp(self):
        super().setUp()
        # Create a model first
        with self.app.app_context():
            table = Table(name="User", description="User model", api_id=self.api_id)
            self.db.session.add(table)
            self.db.session.commit()
            
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            self.db.session.add_all([tb_id, tb_name])
            self.db.session.commit()
            
            self.table_id = table.id
            self.tb_id_param_id = tb_id.id
            self.tb_name_param_id = tb_name.id
        
        self.endpoint = f"api/v1/my_api/{self.api_id}/update_model/User"
    
    def test_update_model_with_wrong_method(self):
        """Test update model with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.post(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_update_model_without_token(self):
        """Test update model without authentication"""
        resp = self.client.put(self.endpoint, json={"name": "UpdatedUser"})
        self.assertEqual(resp.status_code, 401)
    
    def test_update_model_non_existent_api(self):
        """Test updating model for non-existent API"""
        endpoint = "api/v1/my_api/99999/update_model/User"
        resp = self.client.put(
            endpoint,
            json={"tbl_params": []},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "no api of such is associated with the user")
    
    def test_update_model_non_existent_table(self):
        """Test updating non-existent model"""
        endpoint = f"api/v1/my_api/{self.api_id}/update_model/NonExistent"
        resp = self.client.put(
            endpoint,
            json={"tbl_params": []},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table doesn't exist")
    
    def test_update_model_always_require_table_params(self):
        """Test updating model would always require to pass a table param.. pass the previous table params if you don't want anything to change"""
        resp = self.client.put(
            self.endpoint,
            json={"name": "UpdatedUser", "tbl_params": []},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
    

    
    def test_update_model_add_new_field(self):
        """Test adding new field to existing model"""
        tbl_params = [
            {"index": self.tb_id_param_id, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_param_id, "name": "name", "datatype": "string"},
            {"name": "email", "datatype": "string", "dt_length": 100}  # New field
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 3)
            email_param = [p for p in table.table_parameters if p.name == "email"][0]
            self.assertEqual(email_param.dataType_length, 100)
    
    def test_update_model_modify_existing_field(self):
        """Test modifying existing field"""
        tbl_params = [
            {"index": self.tb_id_param_id, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_param_id, "name": "username", "datatype": "string"}  # Changed name
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            param = self.db.session.get(TableParameter, self.tb_name_param_id)
            self.assertEqual(param.name, "username")
    
    def test_update_model_delete_field(self):
        """Test deleting field from model"""
        tbl_params = [
            {"index": self.tb_id_param_id, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]}
            # name field omitted - should be deleted
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 1)
            param = self.db.session.get(TableParameter, self.tb_name_param_id)
            self.assertIsNone(param)
    
    def test_update_model_cannot_remove_all_primary_keys(self):
        """Test that removing all primary keys fails"""
        tbl_params = [
            {"index": self.tb_id_param_id, "name": "_id", "datatype": "integer"},  # No primary_key constraint
            {"index": self.tb_name_param_id, "name": "name", "datatype": "string"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table must contain atleast one primary key")
    
    def test_update_model_with_existing_entries_cannot_add_primary_key(self):
        """Test that adding new primary key field fails when entries exist"""
        # Add entry first
        with self.app.app_context():
            entrylist = EntryList(table_id=self.table_id, primary_key_value="1")
            entry_id = Entry(value="1", tableparameter_id=self.tb_id_param_id, entry_list_id=entrylist.id)
            entry_name = Entry(value="John", tableparameter_id=self.tb_name_param_id, entry_list_id=entrylist.id)
            self.db.session.add_all([entrylist, entry_id, entry_name])
            self.db.session.commit()
        
        tbl_params = [
            {"index": self.tb_id_param_id, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_param_id, "name": "name", "datatype": "string"},
            {"name": "email", "datatype": "string", "constraints": ["primary_key"]}  # New PK
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Can't add new primary key field", resp.json["error"])


class TestShowModel(TestTableEndpoints):
    """Test GET /my_api/<api_id>/show_model/<model_name> endpoint"""
    
    def setUp(self):
        super().setUp()
        # Create a model with constraints
        with self.app.app_context():
            from models.constraints import Constraint
            
            table = Table(name="User", description="User model", api_id=self.api_id)
            self.db.session.add(table)
            self.db.session.commit()
            
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_email = TableParameter(name="email", data_type="string", dataType_length=100, table_id=table.id)
            self.db.session.add_all([tb_id, tb_email])
            self.db.session.commit()
            
            pk_constraint = Constraint(name="primary_key")
            unique_constraint = Constraint(name="unique")
        
            tb_id.constraints.append(pk_constraint)
            tb_id.constraints.append(unique_constraint)
            tb_email.constraints.append(unique_constraint)
            self.db.session.commit()
        
        self.endpoint = f"api/v1/my_api/{self.api_id}/show_model/User"
    
    def test_show_model_with_wrong_method(self):
        """Test show model with wrong HTTP methods"""
        resp1 = self.client.post(self.endpoint)
        resp2 = self.client.put(self.endpoint)
        resp3 = self.client.delete(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_show_model_without_token(self):
        """Test show model without authentication"""
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 401)
    
    def test_show_model_non_existent_api(self):
        """Test showing model for non-existent API"""
        endpoint = "api/v1/my_api/99999/show_model/User"
        resp = self.client.get(endpoint, headers={'x-access-token': self.token})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "no api of such is associated with the user")
    
    def test_show_model_non_existent_table(self):
        """Test showing non-existent model"""
        endpoint = f"api/v1/my_api/{self.api_id}/show_model/NonExistent"
        resp = self.client.get(endpoint, headers={'x-access-token': self.token})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["error"], "Table doesn't exist")
    
    def test_show_model_success(self):
        """Test successful model retrieval"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.token})
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("id", resp.json)
        self.assertEqual(resp.json["name"], "User")
        self.assertEqual(resp.json["desc"], "User model")
        self.assertIn("table_params", resp.json)
        self.assertEqual(len(resp.json["table_params"]), 2)
    
    def test_show_model_includes_constraints(self):
        """Test that show model includes field constraints"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.token})
        
        table_params = resp.json["table_params"]
        id_param = [p for p in table_params if p["name"] == "_id"][0]
        email_param = [p for p in table_params if p["name"] == "email"][0]
        
        self.assertIn("primary_key", id_param["constraints"])
        self.assertIn("unique", id_param["constraints"])
        self.assertIn("unique", email_param["constraints"])
    
    def test_show_model_includes_field_details(self):
        """Test that show model includes all field details"""
        resp = self.client.get(self.endpoint, headers={'x-access-token': self.token})
        
        table_params = resp.json["table_params"]
        email_param = [p for p in table_params if p["name"] == "email"][0]
        
        self.assertEqual(email_param["datatype"], "string")
        self.assertEqual(email_param["dt_length"], 100)
        self.assertIn("index", email_param)


class TestDeleteModel(TestTableEndpoints):
    """Test DELETE /my_api/<api_id>/delete_model/<model_name> endpoint"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            table = Table(name="User", description="User model", api_id=self.api_id)
            self.db.session.add(table)
            self.db.session.commit()
            self.table_id = table.id
        
        self.endpoint = f"api/v1/my_api/{self.api_id}/delete_model/User"
    
    def test_delete_model_with_wrong_method(self):
        """Test delete model with wrong HTTP methods"""
        resp1 = self.client.get(self.endpoint)
        resp2 = self.client.post(self.endpoint)
        resp3 = self.client.put(self.endpoint)
        
        for res in [resp1, resp2, resp3]:
            self.assertEqual(res.status_code, 405)
    
    def test_delete_model_without_token(self):
        """Test delete model without authentication"""
        resp = self.client.delete(self.endpoint)
        self.assertEqual(resp.status_code, 401)
    
    def test_delete_model_non_existent_api(self):
        """Test deleting model for non-existent API"""
        endpoint = "api/v1/my_api/99999/delete_model/User"
        resp = self.client.delete(endpoint, headers={'x-access-token': self.token})
        self.assertEqual(resp.status_code, 400)
    
    def test_delete_model_success(self):
        """Test successful model deletion"""
        resp = self.client.delete(self.endpoint, headers={'x-access-token': self.token})
        self.assertEqual(resp.status_code, 204)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertIsNone(table)



class TestUpdateModelTableParameters(TestTableEndpoints):
    """Comprehensive tests for updating table with proper table parameters"""
    
    def setUp(self):
        super().setUp()
        # Create a table with multiple fields
        with self.app.app_context():
            table = Table(name="User", description="User model", api_id=self.api_id)
            self.db.session.add(table)
            self.db.session.commit()
            
            # Create table parameters
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
                self.db.session.add(pk_const)
                self.db.session.commit()
            
            tb_id.constraints.append(pk_const)
            self.db.session.commit()
            
            self.table_id = table.id
            self.tb_id_index = tb_id.id
            self.tb_name_index = tb_name.id
            self.tb_email_index = tb_email.id
            self.tb_age_index = tb_age.id
        
        self.endpoint = f"api/v1/my_api/{self.api_id}/update_model/User"
    
    def test_update_model_keeping_all_fields(self):
        """Test updating model while keeping all existing fields"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50},
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100},
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 4)
    
    def test_update_model_modify_field_name(self):
        """Test updating a field name while keeping structure"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "username", "datatype": "string", "dt_length": 50},  # Changed name
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100},
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertEqual(param.name, "username")
    
    def test_update_model_modify_datatype(self):
        """Test modifying field datatype"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "text"},  # Changed from string to text
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100},
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertEqual(param.data_type.name, "text")
    
    def test_update_model_modify_length(self):
        """Test modifying field max length"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 100},  # Changed length
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100},
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertEqual(param.dataType_length, 100)
    
    def test_update_model_add_new_field(self):
        """Test adding a new field to existing model"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50},
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100},
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"},
            {"name": "phone", "datatype": "string", "dt_length": 20}  # New field (no index)
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 5)
            
            phone_param = [p for p in table.table_parameters if p.name == "phone"][0]
            self.assertEqual(phone_param.dataType_length, 20)
    
    def test_update_model_delete_field(self):
        """Test deleting a field by omitting it from tbl_params"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50},
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100}
            # age field omitted - should be deleted
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 3)
            
            # Verify age field is deleted
            deleted_param = self.db.session.get(TableParameter, self.tb_age_index)
            self.assertIsNone(deleted_param)
    
    def test_update_model_delete_multiple_fields(self):
        """Test deleting multiple fields at once"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50}
            # email and age omitted - should be deleted
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 2)
    
    def test_update_model_add_and_delete_simultaneously(self):
        """Test adding new fields while deleting others"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50},
            # email and age deleted
            {"name": "phone", "datatype": "string", "dt_length": 20},  # New
            {"name": "address", "datatype": "text"}  # New
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 4)
            
            field_names = [p.name for p in table.table_parameters]
            self.assertIn("phone", field_names)
            self.assertIn("address", field_names)
            self.assertNotIn("email", field_names)
            self.assertNotIn("age", field_names)
    
    def test_update_model_modify_and_add_simultaneously(self):
        """Test modifying existing fields while adding new ones"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "full_name", "datatype": "string", "dt_length": 100},  # Modified
            {"index": self.tb_email_index, "name": "email_address", "datatype": "string", "dt_length": 150},  # Modified
            {"index": self.tb_age_index, "name": "age", "datatype": "integer"},
            {"name": "status", "datatype": "string", "constraints": ["default"], "default_value": "active"}  # New
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 5)
            
            # Verify modifications
            name_param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertEqual(name_param.name, "full_name")
            self.assertEqual(name_param.dataType_length, 100)
            
            email_param = self.db.session.get(TableParameter, self.tb_email_index)
            self.assertEqual(email_param.name, "email_address")
            self.assertEqual(email_param.dataType_length, 150)
            
            # Verify new field
            status_param = [p for p in table.table_parameters if p.name == "status"][0]
            self.assertEqual(status_param.default_value, "active")
    
    def test_update_model_without_tbl_params_fails(self):
        """Test that updating without tbl_params fails with proper error"""
        resp = self.client.put(
            self.endpoint,
            json={"name": "UpdatedUser"},  # No tbl_params
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json)
    
    def test_update_model_empty_tbl_params_fails(self):
        """Test that updating with empty tbl_params fails (no primary key)"""
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": []},  # Empty array
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("atleast one primary key", resp.json["error"])
    
    def test_update_model_only_non_pk_fields_fails(self):
        """Test that removing all primary keys fails"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer"},  # No PK constraint
            {"index": self.tb_name_index, "name": "name", "datatype": "string"},
            {"index": self.tb_email_index, "name": "email", "datatype": "string"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("atleast one primary key", resp.json["error"])
    
    def test_update_model_with_invalid_index(self):
        """Test updating with non-existent index creates new field"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": 99999, "name": "fake_field", "datatype": "string"},  # Invalid index - treated as new
            {"index": self.tb_name_index, "name": "name", "datatype": "string"},
            {"index": self.tb_email_index, "name": "email", "datatype": "string"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            # Should have created fake_field as new since index doesn't exist
            field_names = [p.name for p in table.table_parameters]
            self.assertIn("fake_field", field_names)
    
    def test_update_model_change_constraints(self):
        """Test adding/removing constraints from existing fields"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "dt_length": 50},
            {"index": self.tb_email_index, "name": "email", "datatype": "string", "dt_length": 100, "constraints": ["unique"]},  # Add unique
            {"index": self.tb_age_index, "name": "age", "datatype": "integer", "constraints": ["nullable"]}  # Add nullable
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            email_param = self.db.session.get(TableParameter, self.tb_email_index)
            constraint_names = [c.name.value for c in email_param.constraints]
            self.assertIn("unique", constraint_names)
            
            age_param = self.db.session.get(TableParameter, self.tb_age_index)
            constraint_names = [c.name.value for c in age_param.constraints]
            self.assertIn("nullable", constraint_names)


class TestUpdateModelWithExistingData(TestTableEndpoints):
    """Test updating model when entries already exist"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            # Create table
            self.table = Table(name="User", description="User model", api_id=self.api_id)
            self.db.session.add(self.table)
            self.db.session.commit()
            
            # Create table parameters
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=self.table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=self.table.id)
            tb_email = TableParameter(name="email", data_type="string", table_id=self.table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_email])
            self.db.session.commit()
            
            # Add constraints
            pk_const = Constraint.query.filter_by(name="primary_key").first()
            if not pk_const:
                pk_const = Constraint(name="primary_key")
                self.db.session.add(pk_const)
                self.db.session.commit()
            
            tb_id.constraints.append(pk_const)
            self.db.session.commit()
            
            # Create entries
            entrylist = EntryList(table_id=self.table.id, primary_key_value="1")
            entry_id = Entry(value="1", tableparameter_id=tb_id.id, entry_list_id=entrylist.id)
            entry_name = Entry(value="John Doe", tableparameter_id=tb_name.id, entry_list_id=entrylist.id)
            entry_email = Entry(value="john@test.com", tableparameter_id=tb_email.id, entry_list_id=entrylist.id)
            
            self.db.session.add_all([entrylist, entry_id, entry_name, entry_email])
            self.db.session.commit()
            
            self.table_id = self.table.id
            self.tb_id_index = tb_id.id
            self.tb_name_index = tb_name.id
            self.tb_email_index = tb_email.id
        
        self.endpoint = f"api/v1/my_api/{self.api_id}/update_model/User"
    
    def test_update_model_add_nullable_field_with_data(self):
        """Test adding nullable field when entries exist"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string"},
            {"index": self.tb_email_index, "name": "email", "datatype": "string"},
            {"name": "age", "datatype": "integer", "constraints": ["nullable"]}  # New nullable field
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            table = self.db.session.get(Table, self.table_id)
            self.assertEqual(len(table.table_parameters), 4)
            
            # Verify null entry was created for existing row
            age_param = [p for p in table.table_parameters if p.name == "age"][0]
            age_entries = Entry.query.filter_by(tableparameter_id=age_param.id).all()
            self.assertEqual(len(age_entries), 1)
            self.assertIsNone(age_entries[0].value)
    
    def test_update_model_add_field_with_default_value(self):
        """Test adding field with default value when entries exist"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string"},
            {"index": self.tb_email_index, "name": "email", "datatype": "string"},
            {"name": "status", "datatype": "string", "constraints": ["default"], "default_value": "active"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )

        self.assertEqual(resp.status_code, 200)
        with self.app.app_context():
            # Verify default entry was created for existing row
            table = self.db.session.get(Table, self.table_id)
            status_param = [p for p in table.table_parameters if p.name == "status"][0]
            status_entries = Entry.query.filter_by(tableparameter_id=status_param.id).all()
            self.assertEqual(len(status_entries), 1)
            self.assertEqual(status_entries[0].value, "active")
    
    def test_update_model_cannot_add_new_pk_with_data(self):
        """Test that adding new primary key field fails when entries exist"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string"},
            {"index": self.tb_email_index, "name": "email", "datatype": "string"},
            {"name": "uuid", "datatype": "string", "constraints": ["primary_key"]}  # New PK
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Can't add new primary key field", resp.json["error"])
    
    def test_update_model_cannot_remove_pk_with_data(self):
        """Test that removing primary key field fails when entries exist"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer"},  # Removed PK constraint
            {"index": self.tb_name_index, "name": "name", "datatype": "string", "constraints": ["primary_key"]},  # Make name PK instead
            {"index": self.tb_email_index, "name": "email", "datatype": "string"}
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Can't remove an existing primary key field", resp.json["error"])
    
    def test_update_model_delete_field_with_data(self):
        """Test deleting field when entries exist (should cascade)"""
        tbl_params = [
            {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
            {"index": self.tb_name_index, "name": "name", "datatype": "string"}
            # email field omitted
        ]
        
        resp = self.client.put(
            self.endpoint,
            json={"tbl_params": tbl_params},
            headers={'x-access-token': self.token}
        )
        
        self.assertEqual(resp.status_code, 200)
        
        with self.app.app_context():
            # Verify email parameter is deleted
            deleted_param = self.db.session.get(TableParameter, self.tb_email_index)
            self.assertIsNone(deleted_param)
            
            # Verify email entries are also deleted (cascade)
            email_entries = Entry.query.filter_by(tableparameter_id=self.tb_email_index).all()
            self.assertEqual(len(email_entries), 0)