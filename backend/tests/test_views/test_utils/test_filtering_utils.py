"""
Tests for api/v1/views/utils/filtering_utils.py
Testing filter suffixes, validation and query filtering
"""
import unittest
from api.v1.views.utils.filtering_utils import filter_suffixes, filter_validation, query_filter


class TestFilterSuffixes(unittest.TestCase):
    """Test filter_suffixes function"""
    
    def test_filter_suffixes_returns_base_name(self):
        """Test that filter_suffixes includes the base name"""
        result = filter_suffixes("age")
        self.assertIn("age", result)
    
    def test_filter_suffixes_includes_all_suffixes(self):
        """Test that all valid suffixes are included"""
        result = filter_suffixes("name")
        expected_suffixes = [
            "name",
            "name__lt",
            "name__gt",
            "name__lte",
            "name__gte",
            "name__startswith",
            "name__endswith",
            "name__like",
            "name__ilike",
            "name__istartswith",
            "name__iendswith",
            "name__iexact"
        ]
        
        for suffix in expected_suffixes:
            self.assertIn(suffix, result)
    
    def test_filter_suffixes_count(self):
        """Test that filter_suffixes returns correct count"""
        result = filter_suffixes("field")
        # Base name + 11 suffixes = 12 total
        self.assertEqual(len(result), 12)


class TestFilterValidation(unittest.TestCase):
    """Test filter_validation function"""
    
    # Test integer comparisons
    def test_filter_validation_integer_lt(self):
        """Test less than filter for integers"""
        result = filter_validation("age__lt", "integer", "30", "25")
        self.assertFalse(result)
        
        result2 = filter_validation("age__lt", "integer", "30", "35")
        self.assertTrue(result2)
    
    def test_filter_validation_integer_lte(self):
        """Test less than or equal filter for integers"""
        """
            value must be less than or equal to check_value
            value is the first number
            check_value is the second number
        """
        result = filter_validation("age__lte", "integer", "30", "30")
        self.assertTrue(result)
        
        result2 = filter_validation("age__lte", "integer", "30", "25")
        self.assertFalse(result2) # check_value (25) must be greater than value (30) age__lte = 25 retrieves all dataset less than 25 or equal to 25 
        
        result3 = filter_validation("age__lte", "integer", "30", "35")
        self.assertTrue(result3)
    
    def test_filter_validation_integer_gt(self):
        """Test greater than filter for integers"""
        result = filter_validation("age__gt", "integer", "30", "35")
        self.assertFalse(result)
        
        result2 = filter_validation("age__gt", "integer", "30", "25")
        self.assertTrue(result2)
    
    def test_filter_validation_integer_gte(self):
        """Test greater than or equal filter for integers"""
        """
        value must be greater than or equal to check_value
        value is the first number
        check_value is the second number
        """
        result = filter_validation("age__gte", "integer", "30", "30")
        self.assertTrue(result)
        
        result2 = filter_validation("age__gte", "integer", "30", "35")
        self.assertFalse(result2)
        
        result3 = filter_validation("age__gte", "integer", "30", "25")
        self.assertTrue(result3)
    
    def test_filter_validation_integer_exact(self):
        """Test exact match filter for integers"""
        result = filter_validation("age", "integer", "30", "30")
        self.assertTrue(result)
        
        result2 = filter_validation("age", "integer", "30", "25")
        self.assertFalse(result2)
    
    # Test string comparisons
    def test_filter_validation_string_startswith(self):
        """Test startswith filter for strings"""
        result = filter_validation("name__startswith", "string", "John Doe", "John")
        self.assertTrue(result)
        
        result2 = filter_validation("name__startswith", "string", "John Doe", "Doe")
        self.assertFalse(result2)
    
    def test_filter_validation_string_endswith(self):
        """Test endswith filter for strings"""
        result = filter_validation("name__endswith", "string", "John Doe", "Doe")
        self.assertTrue(result)
        
        result2 = filter_validation("name__endswith", "string", "John Doe", "John")
        self.assertFalse(result2)
    
    def test_filter_validation_string_like(self):
        """Test like (contains) filter for strings"""
        result = filter_validation("name__like", "string", "John Doe", "oh")
        self.assertTrue(result)
        
        result2 = filter_validation("name__like", "string", "John Doe", "xyz")
        self.assertFalse(result2)
    
    def test_filter_validation_string_ilike(self):
        """Test case-insensitive like filter"""
        result = filter_validation("name__ilike", "string", "John Doe", "JOHN")
        self.assertTrue(result)
        
        result2 = filter_validation("name__ilike", "string", "John Doe", "doe")
        self.assertTrue(result2)
    
    def test_filter_validation_string_istartswith(self):
        """Test case-insensitive startswith filter"""
        result = filter_validation("name__istartswith", "string", "John Doe", "john")
        self.assertTrue(result)
        
        result2 = filter_validation("name__istartswith", "string", "John Doe", "JOHN")
        self.assertTrue(result2)
    
    def test_filter_validation_string_iendswith(self):
        """Test case-insensitive endswith filter"""
        result = filter_validation("name__iendswith", "string", "John Doe", "DOE")
        self.assertTrue(result)
        
        result2 = filter_validation("name__iendswith", "string", "John Doe", "doe")
        self.assertTrue(result2)
    
    def test_filter_validation_string_iexact(self):
        """Test case-insensitive exact match"""
        result = filter_validation("name__iexact", "string", "John Doe", "JOHN DOE")
        self.assertTrue(result)
        
        result2 = filter_validation("name__iexact", "string", "John Doe", "john doe")
        self.assertTrue(result2)
        
        result3 = filter_validation("name__iexact", "string", "John Doe", "Jane Doe")
        self.assertFalse(result3)
    
    def test_filter_validation_string_exact(self):
        """Test exact match filter for strings"""
        result = filter_validation("name", "string", "John Doe", "John Doe")
        self.assertTrue(result)
        
        result2 = filter_validation("name", "string", "John Doe", "john doe")
        self.assertFalse(result2)
    
    # Test boolean comparisons
    def test_filter_validation_boolean(self):
        """Test boolean filter"""
        result = filter_validation("active", "boolean", "True", "True")
        self.assertTrue(result)
        
        result2 = filter_validation("active", "boolean", "True", "False")
        self.assertFalse(result2)
        
        result3 = filter_validation("active", "boolean", "False", "False")
        self.assertTrue(result3)
    
    # Test date/datetime comparisons
    def test_filter_validation_date_lt(self):
        """Test less than filter for dates"""
        result = filter_validation("created__lt", "date", "2024-12-15", "2024-12-10")
        self.assertFalse(result)
        
        result2 = filter_validation("created__lt", "date", "2024-12-15", "2024-12-20")
        self.assertTrue(result2)
    
    def test_filter_validation_date_gt(self):
        """Test greater than filter for dates"""
        result = filter_validation("created__gt", "date", "2024-12-15", "2024-12-20")
        self.assertFalse(result)
        
        result2 = filter_validation("created__gt", "date", "2024-12-15", "2024-12-10")
        self.assertTrue(result2)
    
    def test_filter_validation_datetime_lte(self):
        """Test less than or equal for datetime"""
        result = filter_validation("timestamp__lte", "datetime", "2024-12-15T10:00:00", "2024-12-15T10:00:00")
        self.assertTrue(result)
        
        result2 = filter_validation("timestamp__lte", "datetime", "2024-12-15T10:00:00", "2024-12-15T09:00:00")
        self.assertFalse(result2)
    
    def test_filter_validation_datetime_gte(self):
        """Test greater than or equal for datetime"""
        result = filter_validation("timestamp__gte", "datetime", "2024-12-15T10:00:00", "2024-12-15T10:00:00")
        self.assertTrue(result)
        
        result2 = filter_validation("timestamp__gte", "datetime", "2024-12-15T10:00:00", "2024-12-15T11:00:00")
        self.assertFalse(result2)
    
    # Test error handling
    def test_filter_validation_with_invalid_integer(self):
        """Test that invalid integer values return False"""
        result = filter_validation("age__lt", "integer", "30", "invalid")
        self.assertFalse(result)
    
    def test_filter_validation_with_invalid_date(self):
        """Test that invalid date values return False"""
        result = filter_validation("created__lt", "date", "2024-12-15", "not-a-date")
        self.assertFalse(result)
    
    def test_filter_validation_with_invalid_boolean(self):
        """Test that invalid boolean values return False"""
        result = filter_validation("active", "boolean", "True", "maybe")
        self.assertFalse(result)
    
    # Test text datatype (should work same as string)
    def test_filter_validation_text_like(self):
        """Test like filter works for text datatype"""
        result = filter_validation("description__like", "text", "Long description text", "description")
        self.assertTrue(result)

    def test_filter_validation_boolean_with_malicious_input(self):
        """Test boolean filter with malicious input"""
        result1 = filter_validation("active", "boolean", "print('Hacked!')", "print('Hacked!')")
        result2 = filter_validation("active", "boolean", "__import__('os').system('ls')", "__import__('os').system('ls')")
        self.assertFalse(result1)
        self.assertFalse(result2)

    

class TestQueryFilter(unittest.TestCase):
    """Test query_filter function"""
    
    def test_query_filter_with_exact_match(self):
        """Test query filter with exact match"""
        args = {"name": "John Doe"}
        found, filter_in = query_filter("name", args, "string", "John Doe", False, True)
        
        self.assertTrue(found)
        self.assertTrue(filter_in)
    
    def test_query_filter_with_no_match(self):
        """Test query filter when value doesn't match"""
        args = {"name": "John Doe"}
        found, filter_in = query_filter("name", args, "string", "Jane Doe", False, True)
        
        self.assertTrue(found)
        self.assertFalse(filter_in)
    
    def test_query_filter_with_suffix(self):
        """Test query filter with suffix"""
        args = {"age__gte": "30"}
        found, filter_in = query_filter("age", args, "integer", "35", False, True)
        
        self.assertTrue(found)
        self.assertTrue(filter_in)
    
    def test_query_filter_field_not_in_args(self):
        """Test query filter when field not in args"""
        args = {"name": "John"}
        found, filter_in = query_filter("age", args, "integer", "30", False, True)
        
        # found should remain False, filter_in unchanged
        self.assertFalse(found)
        self.assertTrue(filter_in)
    
    def test_query_filter_maintains_filter_in_false(self):
        """Test that query_filter maintains filter_in=False"""
        args = {"age__gt": "30"}
        found, filter_in = query_filter("age", args, "integer", "25", False, False)
        
        self.assertTrue(found)
        self.assertFalse(filter_in)
    
    def test_query_filter_with_multiple_suffixes(self):
        """Test query filter checks multiple suffixes"""
        args = {"name__ilike": "john"}
        found, filter_in = query_filter("name", args, "string", "John Doe", False, True)
        
        self.assertTrue(found)
        self.assertTrue(filter_in)
    
    def test_query_filter_integer_comparison(self):
        """Test query filter with integer lt comparison"""
        args = {"age__lt": "30"}
        found, filter_in = query_filter("age", args, "integer", "25", False, True)
        
        self.assertTrue(found)
        self.assertTrue(filter_in)
        
        found2, filter_in2 = query_filter("age", args, "integer", "35", False, True)
        self.assertTrue(found2)
        self.assertFalse(filter_in2)
    
    def test_query_filter_preserves_found_flag(self):
        """Test that found flag is preserved if already True"""
        args = {"other_field": "value"}
        found, filter_in = query_filter("name", args, "string", "John", True, True)
        
        # Should preserve found=True even though name not in args
        self.assertTrue(found)
        self.assertTrue(filter_in)




