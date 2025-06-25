"""
Tests for the config schema validation module.
"""

import unittest
from smart_tiling.config.schema import (
    validate_config,
    validate_rule,
    validate_parent,
    validate_child,
    validate_actions,
    validate_action,
    validate_set_mode,
    validate_place,
    validate_size_ratio,
    validate_boolean_action,
    validate_settings
)


class TestConfigSchemaValidation(unittest.TestCase):
    """Test cases for config schema validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            'rules': [
                {
                    'name': 'Neovim Terminal',
                    'parent': {
                        'app_id': ['neovim', 'nvim'],
                        'class': ['Neovim']
                    },
                    'child': {
                        'app_id': ['kitty', 'alacritty', 'foot']
                    },
                    'actions': [
                        {'set_mode': 'v after'},
                        {'place': 'below'},
                        {'size_ratio': 0.333},
                        {'inherit_cwd': True},
                        {'preserve_column': True}
                    ]
                }
            ],
            'settings': {
                'debug': False,
                'rule_timeout': 10
            }
        }
        
        self.valid_rule = self.valid_config['rules'][0]
    
    def test_validate_config_valid(self):
        """Test validation of a valid configuration."""
        is_valid, errors = validate_config(self.valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_config_not_dict(self):
        """Test validation when config is not a dictionary."""
        is_valid, errors = validate_config("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("Configuration must be a dictionary", errors)
    
    def test_validate_config_missing_rules(self):
        """Test validation when rules field is missing."""
        config = {'settings': {'debug': True}}
        is_valid, errors = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("Configuration missing required field: rules", errors)
    
    def test_validate_config_rules_not_list(self):
        """Test validation when rules is not a list."""
        config = {'rules': 'not a list'}
        is_valid, errors = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("Field 'rules' must be a list", errors)
    
    def test_validate_config_empty_rules(self):
        """Test validation with empty rules list."""
        config = {'rules': []}
        is_valid, errors = validate_config(config)
        self.assertTrue(is_valid)  # Empty rules list is valid
        self.assertEqual(errors, [])
    
    def test_validate_config_duplicate_rule_names(self):
        """Test validation catches duplicate rule names."""
        config = {
            'rules': [
                {
                    'name': 'Duplicate Name',
                    'parent': {'app_id': ['test']},
                    'child': {'app_id': ['test']},
                    'actions': [{'place': 'below'}]
                },
                {
                    'name': 'Duplicate Name',
                    'parent': {'app_id': ['test2']},
                    'child': {'app_id': ['test2']},
                    'actions': [{'place': 'right'}]
                }
            ]
        }
        is_valid, errors = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("Duplicate rule name: 'Duplicate Name'", errors)
    
    def test_validate_config_invalid_settings(self):
        """Test validation with invalid settings."""
        config = {
            'rules': [],
            'settings': 'not a dict'
        }
        is_valid, errors = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("settings must be a dictionary", errors)
    
    def test_validate_rule_valid(self):
        """Test validation of a valid rule."""
        is_valid, errors = validate_rule(self.valid_rule)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_rule_not_dict(self):
        """Test validation when rule is not a dictionary."""
        is_valid, errors = validate_rule("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("Rule must be a dictionary", errors)
    
    def test_validate_rule_missing_required_fields(self):
        """Test validation when rule is missing required fields."""
        rule = {'name': 'Test'}
        is_valid, errors = validate_rule(rule)
        self.assertFalse(is_valid)
        self.assertIn("Rule missing required field: parent", errors)
        self.assertIn("Rule missing required field: child", errors)
        self.assertIn("Rule missing required field: actions", errors)
    
    def test_validate_rule_invalid_name(self):
        """Test validation of rule name field."""
        # Name not a string
        rule = {
            'name': 123,
            'parent': {'app_id': ['test']},
            'child': {'app_id': ['test']},
            'actions': [{'place': 'below'}]
        }
        is_valid, errors = validate_rule(rule)
        self.assertFalse(is_valid)
        self.assertIn("Rule 'name' must be a string", errors)
        
        # Empty name
        rule['name'] = ''
        is_valid, errors = validate_rule(rule)
        self.assertFalse(is_valid)
        self.assertIn("Rule 'name' cannot be empty", errors)
    
    def test_validate_parent_valid(self):
        """Test validation of valid parent configurations."""
        # With app_id
        parent = {'app_id': ['neovim', 'vim']}
        is_valid, errors = validate_parent(parent)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # With class
        parent = {'class': ['Neovim', 'Terminal']}
        is_valid, errors = validate_parent(parent)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # With title_pattern
        parent = {'title_pattern': ['.*neovim.*']}
        is_valid, errors = validate_parent(parent)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # With multiple fields
        parent = {
            'app_id': ['neovim'],
            'class': ['Neovim'],
            'title_pattern': ['.*neovim.*']
        }
        is_valid, errors = validate_parent(parent)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_parent_not_dict(self):
        """Test validation when parent is not a dictionary."""
        is_valid, errors = validate_parent("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("parent must be a dictionary", errors)
    
    def test_validate_parent_empty(self):
        """Test validation when parent is empty."""
        is_valid, errors = validate_parent({})
        self.assertFalse(is_valid)
        self.assertIn("parent cannot be empty", errors)
    
    def test_validate_parent_unknown_field(self):
        """Test validation when parent has unknown fields."""
        parent = {'unknown_field': ['test']}
        is_valid, errors = validate_parent(parent)
        self.assertFalse(is_valid)
        self.assertIn("Unknown parent field: unknown_field", errors)
    
    def test_validate_parent_field_not_list(self):
        """Test validation when parent field is not a list."""
        parent = {'app_id': 'not a list'}
        is_valid, errors = validate_parent(parent)
        self.assertFalse(is_valid)
        self.assertIn("parent.app_id must be a list", errors)
    
    def test_validate_parent_empty_list(self):
        """Test validation when parent field is empty list."""
        parent = {'app_id': []}
        is_valid, errors = validate_parent(parent)
        self.assertFalse(is_valid)
        self.assertIn("parent.app_id cannot be empty", errors)
    
    def test_validate_parent_non_string_items(self):
        """Test validation when parent field contains non-string items."""
        parent = {'app_id': ['valid', 123, 'also_valid']}
        is_valid, errors = validate_parent(parent)
        self.assertFalse(is_valid)
        self.assertIn("parent.app_id[1] must be a string", errors)
    
    def test_validate_child_valid(self):
        """Test validation of valid child configuration."""
        child = {'app_id': ['kitty', 'alacritty']}
        is_valid, errors = validate_child(child)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_child_not_dict(self):
        """Test validation when child is not a dictionary."""
        is_valid, errors = validate_child("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("child must be a dictionary", errors)
    
    def test_validate_child_missing_app_id(self):
        """Test validation when child is missing app_id."""
        child = {}
        is_valid, errors = validate_child(child)
        self.assertFalse(is_valid)
        self.assertIn("child missing required field: app_id", errors)
    
    def test_validate_child_app_id_not_list(self):
        """Test validation when child app_id is not a list."""
        child = {'app_id': 'not a list'}
        is_valid, errors = validate_child(child)
        self.assertFalse(is_valid)
        self.assertIn("child.app_id must be a list", errors)
    
    def test_validate_child_empty_app_id(self):
        """Test validation when child app_id is empty."""
        child = {'app_id': []}
        is_valid, errors = validate_child(child)
        self.assertFalse(is_valid)
        self.assertIn("child.app_id cannot be empty", errors)
    
    def test_validate_child_non_string_app_id(self):
        """Test validation when child app_id contains non-string items."""
        child = {'app_id': ['valid', 123]}
        is_valid, errors = validate_child(child)
        self.assertFalse(is_valid)
        self.assertIn("child.app_id[1] must be a string", errors)
    
    def test_validate_child_unknown_field(self):
        """Test validation when child has unknown fields."""
        child = {'app_id': ['test'], 'unknown_field': ['test']}
        is_valid, errors = validate_child(child)
        self.assertFalse(is_valid)
        self.assertIn("Unknown child field: unknown_field", errors)
    
    def test_validate_actions_valid(self):
        """Test validation of valid actions."""
        actions = [
            {'set_mode': 'v after'},
            {'place': 'below'},
            {'size_ratio': 0.5}
        ]
        is_valid, errors = validate_actions(actions)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_actions_not_list(self):
        """Test validation when actions is not a list."""
        is_valid, errors = validate_actions("not a list")
        self.assertFalse(is_valid)
        self.assertIn("actions must be a list", errors)
    
    def test_validate_actions_empty(self):
        """Test validation when actions is empty."""
        is_valid, errors = validate_actions([])
        self.assertFalse(is_valid)
        self.assertIn("actions cannot be empty", errors)
    
    def test_validate_action_valid_types(self):
        """Test validation of all valid action types."""
        valid_actions = [
            {'set_mode': 'h'},
            {'set_mode': 'v after'},
            {'place': 'below'},
            {'place': 'right'},
            {'place': 'above'},
            {'place': 'left'},
            {'size_ratio': 0.5},
            {'inherit_cwd': True},
            {'preserve_column': False}
        ]
        
        for action in valid_actions:
            is_valid, errors = validate_action(action)
            self.assertTrue(is_valid, f"Action {action} should be valid, but got errors: {errors}")
    
    def test_validate_action_not_dict(self):
        """Test validation when action is not a dictionary."""
        is_valid, errors = validate_action("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("action must be a dictionary", errors)
    
    def test_validate_action_multiple_keys(self):
        """Test validation when action has multiple keys."""
        action = {'set_mode': 'h', 'place': 'below'}
        is_valid, errors = validate_action(action)
        self.assertFalse(is_valid)
        self.assertIn("action must contain exactly one key-value pair", errors)
    
    def test_validate_action_unknown_type(self):
        """Test validation of unknown action type."""
        action = {'invalid_action': 'value'}
        is_valid, errors = validate_action(action)
        self.assertFalse(is_valid)
        self.assertIn("unknown action type 'invalid_action'", errors)
    
    def test_validate_set_mode_valid(self):
        """Test validation of valid set_mode values."""
        valid_modes = ['h', 'v', 'h after', 'v before', 'h end', 'v beg']
        
        for mode in valid_modes:
            is_valid, errors = validate_set_mode(mode)
            self.assertTrue(is_valid, f"Mode '{mode}' should be valid, but got errors: {errors}")
    
    def test_validate_set_mode_invalid(self):
        """Test validation of invalid set_mode values."""
        invalid_modes = [
            'x',
            'h invalid',
            'v after before',
            '',
            'horizontal',
            'h afterr'
        ]
        
        for mode in invalid_modes:
            is_valid, errors = validate_set_mode(mode)
            self.assertFalse(is_valid, f"Mode '{mode}' should be invalid")
            self.assertIn("invalid set_mode format", errors[0])
    
    def test_validate_set_mode_not_string(self):
        """Test validation when set_mode is not a string."""
        is_valid, errors = validate_set_mode(123)
        self.assertFalse(is_valid)
        self.assertIn("set_mode value must be a string", errors)
    
    def test_validate_place_valid(self):
        """Test validation of valid place values."""
        valid_places = ['below', 'right', 'above', 'left']
        
        for place in valid_places:
            is_valid, errors = validate_place(place)
            self.assertTrue(is_valid, f"Place '{place}' should be valid")
    
    def test_validate_place_invalid(self):
        """Test validation of invalid place values."""
        invalid_places = ['down', 'up', 'top', 'bottom', 'center', '']
        
        for place in invalid_places:
            is_valid, errors = validate_place(place)
            self.assertFalse(is_valid, f"Place '{place}' should be invalid")
            self.assertIn("invalid place direction", errors[0])
    
    def test_validate_place_not_string(self):
        """Test validation when place is not a string."""
        is_valid, errors = validate_place(123)
        self.assertFalse(is_valid)
        self.assertIn("place value must be a string", errors)
    
    def test_validate_size_ratio_valid(self):
        """Test validation of valid size_ratio values."""
        valid_ratios = [0.1, 0.5, 0.9, 0.33333]
        
        for ratio in valid_ratios:
            is_valid, errors = validate_size_ratio(ratio)
            self.assertTrue(is_valid, f"Ratio {ratio} should be valid")
    
    def test_validate_size_ratio_invalid(self):
        """Test validation of invalid size_ratio values."""
        invalid_ratios = [0.0, 0.05, 1.0, 1.5, -0.5]
        
        for ratio in invalid_ratios:
            is_valid, errors = validate_size_ratio(ratio)
            self.assertFalse(is_valid, f"Ratio {ratio} should be invalid")
            self.assertIn("size_ratio must be between 0.1 and 0.9", errors[0])
    
    def test_validate_size_ratio_not_number(self):
        """Test validation when size_ratio is not a number."""
        is_valid, errors = validate_size_ratio("0.5")
        self.assertFalse(is_valid)
        self.assertIn("size_ratio value must be a number", errors)
    
    def test_validate_boolean_action_valid(self):
        """Test validation of valid boolean action values."""
        is_valid, errors = validate_boolean_action(True, 'test_action')
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        is_valid, errors = validate_boolean_action(False, 'test_action')
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_boolean_action_invalid(self):
        """Test validation of invalid boolean action values."""
        invalid_values = [1, 0, "true", "false", None, []]
        
        for value in invalid_values:
            is_valid, errors = validate_boolean_action(value, 'test_action')
            self.assertFalse(is_valid, f"Value {value} should be invalid")
            self.assertIn("test_action value must be a boolean", errors[0])
    
    def test_validate_settings_valid(self):
        """Test validation of valid settings."""
        valid_settings = [
            {},
            {'debug': True},
            {'rule_timeout': 15},
            {'debug': False, 'rule_timeout': 5.5}
        ]
        
        for settings in valid_settings:
            is_valid, errors = validate_settings(settings)
            self.assertTrue(is_valid, f"Settings {settings} should be valid, but got errors: {errors}")
    
    def test_validate_settings_not_dict(self):
        """Test validation when settings is not a dictionary."""
        is_valid, errors = validate_settings("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("settings must be a dictionary", errors)
    
    def test_validate_settings_invalid_debug(self):
        """Test validation when settings.debug is not a boolean."""
        settings = {'debug': 'true'}
        is_valid, errors = validate_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("settings.debug must be a boolean", errors)
    
    def test_validate_settings_invalid_rule_timeout(self):
        """Test validation of invalid rule_timeout values."""
        # Not a number
        settings = {'rule_timeout': 'ten'}
        is_valid, errors = validate_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("settings.rule_timeout must be a number", errors)
        
        # Negative value
        settings = {'rule_timeout': -5}
        is_valid, errors = validate_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("settings.rule_timeout must be greater than 0", errors)
        
        # Zero
        settings = {'rule_timeout': 0}
        is_valid, errors = validate_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("settings.rule_timeout must be greater than 0", errors)
    
    def test_validate_settings_unknown_field(self):
        """Test validation when settings has unknown fields."""
        settings = {'unknown_field': 'value'}
        is_valid, errors = validate_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("Unknown settings field: unknown_field", errors)
    
    def test_integration_complex_config(self):
        """Test validation of complex configuration with multiple rules."""
        complex_config = {
            'rules': [
                {
                    'name': 'Neovim Terminal',
                    'parent': {
                        'app_id': ['neovim', 'nvim'],
                        'class': ['Neovim'],
                        'title_pattern': ['.*neovim.*']
                    },
                    'child': {
                        'app_id': ['kitty', 'alacritty', 'foot']
                    },
                    'actions': [
                        {'set_mode': 'v after'},
                        {'place': 'below'},
                        {'size_ratio': 0.333},
                        {'inherit_cwd': True},
                        {'preserve_column': True}
                    ]
                },
                {
                    'name': 'Browser Side Panel',
                    'parent': {
                        'app_id': ['firefox', 'chrome']
                    },
                    'child': {
                        'app_id': ['obsidian', 'notes']
                    },
                    'actions': [
                        {'set_mode': 'h'},
                        {'place': 'right'},
                        {'size_ratio': 0.2}
                    ]
                }
            ],
            'settings': {
                'debug': True,
                'rule_timeout': 15.5
            }
        }
        
        is_valid, errors = validate_config(complex_config)
        self.assertTrue(is_valid, f"Complex config should be valid, but got errors: {errors}")
        self.assertEqual(errors, [])
    
    def test_integration_error_messages(self):
        """Test that error messages are clear and actionable."""
        invalid_config = {
            'rules': [
                {
                    'name': 'Invalid Rule',
                    'parent': {},  # Empty parent
                    'child': {'app_id': []},  # Empty app_id
                    'actions': [
                        {'invalid_action': 'test'},  # Unknown action
                        {'size_ratio': 1.5}  # Invalid ratio
                    ]
                }
            ]
        }
        
        is_valid, errors = validate_config(invalid_config)
        self.assertFalse(is_valid)
        
        # Check that specific error messages are present
        error_text = ' '.join(errors)
        self.assertIn('parent cannot be empty', error_text)
        self.assertIn('child.app_id cannot be empty', error_text)
        self.assertIn("unknown action type 'invalid_action'", error_text)
        self.assertIn('size_ratio must be between 0.1 and 0.9, got 1.5', error_text)


if __name__ == '__main__':
    unittest.main()