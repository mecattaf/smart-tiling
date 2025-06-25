"""
Tests for the config parser module.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

import yaml

from smart_tiling.config.parser import load_config, parse_yaml_file


class TestConfigParser(unittest.TestCase):
    """Test cases for config parser functionality."""
    
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
        
        self.valid_yaml = yaml.dump(self.valid_config)
    
    def test_parse_yaml_file_valid(self):
        """Test parsing a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(self.valid_yaml)
            temp_path = f.name
        
        try:
            result = parse_yaml_file(temp_path)
            self.assertEqual(result, self.valid_config)
        finally:
            os.unlink(temp_path)
    
    def test_parse_yaml_file_empty(self):
        """Test parsing an empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name
        
        try:
            result = parse_yaml_file(temp_path)
            self.assertEqual(result, {})
        finally:
            os.unlink(temp_path)
    
    def test_parse_yaml_file_not_found(self):
        """Test parsing a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            parse_yaml_file('/nonexistent/path/config.yaml')
    
    def test_parse_yaml_file_invalid_syntax(self):
        """Test parsing a file with invalid YAML syntax."""
        invalid_yaml = "key: value\n  invalid indentation"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            with self.assertRaises(yaml.YAMLError):
                parse_yaml_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_config_with_valid_path(self):
        """Test loading config with a provided valid path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(self.valid_yaml)
            temp_path = f.name
        
        try:
            result = load_config(temp_path)
            self.assertEqual(result, self.valid_config)
        finally:
            os.unlink(temp_path)
    
    def test_load_config_with_invalid_path(self):
        """Test loading config with a non-existent path."""
        result = load_config('/nonexistent/path/config.yaml')
        self.assertEqual(result, {})
    
    def test_load_config_with_invalid_yaml(self):
        """Test loading config with invalid YAML syntax."""
        invalid_yaml = "key: value\n  invalid indentation"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            result = load_config(temp_path)
            self.assertEqual(result, {})
        finally:
            os.unlink(temp_path)
    
    @patch('smart_tiling.config.parser.Path.home')
    @patch('pathlib.Path.exists')
    def test_load_config_default_paths_rules_yaml(self, mock_exists, mock_home):
        """Test loading config from default rules.yaml location."""
        mock_home.return_value = Path('/home/testuser')
        
        def exists_side_effect(path_obj):
            return str(path_obj) == '/home/testuser/.config/smart-tiling/rules.yaml'
        
        mock_exists.side_effect = exists_side_effect
        
        with patch('smart_tiling.config.parser.parse_yaml_file') as mock_parse:
            mock_parse.return_value = self.valid_config
            
            result = load_config()
            
            mock_parse.assert_called_once_with('/home/testuser/.config/smart-tiling/rules.yaml')
            self.assertEqual(result, self.valid_config)
    
    @patch('smart_tiling.config.parser.Path.home')
    @patch('pathlib.Path.exists')
    def test_load_config_default_paths_config_yaml(self, mock_exists, mock_home):
        """Test loading config from default config.yaml location."""
        mock_home.return_value = Path('/home/testuser')
        
        def exists_side_effect(path_obj):
            return str(path_obj) == '/home/testuser/.config/smart-tiling/config.yaml'
        
        mock_exists.side_effect = exists_side_effect
        
        with patch('smart_tiling.config.parser.parse_yaml_file') as mock_parse:
            mock_parse.return_value = self.valid_config
            
            result = load_config()
            
            mock_parse.assert_called_once_with('/home/testuser/.config/smart-tiling/config.yaml')
            self.assertEqual(result, self.valid_config)
    
    @patch('smart_tiling.config.parser.Path.home')
    @patch('pathlib.Path.exists')
    def test_load_config_default_paths_etc(self, mock_exists, mock_home):
        """Test loading config from /etc location."""
        mock_home.return_value = Path('/home/testuser')
        
        def exists_side_effect(path_obj):
            return str(path_obj) == '/etc/smart-tiling/config.yaml'
        
        mock_exists.side_effect = exists_side_effect
        
        with patch('smart_tiling.config.parser.parse_yaml_file') as mock_parse:
            mock_parse.return_value = self.valid_config
            
            result = load_config()
            
            mock_parse.assert_called_once_with('/etc/smart-tiling/config.yaml')
            self.assertEqual(result, self.valid_config)
    
    @patch('smart_tiling.config.parser.Path.home')
    @patch('pathlib.Path.exists')
    def test_load_config_no_default_paths(self, mock_exists, mock_home):
        """Test loading config when no default paths exist."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = False
        
        result = load_config()
        self.assertEqual(result, {})
    
    @patch('smart_tiling.config.parser.Path.home')
    @patch('pathlib.Path.exists')
    def test_load_config_default_path_with_yaml_error(self, mock_exists, mock_home):
        """Test loading config when default path has YAML error - should continue to next path."""
        mock_home.return_value = Path('/home/testuser')
        
        def exists_side_effect(path_obj):
            return str(path_obj) in [
                '/home/testuser/.config/smart-tiling/rules.yaml',
                '/home/testuser/.config/smart-tiling/config.yaml'
            ]
        
        mock_exists.side_effect = exists_side_effect
        
        with patch('smart_tiling.config.parser.parse_yaml_file') as mock_parse:
            # First call raises YAMLError, second call succeeds
            mock_parse.side_effect = [yaml.YAMLError("Invalid YAML"), self.valid_config]
            
            result = load_config()
            
            # Should have called parse_yaml_file twice
            self.assertEqual(mock_parse.call_count, 2)
            self.assertEqual(result, self.valid_config)
    
    def test_load_config_empty_config(self):
        """Test loading an empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name
        
        try:
            result = load_config(temp_path)
            self.assertEqual(result, {})
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()