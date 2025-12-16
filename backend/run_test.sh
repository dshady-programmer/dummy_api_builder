#!/bin/bash
APP_ENVIRON="test" python -m unittest discover tests

# APP_ENVIRON="test" python -m unittest tests.test_views.test_utils.test_foreign_key_relationships.TestForeignKeyWithDefaultValue.test_create_fk_with_default_value

