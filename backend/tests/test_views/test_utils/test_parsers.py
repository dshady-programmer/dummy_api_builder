"""
Tests for api/v1/views/utils/parsers.py
Testing value parsing functions
"""
from tests import TestConfig
from api.v1.views.utils.parsers import parse_value
from models import User, Api, Table, TableParameter


class TestParseValue(TestConfig):
    """Test parse_value function"""
    
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            user = User(email="test@test.com", password="password")
            api = Api(name="TestApi", description="Test", user_id=1)
            table = Table(name="TestTable", description="Test", api_id=1)
            self.db.session.add_all([user, api, table])
            self.db.session.commit()
            
            # Create table parameters with different datatypes
            self.tb_id = TableParameter(
                name="_id",
                data_type="integer",
                table_id=table.id
            )
            self.tb_name = TableParameter(
                name="name",
                data_type="string",
                table_id=table.id
            )
            self.tb_description = TableParameter(
                name="description",
                data_type="text",
                table_id=table.id
            )
            self.tb_active = TableParameter(
                name="active",
                data_type="boolean",
                table_id=table.id
            )
            self.tb_created = TableParameter(
                name="created",
                data_type="date",
                table_id=table.id
            )
            self.tb_timestamp = TableParameter(
                name="timestamp",
                data_type="datetime",
                table_id=table.id
            )
            
            self.db.session.add_all([
                self.tb_id, self.tb_name, self.tb_description,
                self.tb_active, self.tb_created, self.tb_timestamp
            ])
            self.db.session.commit()
    
    def test_parse_value_integer(self):
        """Test parsing integer values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="_id").first()
            
            result = parse_value(tb_param, "123")
            self.assertEqual(result, 123)
            self.assertIsInstance(result, int)
            
            result2 = parse_value(tb_param, "0")
            self.assertEqual(result2, 0)
            
            result3 = parse_value(tb_param, "-456")
            self.assertEqual(result3, -456)
    
    def test_parse_value_string(self):
        """Test parsing string values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="name").first()
            
            result = parse_value(tb_param, "John Doe")
            self.assertEqual(result, "John Doe")
            self.assertIsInstance(result, str)
            
            result2 = parse_value(tb_param, "123")
            self.assertEqual(result2, "123")
            self.assertIsInstance(result2, str)
    
    def test_parse_value_text(self):
        """Test parsing text values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="description").first()
            
            result = parse_value(tb_param, "Long text description")
            self.assertEqual(result, "Long text description")
            self.assertIsInstance(result, str)
    
    def test_parse_value_boolean_true(self):
        """Test parsing boolean True values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="active").first()
            
            result = parse_value(tb_param, "True")
            self.assertEqual(result, True)
            self.assertIsInstance(result, bool)
    
    def test_parse_value_boolean_false(self):
        """Test parsing boolean False values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="active").first()
            
            result = parse_value(tb_param, "False")
            self.assertEqual(result, False)
            self.assertIsInstance(result, bool)
    
    def test_parse_value_date(self):
        """Test parsing date values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="created").first()
            
            result = parse_value(tb_param, "2024-12-15")
            self.assertEqual(result, "2024-12-15")
            self.assertIsInstance(result, str)
    
    def test_parse_value_datetime(self):
        """Test parsing datetime values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="timestamp").first()
            
            result = parse_value(tb_param, "2024-12-15 10:30:00")
            self.assertEqual(result, "2024-12-15 10:30:00")
            self.assertIsInstance(result, str)
    
    def test_parse_value_null(self):
        """Test parsing null/empty values"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="name").first()
            
            result = parse_value(tb_param, None)
            self.assertIsNone(result)
            
            result2 = parse_value(tb_param, "")
            self.assertIsNone(result2)
    
    def test_parse_value_integer_from_empty_string(self):
        """Test parsing empty string for integer returns None"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="_id").first()
            
            result = parse_value(tb_param, "")
            self.assertIsNone(result)
            
            result2 = parse_value(tb_param, None)
            self.assertIsNone(result2)
    
    def test_parse_value_boolean_from_empty_string(self):
        """Test parsing empty string for boolean returns None"""
        with self.app.app_context():
            tb_param = TableParameter.query.filter_by(name="active").first()
            
            result = parse_value(tb_param, "")
            self.assertIsNone(result)
            
            result2 = parse_value(tb_param, None)
            self.assertIsNone(result2)