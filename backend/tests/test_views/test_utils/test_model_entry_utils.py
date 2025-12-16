"""
Tests for api/v1/views/utils/model_entry_utils.py
Testing entry creation, update, listing, and validation logic
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
from api.v1.views.utils.model_entry_utils import (
    create_entry,
    update_entry,
    list_entries,
    create_null_value_entries,
    create_default_value_entries,
    update_default_value_entries,
    datetime_repr
)


class TestDatetimeRepr(TestConfig):
    """Test datetime_repr function"""
    
    def test_datetime_repr_for_datetime(self):
        """Test datetime representation for datetime type"""
        result = datetime_repr("2024-12-15T10:30:00", "datetime")
        self.assertIsInstance(result, str)
        self.assertIn("2024-12-15", result)
        self.assertIn("10:30:00", result)
    
    def test_datetime_repr_for_date(self):
        """Test datetime representation for date type"""
        result = datetime_repr("2024-12-15", "date")
        self.assertEqual(result, "2024-12-15")
    
    def test_datetime_repr_for_non_datetime(self):
        """Test datetime representation for non-datetime types"""
        result = datetime_repr("some_value", "string")
        self.assertEqual(result, "some_value")
        
        result2 = datetime_repr("123", "integer")
        self.assertEqual(result2, "123")


class TestCreateEntry(TestConfig):
    """Test create_entry function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            # Setup user, api, table
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="User", description="User table", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table parameters
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", dataType_length=50, table_id=table.id)
            tb_email = TableParameter(name="email", data_type="string", dataType_length=100, table_id=table.id)
            tb_age = TableParameter(name="age", data_type="integer", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_email, tb_age])
            self.db.session.commit()
            
            # Add constraints
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            unique = Constraint.query.filter_by(name="unique").first() or Constraint(name="unique")
            nullable = Constraint.query.filter_by(name="nullable").first() or Constraint(name="nullable")
            
            self.db.session.add_all([pk, unique, nullable])
            self.db.session.commit()
            
            tb_id.constraints.extend([pk, unique])
            tb_email.constraints.append(unique)
            tb_age.constraints.append(nullable)
            
            self.db.session.commit()
            
            self.user = user
            self.table = table
    
    def test_create_entry_success(self):
        """Test successful entry creation"""
        with self.app.app_context():
            table = Table.query.first()
            
            entry = {
                "_id": 1,
                "name": "John Doe",
                "email": "john@test.com",
                "age": 25
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            self.assertEqual(result["_id"], 1)
            self.assertEqual(result["name"], "John Doe")
            self.assertEqual(result["email"], "john@test.com")
            self.assertEqual(result["age"], 25)
            
            # Verify in database
            entrylist = EntryList.query.first()
            self.assertIsNotNone(entrylist)
            self.assertEqual(entrylist.primary_key_value, "1")
            self.assertEqual(len(entrylist.entries), 4)
    
    def test_create_entry_with_nullable_field_omitted(self):
        """Test creating entry with nullable field omitted"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "John Doe",
                "email": "john@test.com"
                # age omitted (nullable)
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            self.assertIsNone(result["age"])
    
    def test_create_entry_invalid_type(self):
        """Test creating entry with invalid type (not dict)"""
        with self.app.app_context():
            table = Table.query.first()

            
            result = create_entry(table, "not a dict")
            
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Entry must be a dictionary")
    
    def test_create_entry_missing_primary_key(self):
        """Test creating entry without primary key"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "name": "John Doe",
                "email": "john@test.com",
                "age": 25
                # _id missing
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("No primary key", result["error"])
    
    def test_create_entry_missing_required_field(self):
        """Test creating entry missing required non-nullable field"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "John Doe"
                # email missing (required, unique)
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)

    def test_create_entry_missing_required_field_with_same_number_of_required_fields(self):
        """Test creating entry missing required non-nullable field passing data with the same number of required table parameter"""
        
        """
        For this field there are 3 non-nullable fields.. so we'll pass in 3 fields... which excludes email a non-nullable fields and includes age a nullable field
        """
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "John Doe",
                "age": 26,
                # email missing (required, unique)
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertEqual(result["error"], "email is a non-nullable field (can't be empty)")
    
    def test_create_entry_with_extra_field(self):
        """Test creating entry with non-existent field"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "John Doe",
                "email": "john@test.com",
                "age": 25,
                "extra_field": "should fail"
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("non declared field", result["error"])
    
    def test_create_entry_duplicate_primary_key(self):
        """Test creating entry with duplicate primary key"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry1 = {
                "_id": 1,
                "name": "John Doe",
                "email": "john@test.com",
                "age": 25
            }
            
            # Create first entry
            result1 = create_entry(table, entry1)
            self.assertNotIn("error", result1)
            
            # Try duplicate
            entry2 = {
                "_id": 1,
                "name": "Jane Doe",
                "email": "jane@test.com",
                "age": 30
            }
            
            result2 = create_entry(table, entry2)
            
            self.assertIn("error", result2)
            self.assertIn("1 already exists in the database", result2["error"])
    
    def test_create_entry_duplicate_unique_field(self):
        """Test creating entry with duplicate unique field"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry1 = {
                "_id": 1,
                "name": "John Doe",
                "email": "duplicate@test.com",
                "age": 25
            }
            
            result1 = create_entry(table, entry1)
            self.assertNotIn("error", result1)
            
            entry2 = {
                "_id": 2,
                "name": "Jane Doe",
                "email": "duplicate@test.com",  # Duplicate email
                "age": 30
            }
            
            result2 = create_entry(table, entry2)
            
            self.assertIn("error", result2)
            self.assertIn("already exists", result2["error"])
    
    def test_create_entry_wrong_datatype(self):
        """Test creating entry with wrong datatype"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": "not_an_integer",
                "name": "John Doe",
                "email": "john@test.com",
                "age": 25
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("Wrong data type", result["error"])
    
    def test_create_entry_exceeds_max_length(self):
        """Test creating entry with value exceeding max length"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "x" * 100,  # Exceeds 50 char limit
                "email": "john@test.com",
                "age": 25
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("max length", result["error"])
    
    def test_create_entry_with_composite_primary_key(self):
        """Test creating entry with multiple primary key fields"""
        with self.app.app_context():
            # Create table with composite PK
            table = Table(name="CompositeTable", description="Test", api_id=1)
            self.db.session.add(table)
            self.db.session.commit()
            
            tb_id1 = TableParameter(name="id1", data_type="integer", primary_key=True, table_id=table.id)
            tb_id2 = TableParameter(name="id2", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            
            self.db.session.add_all([tb_id1, tb_id2, tb_name])
            self.db.session.commit()
            
            pk = Constraint.query.filter_by(name="primary_key").first()
            unique = Constraint.query.filter_by(name="unique").first()
            
            tb_id1.constraints.extend([pk, unique])
            tb_id2.constraints.extend([pk, unique])
            self.db.session.commit()
            

            
            entry = {
                "id1": 1,
                "id2": 2,
                "name": "Test"
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            
            # Verify composite PK value
            entrylist = EntryList.query.filter_by(table_id=table.id).first()
            self.assertEqual(entrylist.primary_key_value, "12")  # Concatenated


class TestUpdateEntry(TestConfig):
    """Test update_entry function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            # Setup user, api, table
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="User", description="User table", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table parameters
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            tb_email = TableParameter(name="email", data_type="string", table_id=table.id)
            tb_age = TableParameter(name="age", data_type="integer", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_email, tb_age])
            self.db.session.commit()
            
            # Add constraints
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            unique = Constraint.query.filter_by(name="unique").first() or Constraint(name="unique")
            
            self.db.session.add_all([pk, unique])
            self.db.session.commit()
            
            tb_id.constraints.extend([pk, unique])
            tb_email.constraints.append(unique)
            
            self.db.session.commit()
            
            # Create an entry to update
            entrylist = EntryList(table_id=table.id, primary_key_value="1")
            entry_id = Entry(value="1", tableparameter_id=tb_id.id)
            entry_name = Entry(value="John Doe", tableparameter_id=tb_name.id)
            entry_email = Entry(value="john@test.com", tableparameter_id=tb_email.id)
            entry_age = Entry(value="25", tableparameter_id=tb_age.id)

            entrylist.entries.extend([entry_id, entry_name, entry_email, entry_age])
            
            self.db.session.add(entrylist)
            self.db.session.commit()
            
            self.user = user
            self.table = table
            self.entrylist = entrylist
    
    def test_update_entry_single_field(self):
        """Test updating single field"""
        with self.app.app_context():
            table = Table.query.first()
            entrylist = EntryList.query.first()
            update_data = {"name": "Jane Doe"}
            
            result = update_entry(update_data, table, entrylist)
            self.assertNotIn("error", result)
            self.assertEqual(result["name"], "Jane Doe")
            self.assertEqual(result["email"], "john@test.com")  # Unchanged
    
    def test_update_entry_multiple_fields(self):
        """Test updating multiple fields"""
        with self.app.app_context():
            table = Table.query.first()
            entrylist = EntryList.query.first()
            
            update_data = {
                "name": "Jane Smith",
                "email": "jane@test.com",
                "age": 30
            }
            
            result = update_entry(update_data, table, entrylist)
            
            self.assertNotIn("error", result)
            self.assertEqual(result["name"], "Jane Smith")
            self.assertEqual(result["email"], "jane@test.com")
            self.assertEqual(result["age"], 30)
    
    def test_update_entry_invalid_type(self):
        """Test updating with invalid type (not dict)"""
        with self.app.app_context():
            table = Table.query.first()
            entrylist = EntryList.query.first()
            
            result = update_entry("not a dict", table, entrylist)
            
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Entry must be a dictionary")
    
    def test_update_entry_with_non_existent_field(self):
        """Test updating with non-existent field (should be ignored)"""
        with self.app.app_context():
            table = Table.query.first()
            entrylist = EntryList.query.first()
            
            update_data = {
                "name": "Updated Name",
                "fake_field": "should be ignored"
            }
            
            result = update_entry(update_data, table, entrylist)
            
            # Should succeed, ignoring fake_field
            self.assertNotIn("error", result)
            self.assertEqual(result["name"], "Updated Name")
    
    def test_update_entry_violate_unique_constraint(self):
        """Test updating to violate unique constraint"""
        with self.app.app_context():
            table = Table.query.first()

            
            # Create second entry
            tb_params = {p.name: p for p in table.table_parameters}
            entrylist2 = EntryList(table_id=table.id, primary_key_value="2")
            entry2_id = Entry(value="2", tableparameter_id=tb_params["_id"].id, entry_list_id=entrylist2.id)
            entry2_email = Entry(value="jane@test.com", tableparameter_id=tb_params["email"].id, entry_list_id=entrylist2.id)
            
            self.db.session.add_all([entrylist2, entry2_id, entry2_email])
            self.db.session.commit()
            
            # Try to update first entry with duplicate email
            entrylist1 = EntryList.query.filter_by(primary_key_value="1").first()
            update_data = {"email": "jane@test.com"}
            
            result = update_entry(update_data, table, entrylist1)
            
            self.assertIn("error", result)
            self.assertIn("already exists", result["error"])
    
    def test_update_entry_wrong_datatype(self):
        """Test updating with wrong datatype"""
        with self.app.app_context():
            table = Table.query.first()
            entrylist = EntryList.query.first()
            
            update_data = {"age": "not_an_integer"}
            
            result = update_entry(update_data, table, entrylist)
            
            self.assertIn("error", result)
            self.assertIn("Wrong data type", result["error"])


class TestListEntries(TestConfig):
    """Test list_entries function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            # Setup user, api, table
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="User", description="User table", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table parameters
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            tb_age = TableParameter(name="age", data_type="integer", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_age])
            self.db.session.commit()
            
            # Create sample entries
            entries_data = [
                {"_id": "1", "name": "John Doe", "age": "25"},
                {"_id": "2", "name": "Jane Smith", "age": "30"},
                {"_id": "3", "name": "Bob Johnson", "age": "35"},
                {"_id": "4", "name": "Alice Brown", "age": "28"}
            ]
            
            for entry_data in entries_data:
                entrylist = EntryList(table_id=table.id, primary_key_value=entry_data["_id"])
                self.db.session.add(entrylist)
                self.db.session.commit()
                
                for param_name, value in entry_data.items():
                    tb_param = [p for p in table.table_parameters if p.name == param_name][0]
                    entry = Entry(value=value, tableparameter_id=tb_param.id, entry_list_id=entrylist.id)
                    self.db.session.add(entry)
                
                self.db.session.commit()
            
            self.table = table
    
    def test_list_entries_without_filters(self):
        """Test listing all entries without filters"""
        with self.app.app_context():
            table = Table.query.first()
            
            result = list_entries({}, table)
            
            self.assertIn("data", result)
            self.assertEqual(len(result["data"]), 4)
    
    def test_list_entries_with_exact_match(self):
        """Test listing entries with exact match filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"name": "John Doe"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            self.assertEqual(len(result["data"]), 1)
            self.assertEqual(result["data"][0]["name"], "John Doe")
    
    def test_list_entries_with_integer_filter(self):
        """Test listing entries with integer filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"age": "30"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            self.assertEqual(len(result["data"]), 1)
            self.assertEqual(result["data"][0]["age"], 30)
    
    def test_list_entries_with_lt_filter(self):
        """Test listing entries with less than filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"age__lt": "30"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            # Should return entries with age < 30 (25, 28)
            self.assertEqual(len(result["data"]), 2)
    
    def test_list_entries_with_gte_filter(self):
        """Test listing entries with greater than or equal filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"age__gte": "30"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            # Should return entries with age >= 30
            self.assertEqual(len(result["data"]), 2)
    
    def test_list_entries_with_like_filter(self):
        """Test listing entries with like filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"name__like": "John"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            # Should return entries with "John" in name
            self.assertGreater(len(result["data"]), 0)
    
    def test_list_entries_with_ilike_filter(self):
        """Test listing entries with case-insensitive like filter"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"name__ilike": "JOHN"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            self.assertGreater(len(result["data"]), 0)
    
    def test_list_entries_with_multiple_filters(self):
        """Test listing entries with multiple filters"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"age__gte": "28", "name__like": "o"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            # Should return entries matching both conditions
            for entry in result["data"]:
                self.assertGreaterEqual(entry["age"], 28)
                self.assertIn("o", entry["name"].lower())
    
    def test_list_entries_with_invalid_filter(self):
        """Test that invalid filter returns all entries"""
        with self.app.app_context():
            table = Table.query.first()
            args = {"invalid_field": "value"}
            
            result = list_entries(args, table)
            
            self.assertIn("data", result)
            self.assertEqual(len(result["data"]), 4)


class TestCreateNullValueEntries(TestConfig):
    """Test create_null_value_entries function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create existing entries
            tb_id = TableParameter(name="_id", data_type="integer", table_id=table.id)
            self.db.session.add(tb_id)
            self.db.session.commit()
            
            entrylist1 = EntryList(table_id=table.id, primary_key_value="1")
            entrylist2 = EntryList(table_id=table.id, primary_key_value="2")
            entry1 = Entry(value="1", tableparameter_id=tb_id.id, entry_list_id=entrylist1.id)
            entry2 = Entry(value="2", tableparameter_id=tb_id.id, entry_list_id=entrylist2.id)
            
            self.db.session.add_all([entrylist1, entrylist2, entry1, entry2])
            self.db.session.commit()
            
            self.table = table
            self.tb_id = tb_id
    
    def test_create_null_value_entries(self):
        """Test creating null value entries for all existing rows"""
        with self.app.app_context():
            table = Table.query.first()
            
            # Add new nullable field
            tb_new = TableParameter(name="new_field", data_type="string", table_id=table.id)
            self.db.session.add(tb_new)
            self.db.session.commit()
            
            # Create null entries
            create_null_value_entries(table, tb_new)
            self.db.session.commit()
            
            # Verify null entries created for both existing rows
            entries = Entry.query.filter_by(tableparameter_id=tb_new.id).all()
            self.assertEqual(len(entries), 2)
            
            for entry in entries:
                self.assertIsNone(entry.value)


class TestCreateDefaultValueEntries(TestConfig):
    """Test create_default_value_entries function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create existing entries
            tb_id = TableParameter(name="_id", data_type="integer", table_id=table.id)
            self.db.session.add(tb_id)
            self.db.session.commit()
            
            entrylist1 = EntryList(table_id=table.id, primary_key_value="1")
            entrylist2 = EntryList(table_id=table.id, primary_key_value="2")
            entry1 = Entry(value="1", tableparameter_id=tb_id.id, entry_list_id=entrylist1.id)
            entry2 = Entry(value="2", tableparameter_id=tb_id.id, entry_list_id=entrylist2.id)
            
            self.db.session.add_all([entrylist1, entrylist2, entry1, entry2])
            self.db.session.commit()
            
            self.table = table
    
    def test_create_default_value_entries(self):
        """Test creating default value entries for all existing rows"""
        with self.app.app_context():
            table = Table.query.first()
            
            # Add new field with default value
            tb_status = TableParameter(name="status", data_type="string", default_value="active", table_id=table.id)
            self.db.session.add(tb_status)
            self.db.session.commit()
            
            # Create default entries
            create_default_value_entries(table, tb_status, "active")
            self.db.session.commit()
            
            # Verify default entries created
            entries = Entry.query.filter_by(tableparameter_id=tb_status.id).all()
            self.assertEqual(len(entries), 2)
            
            for entry in entries:
                self.assertEqual(entry.value, "active")


class TestUpdateDefaultValueEntries(TestConfig):
    """Test update_default_value_entries function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create field with default value
            tb_status = TableParameter(name="status", data_type="string", default_value="active", table_id=table.id)
            self.db.session.add(tb_status)
            self.db.session.commit()
            
            # Create entries - some with null values
            entrylist1 = EntryList(table_id=table.id, primary_key_value="1")
            entrylist2 = EntryList(table_id=table.id, primary_key_value="2")
            entrylist3 = EntryList(table_id=table.id, primary_key_value="3")
            
            entry1 = Entry(value=None, tableparameter_id=tb_status.id, entry_list_id=entrylist1.id)
            entry2 = Entry(value="custom", tableparameter_id=tb_status.id, entry_list_id=entrylist2.id)
            entry3 = Entry(value=None, tableparameter_id=tb_status.id, entry_list_id=entrylist3.id)
            
            self.db.session.add_all([entrylist1, entrylist2, entrylist3, entry1, entry2, entry3])
            self.db.session.commit()
            
            self.tb_status = tb_status
            self.entry1_id = entry1.id
            self.entry2_id = entry2.id
            self.entry3_id = entry3.id
    
    def test_update_default_value_entries(self):
        """Test updating only null entries with default value"""
        with self.app.app_context():
            tb_param = TableParameter.query.first()
            
            # Update default value
            update_default_value_entries(tb_param, "pending")
            self.db.session.commit()
            
            # Verify only null entries were updated
            entry1 = self.db.session.get(Entry, self.entry1_id)
            entry2 = self.db.session.get(Entry, self.entry2_id)
            entry3 = self.db.session.get(Entry, self.entry3_id)
            
            self.assertEqual(entry1.value, "pending")  # Was null, now pending
            self.assertEqual(entry2.value, "custom")   # Was custom, still custom
            self.assertEqual(entry3.value, "pending")  # Was null, now pending
    
    def test_update_default_value_entries_all_have_values(self):
        """Test updating when all entries already have values"""
        with self.app.app_context():
            tb_param = TableParameter.query.first()
            
            # Set all entries to have values
            entries = tb_param.entries
            for entry in entries:
                entry.value = "existing"
            self.db.session.commit()
            
            # Update default value
            update_default_value_entries(tb_param, "new_default")
            self.db.session.commit()
            
            # Verify no entries were changed
            for entry in tb_param.entries:
                self.assertEqual(entry.value, "existing")


class TestEntryWithDatetimeFields(TestConfig):
    """Test entry creation and updates with datetime fields"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="Events", description="Events table", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table with date/datetime fields
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            tb_date = TableParameter(name="event_date", data_type="date", table_id=table.id)
            tb_datetime = TableParameter(name="created_at", data_type="datetime", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_date, tb_datetime])
            self.db.session.commit()
            
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            self.db.session.add(pk)
            self.db.session.commit()
            
            tb_id.constraints.append(pk)
            self.db.session.commit()
            
            self.user = user
            self.table = table
    
    def test_create_entry_with_date_field(self):
        """Test creating entry with date field"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "Test Event",
                "event_date": "2024-12-15",
                "created_at": "2024-12-15T10:30:00"
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            self.assertIn("2024-12-15", result["event_date"])
    
    def test_create_entry_with_invalid_date(self):
        """Test creating entry with invalid date format"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "Test Event",
                "event_date": "not-a-date",
                "created_at": "2024-12-15T10:30:00"
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("Wrong data type", result["error"])


class TestEntryWithNonNullableField(TestConfig):
    """Test entry creation with non-nullable field validation"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table with non-nullable field
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_name = TableParameter(name="name", data_type="string", table_id=table.id)
            tb_required = TableParameter(name="required_field", data_type="string", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_name, tb_required])
            self.db.session.commit()
            
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            self.db.session.add(pk)
            self.db.session.commit()
            
            tb_id.constraints.append(pk)
            # tb_required has no nullable constraint, so it's required
            self.db.session.commit()
            
            self.user = user
            self.table = table
    
    def test_create_entry_missing_non_nullable_field(self):
        """Test that missing non-nullable field fails"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "name": "Test"
                # required_field missing
            }
            
            result = create_entry(table, entry)
            
            self.assertIn("error", result)
            self.assertIn("incomplete field", result["error"].lower())


class TestEntryWithBooleanField(TestConfig):
    """Test entry creation with boolean fields"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            tb_id = TableParameter(name="_id", data_type="integer", primary_key=True, table_id=table.id)
            tb_active = TableParameter(name="is_active", data_type="boolean", table_id=table.id)
            
            self.db.session.add_all([tb_id, tb_active])
            self.db.session.commit()
            
            pk = Constraint.query.filter_by(name="primary_key").first() or Constraint(name="primary_key")
            self.db.session.add(pk)
            self.db.session.commit()
            
            tb_id.constraints.append(pk)
            self.db.session.commit()
            
            self.user = user
            self.table = table
    
    def test_create_entry_with_boolean_true(self):
        """Test creating entry with boolean True"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "is_active": True
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            self.assertTrue(result["is_active"])
    
    def test_create_entry_with_boolean_false(self):
        """Test creating entry with boolean False"""
        with self.app.app_context():
            table = Table.query.first()

            
            entry = {
                "_id": 1,
                "is_active": False
            }
            
            result = create_entry(table, entry)
            
            self.assertNotIn("error", result)
            self.assertFalse(result["is_active"])

