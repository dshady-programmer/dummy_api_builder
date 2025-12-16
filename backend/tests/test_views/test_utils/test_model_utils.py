"""
Tests for api/v1/views/utils/model_utils.py
Testing table parameter creation, update, and validation logic
"""
from tests import TestConfig
from models.user import User
from models.api import Api
from models.table import Table
from models.tableparameter import TableParameter
from models.constraints import Constraint
from models.entry import Entry
from models.entrylist import EntryList
from api.v1.views.utils.model_utils import (
    create_table_parameter,
    update_table_parameter,
    delete_table_parameter,
    parse_and_create_tableparameters,
    parse_and_update_tableparameters
)


class TestCreateTableParameter(TestConfig):
    """Test create_table_parameter function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            self.user = user
            self.table = table
            self.tableparam_names = set()
    
    def test_create_basic_table_parameter(self):
        """Test creating basic table parameter"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "name": "username",
                "datatype": "string",
                "dt_length": 50,
                "constraints": []
            }
            
            is_pk = create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertFalse(is_pk)
            self.assertIn("username", self.tableparam_names)
            
            tb_param = TableParameter.query.filter_by(name="username").first()
            self.assertIsNotNone(tb_param)
            self.assertEqual(tb_param.dataType_length, 50)
    
    def test_create_primary_key_parameter(self):
        """Test creating primary key parameter"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "name": "_id",
                "datatype": "integer",
                "constraints": ["primary_key"]
            }
            
            is_pk = create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertTrue(is_pk)
            
            tb_param = TableParameter.query.filter_by(name="_id").first()
            self.assertTrue(tb_param.primary_key)
            
            # Should have unique constraint added automatically
            
            constraint_names = [c.name for c in tb_param.constraints]
            self.assertIn("unique", constraint_names)
    
    def test_create_parameter_with_default_value(self):
        """Test creating parameter with default value"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "name": "status",
                "datatype": "string",
                "constraints": ["default"],
                "default_value": "active"
            }
            
            create_table_parameter(param, table, self.tableparam_names, user, False)
            
            tb_param = TableParameter.query.filter_by(name="status").first()
            self.assertEqual(tb_param.default_value, "active")
    
    def test_create_parameter_duplicate_name(self):
        """Test creating parameter with duplicate name"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            self.tableparam_names.add("username")
            
            param = {
                "name": "username",
                "datatype": "string",
                "constraints": []
            }
            
            with self.assertRaises(Exception) as context:
                create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertIn("Duplicate name", str(context.exception.args[0]["error"]))
    
    def test_create_parameter_invalid_datatype(self):
        """Test creating parameter with invalid datatype"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "name": "field",
                "datatype": "invalid_type",
                "constraints": []
            }
            
            with self.assertRaises(Exception) as context:
                create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertIn("invalid data type", str(context.exception.args[0]["error"]))
    
    def test_create_parameter_invalid_name(self):
        """Test creating parameter with invalid name"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "name": "for",  # Python keyword
                "datatype": "string",
                "constraints": []
            }
            
            with self.assertRaises(Exception) as context:
                create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertIn("invalid name", str(context.exception.args[0]["error"]))
    
    def test_create_parameter_without_name(self):
        """Test creating parameter without name"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            param = {
                "datatype": "string",
                "constraints": []
            }
            
            with self.assertRaises(Exception) as context:
                create_table_parameter(param, table, self.tableparam_names, user, False)
            
            self.assertIn("name can't be empty", str(context.exception.args[0]["error"]))


class TestUpdateTableParameter(TestConfig):
    """Test update_table_parameter function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create existing parameter
            tb_param = TableParameter(name="username", data_type="string", table_id=table.id)
            self.db.session.add(tb_param)
            self.db.session.commit()
            
            self.user = user
            self.table = table
            self.tb_param = tb_param
            self.tableparam_names = {"username"}
    
    def test_update_parameter_name(self):
        """Test updating parameter name"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            tb_param = TableParameter.query.first()
            
            param = {
                "name": "user_name",
                "datatype": "string",
                "constraints": []
            }
            
            update_table_parameter(param, table, tb_param, self.tableparam_names, user, False)
            
            self.assertEqual(tb_param.name, "user_name")
            self.assertIn("user_name", self.tableparam_names)
    
    def test_update_parameter_datatype(self):
        """Test updating parameter datatype"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            tb_param = TableParameter.query.first()
            
            param = {
                "datatype": "text",
                "constraints": []
            }
            
            update_table_parameter(param, table, tb_param, self.tableparam_names, user, False)
            
            self.assertEqual(tb_param.data_type, "text")
    
    def test_update_parameter_add_length(self):
        """Test updating parameter to add length"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            tb_param = TableParameter.query.first()
            
            param = {
                "dt_length": 100,
                "datatype": "string",
                "constraints": []
            }
            
            update_table_parameter(param, table, tb_param, self.tableparam_names, user, False)
            
            self.assertEqual(tb_param.dataType_length, 100)
    
    def test_update_parameter_remove_length(self):
        """Test updating parameter to remove length"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            tb_param = TableParameter.query.first()
            tb_param.dataType_length = 50
            self.db.session.commit()
            
            param = {
                "datatype": "integer",  # integer doesn't use length
                "constraints": []
            }
            
            update_table_parameter(param, table, tb_param, self.tableparam_names, user, False)
            
            self.assertIsNone(tb_param.dataType_length)


class TestDeleteTableParameter(TestConfig):
    """Test delete_table_parameter function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create parameters
            tb_param1 = TableParameter(name="field1", data_type="string", table_id=table.id)
            tb_param2 = TableParameter(name="field2", data_type="integer", table_id=table.id)
            self.db.session.add_all([tb_param1, tb_param2])
            self.db.session.commit()
            
            self.param1_id = tb_param1.id
            self.param2_id = tb_param2.id
    
    def test_delete_table_parameters(self):
        """Test deleting multiple table parameters"""
        with self.app.app_context():
            params_to_delete = {
                self.param1_id: self.db.session.get(TableParameter, self.param1_id),
                self.param2_id: self.db.session.get(TableParameter, self.param2_id)
            }
            
            delete_table_parameter(params_to_delete)
            self.db.session.commit()
            
            # Verify deletion
            param1 = self.db.session.get(TableParameter, self.param1_id)
            param2 = self.db.session.get(TableParameter, self.param2_id)
            
            self.assertIsNone(param1)
            self.assertIsNone(param2)
    
    def test_delete_parameter_with_entries(self):
        """Test deleting parameter cascades to entries"""
        with self.app.app_context():
            table = Table.query.first()
            tb_param = self.db.session.get(TableParameter, self.param1_id)
            
            # Create entry
            entrylist = EntryList(table_id=table.id)
            entry = Entry(value="test", tableparameter_id=tb_param.id, entry_list_id=entrylist.id)
            self.db.session.add_all([entrylist, entry])
            self.db.session.commit()
            entry_id = entry.id
            
            # Delete parameter
            params_to_delete = {self.param1_id: tb_param}
            delete_table_parameter(params_to_delete)
            self.db.session.commit()
            
            # Verify entry is also deleted
            deleted_entry = self.db.session.get(Entry, entry_id)
            self.assertIsNone(deleted_entry)


class TestParseAndCreateTableParameters(TestConfig):
    """Test parse_and_create_tableparameters function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            self.user = user
            self.table = table
    
    def test_parse_create_valid_parameters(self):
        """Test parsing and creating valid parameters"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
                {"name": "username", "datatype": "string", "dt_length": 50},
                {"name": "age", "datatype": "integer", "constraints": ["nullable"]}
            ]
            
            result = parse_and_create_tableparameters(table_parameters, table, user)
            
            self.assertNotIn("error", result)
            self.assertEqual(len(table.table_parameters), 3)
    
    def test_parse_create_without_primary_key(self):
        """Test parsing parameters without primary key fails"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"name": "username", "datatype": "string"},
                {"name": "age", "datatype": "integer"}
            ]
            
            result = parse_and_create_tableparameters(table_parameters, table, user)
            
            self.assertIn("error", result)
            self.assertIn("atleast one primary key", result["error"])
    
    def test_parse_create_with_duplicate_names(self):
        """Test parsing parameters with duplicate names fails"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
                {"name": "username", "datatype": "string"},
                {"name": "username", "datatype": "text"}  # Duplicate
            ]
            
            result = parse_and_create_tableparameters(table_parameters, table, user)
            
            self.assertIn("error", result)
            self.assertIn("Duplicate name", result["error"])


class TestParseAndUpdateTableParameters(TestConfig):
    """Test parse_and_update_tableparameters function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create existing parameters
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="username", data_type="string", table_id=table.id)
            self.db.session.add_all([tb_id, tb_name])
            self.db.session.commit()
            
            # Add constraints
            pk_const = Constraint.query.filter_by(name="primary_key").first()
            if not pk_const:
                pk_const = Constraint(name="primary_key")
                self.db.session.add(pk_const)
                self.db.session.commit()
            
            tb_id.constraints.append(pk_const)
            self.db.session.commit()
            
            self.user = user
            self.table = table
            self.tb_id_index = tb_id.id
            self.tb_name_index = tb_name.id
    
    def test_parse_update_modify_existing(self):
        """Test updating existing parameters"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
                {"index": self.tb_name_index, "name": "user_name", "datatype": "string"}  # Changed name
            ]
            
            result = parse_and_update_tableparameters(table_parameters, table, user, False)
            
            self.assertNotIn("error", result)
            
            tb_param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertEqual(tb_param.name, "user_name")
    
    def test_parse_update_add_new_field(self):
        """Test adding new field during update"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
                {"index": self.tb_name_index, "name": "username", "datatype": "string"},
                {"name": "email", "datatype": "string", "dt_length": 100}  # New field
            ]
            
            result = parse_and_update_tableparameters(table_parameters, table, user, False)
            
            self.assertNotIn("error", result)
            self.assertEqual(len(table.table_parameters), 3)
            
            email_param = [p for p in table.table_parameters if p.name == "email"][0]
            self.assertEqual(email_param.dataType_length, 100)
    
    def test_parse_update_delete_field(self):
        """Test deleting field during update"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]}
                # username omitted - should be deleted
            ]
            
            result = parse_and_update_tableparameters(table_parameters, table, user, False)
            
            self.assertNotIn("error", result)
            self.assertEqual(len(table.table_parameters), 1)
            
            deleted_param = self.db.session.get(TableParameter, self.tb_name_index)
            self.assertIsNone(deleted_param)
    
    def test_parse_update_remove_all_pks_fails(self):
        """Test that removing all primary keys fails"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            table_parameters = [
                {"index": self.tb_id_index, "name": "_id", "datatype": "integer"},  # No PK constraint
                {"index": self.tb_name_index, "name": "username", "datatype": "string"}
            ]
            
            result = parse_and_update_tableparameters(table_parameters, table, user, False)
            
            self.assertIn("error", result)
            self.assertIn("atleast one primary key", result["error"])
    
    def test_parse_update_with_entries_cannot_add_pk(self):
        """Test that adding new PK field fails when entries exist"""
        with self.app.app_context():
            table = Table.query.first()
            user = User.query.first()
            
            # Add entry
            entrylist = EntryList(table_id=table.id)
            tb_id = self.db.session.get(TableParameter, self.tb_id_index)
            entry = Entry(value="1", tableparameter_id=tb_id.id, entry_list_id=entrylist.id)
            self.db.session.add_all([entrylist, entry])
            self.db.session.commit()
            
            table_parameters = [
                {"index": self.tb_id_index, "name": "_id", "datatype": "integer", "constraints": ["primary_key"]},
                {"index": self.tb_name_index, "name": "username", "datatype": "string"},
                {"name": "email", "datatype": "string", "constraints": ["primary_key"]}  # New PK
            ]
            
            result = parse_and_update_tableparameters(table_parameters, table, user, True)
            
            self.assertIn("error", result)
            self.assertIn("Can't add new primary key field", result["error"])


