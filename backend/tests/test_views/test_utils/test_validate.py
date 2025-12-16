"""
Tests for api/v1/views/utils/validate.py
Testing validation helper functions
"""
import unittest
from tests import TestConfig
from api.v1.views.utils.validate import (
    validate_constraint,
    validate_dtType,
    validate_name,
    validate_entry_value,
    validate_entry_value_length,
    validate_primary_key_dtType,
    autogenerate_keys
)
from models import User, Api, Table, TableParameter, Entry, EntryList


class TestValidateConstraint(unittest.TestCase):
    """Test validate_constraint function"""
    
    def test_validate_constraint_valid_constraints(self):
        """Test validation of all valid constraints"""
        valid_constraints = ["foreign_key", "unique", "nullable", "primary_key", "default"]
        
        for constraint in valid_constraints:
            self.assertTrue(validate_constraint(constraint))
    
    def test_validate_constraint_invalid_constraints(self):
        """Test validation of invalid constraints"""
        invalid_constraints = ["not_null", "check", "pk", "fk", ""]
        
        for constraint in invalid_constraints:
            self.assertFalse(validate_constraint(constraint))


class TestValidateDtType(unittest.TestCase):
    """Test validate_dtType function"""
    
    def test_validate_dttype_valid_types(self):
        """Test validation of all valid data types"""
        valid_types = ["string", "text", "integer", "boolean", "date", "datetime"]
        
        for dt in valid_types:
            self.assertTrue(validate_dtType(dt))
    
    def test_validate_dttype_invalid_types(self):
        """Test validation of invalid data types"""
        invalid_types = ["int", "str", "bool", "float", "decimal", "varchar", ""]
        
        for dt in invalid_types:
            self.assertFalse(validate_dtType(dt))


class TestValidateName(unittest.TestCase):
    """Test validate_name function"""
    
    def test_validate_name_valid_names(self):
        """Test validation of valid Python identifiers"""
        valid_names = ["user", "user_name", "_id", "firstName", "camelCase", "snake_case"]
        
        for name in valid_names:
            self.assertTrue(validate_name(name), f"{name} should be valid")
    
    def test_validate_name_invalid_starting_with_number(self):
        """Test that names starting with numbers are invalid"""
        invalid_names = ["1user", "2name", "9field"]
        
        for name in invalid_names:
            self.assertFalse(validate_name(name))
    
    def test_validate_name_python_keywords(self):
        """Test that Python keywords are invalid"""
        keywords = ["for", "if", "else", "while", "def", "class", "return", "import"]
        
        for keyword in keywords:
            self.assertFalse(validate_name(keyword))
    
    def test_validate_name_with_spaces(self):
        """Test that names with spaces are invalid"""
        self.assertFalse(validate_name("user name"))
        self.assertFalse(validate_name("first name"))
    
    def test_validate_name_with_special_chars(self):
        """Test that names with special characters are invalid"""
        invalid_names = ["user-name", "user.name", "user@name", "user$name"]
        
        for name in invalid_names:
            self.assertFalse(validate_name(name))
    
    def test_validate_name_too_short(self):
        """Test that names shorter than 3 characters are invalid"""
        self.assertFalse(validate_name("ab"))
        self.assertFalse(validate_name("x"))
        self.assertFalse(validate_name(""))
    
    def test_validate_name_exactly_three_chars(self):
        """Test that 3 character names are valid"""
        self.assertTrue(validate_name("abc"))
        self.assertTrue(validate_name("xyz"))
    
    def test_validate_name_none_value(self):
        """Test that None returns False"""
        self.assertFalse(validate_name(None))
    
    def test_validate_name_non_string(self):
        """Test that non-string types return False"""
        self.assertFalse(validate_name(123))
        self.assertFalse(validate_name(['list']))


class TestValidateEntryValue(unittest.TestCase):
    """Test validate_entry_value function"""
    
    def test_validate_entry_value_integer_valid(self):
        """Test validation of valid integer values"""
        self.assertTrue(validate_entry_value("123", "integer"))
        self.assertTrue(validate_entry_value("0", "integer"))
        self.assertTrue(validate_entry_value("-456", "integer"))
    
    def test_validate_entry_value_integer_invalid(self):
        """Test validation of invalid integer values"""
        self.assertFalse(validate_entry_value("12.5", "integer"))
        self.assertFalse(validate_entry_value("abc", "integer"))
        self.assertFalse(validate_entry_value("", "integer"))
        self.assertFalse(validate_entry_value(None, "integer"))
    
    def test_validate_entry_value_boolean_valid(self):
        """Test validation of valid boolean values"""
        self.assertTrue(validate_entry_value("True", "boolean"))
        self.assertTrue(validate_entry_value("False", "boolean"))
    
    def test_validate_entry_value_boolean_invalid(self):
        """Test validation of invalid boolean values"""
        self.assertFalse(validate_entry_value("true", "boolean"))
        self.assertFalse(validate_entry_value("false", "boolean"))
        self.assertFalse(validate_entry_value("1", "boolean"))
        self.assertFalse(validate_entry_value("yes", "boolean"))
        self.assertFalse(validate_entry_value("", "boolean"))
    
    def test_validate_entry_value_date_valid(self):
        """Test validation of valid date values"""
        self.assertTrue(validate_entry_value("2024-12-15", "date"))
        self.assertTrue(validate_entry_value("2024/12/15", "date"))
        self.assertTrue(validate_entry_value("Dec 15, 2024", "date"))
    
    def test_validate_entry_value_date_invalid(self):
        """Test validation of invalid date values"""
        self.assertFalse(validate_entry_value("not-a-date", "date"))
        self.assertFalse(validate_entry_value("2024-13-45", "date"))
        self.assertFalse(validate_entry_value("", "date"))
        self.assertFalse(validate_entry_value(None, "date"))
    
    def test_validate_entry_value_datetime_valid(self):
        """Test validation of valid datetime values"""
        self.assertTrue(validate_entry_value("2024-12-15 10:30:00", "datetime"))
        self.assertTrue(validate_entry_value("2024-12-15T10:30:00", "datetime"))
        self.assertTrue(validate_entry_value("Dec 15, 2024 10:30 AM", "datetime"))
    
    def test_validate_entry_value_datetime_invalid(self):
        """Test validation of invalid datetime values"""
        self.assertFalse(validate_entry_value("not-a-datetime", "datetime"))
        self.assertFalse(validate_entry_value("", "datetime"))
        self.assertFalse(validate_entry_value(None, "datetime"))
    
    def test_validate_entry_value_string_always_valid(self):
        """Test that any value is valid for string type"""
        self.assertTrue(validate_entry_value("any string", "string"))
        self.assertTrue(validate_entry_value("123", "string"))
        self.assertFalse(validate_entry_value("", "string")) 
    
    def test_validate_entry_value_text_always_valid(self):
        """Test that any value is valid for text type"""
        self.assertTrue(validate_entry_value("any text", "text"))
        self.assertTrue(validate_entry_value("long text content", "text"))


class TestValidateEntryValueLength(unittest.TestCase):
    """Test validate_entry_value_length function"""
    
    def test_validate_length_no_limit(self):
        """Test that None length always returns True"""
        self.assertTrue(validate_entry_value_length("any length string", "string", None))
        self.assertTrue(validate_entry_value_length("x" * 1000, "text", None))
    
    def test_validate_length_string_within_limit(self):
        """Test string within length limit"""
        self.assertTrue(validate_entry_value_length("hello", "string", 10))
        self.assertTrue(validate_entry_value_length("x" * 50, "string", 50))
    
    def test_validate_length_string_exceeds_limit(self):
        """Test string exceeding length limit"""
        self.assertFalse(validate_entry_value_length("hello world", "string", 5))
        self.assertFalse(validate_entry_value_length("x" * 100, "string", 50))
    
    def test_validate_length_text_within_limit(self):
        """Test text within length limit"""
        self.assertTrue(validate_entry_value_length("short text", "text", 20))
    
    def test_validate_length_text_exceeds_limit(self):
        """Test text exceeding length limit"""
        self.assertFalse(validate_entry_value_length("x" * 100, "text", 50))
    
    def test_validate_length_non_string_types(self):
        """Test that length validation always passes for non-string types"""
        self.assertTrue(validate_entry_value_length("12345", "integer", 3))
        self.assertTrue(validate_entry_value_length("True", "boolean", 2))
        self.assertTrue(validate_entry_value_length("2024-12-15", "date", 5))


class TestValidatePrimaryKeyDtType(unittest.TestCase):
    """Test validate_primary_key_dtType function"""
    
    def test_validate_pk_valid_types(self):
        """Test valid primary key data types"""
        valid_types = ["string", "text", "integer"]
        
        for dt in valid_types:
            self.assertTrue(validate_primary_key_dtType(dt))
    
    def test_validate_pk_invalid_types(self):
        """Test invalid primary key data types"""
        invalid_types = ["boolean", "date", "datetime"]
        
        for dt in invalid_types:
            self.assertFalse(validate_primary_key_dtType(dt))


class TestAutogenerateKeys(TestConfig):
    """Test autogenerate_keys function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            self.tb_id = TableParameter(
                name="_id",
                data_type="integer",
                primary_key=True,
                table_id=table.id
            )
            self.tb_uuid = TableParameter(
                name="uuid",
                data_type="string",
                primary_key=True,
                table_id=table.id
            )
            self.db.session.add_all([self.tb_id, self.tb_uuid])
            self.db.session.commit()
    
    def test_autogenerate_integer_key(self):
        """Test auto-generation of integer primary keys"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="_id").first()
            value = autogenerate_keys(tb_param)
            
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 1)
            self.assertLessEqual(value, 2000)
    
    def test_autogenerate_string_key(self):
        """Test auto-generation of string/UUID primary keys"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="uuid").first()
            value = autogenerate_keys(tb_param)
            
            self.assertIsInstance(value, str)
            self.assertEqual(len(value), 36)  # UUID length
            self.assertIn("-", value)  # UUID format
    
    def test_autogenerate_unique_values(self):
        """Test that auto-generated keys are unique"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="_id").first()
            
            # Generate multiple keys
            values = [autogenerate_keys(tb_param) for _ in range(10)]
            
            # All should be unique
            self.assertEqual(len(values), len(set(values)))
    
    def test_autogenerate_avoids_existing_values(self):
        """Test that auto-generation avoids existing values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="_id").first()
            table = tb_param.table
            
            # Create an entry with a specific value
            entrylist = EntryList(table_id=table.id, primary_key_value="100")
            entry = Entry(value="100", tableparameter_id=tb_param.id, entry_list_id=entrylist.id)
            self.db.session.add_all([entrylist, entry])
            self.db.session.commit()
            
            # Generate new key - should not be "100"
            new_value = autogenerate_keys(tb_param)
            self.assertNotEqual(new_value, 100)

