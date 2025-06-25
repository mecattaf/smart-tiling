"""
Configuration parser for smart-tiling YAML rules.

This module provides functionality to load and parse YAML configuration files
with support for default paths and graceful error handling.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from .schema import validate_config


def parse_yaml_file(path: str) -> Dict[str, Any]:
    """
    Load and parse YAML file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If YAML syntax is invalid
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {path}: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Unexpected error reading {path}: {e}", file=sys.stderr)
        raise


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        path: Optional path to YAML file. If not provided, checks default locations:
            - ~/.config/smart-tiling/rules.yaml
            - ~/.config/smart-tiling/config.yaml  
            - /etc/smart-tiling/config.yaml
            
    Returns:
        Parsed configuration dictionary, or empty dict if no config found
    """
    config = {}
    config_source = None
    
    if path:
        # Use provided path
        try:
            config = parse_yaml_file(path)
            config_source = path
        except FileNotFoundError:
            print(f"Config file not found: {path}", file=sys.stderr)
            return {}
        except yaml.YAMLError:
            # Error already printed in parse_yaml_file
            return {}
        except Exception:
            # Error already printed in parse_yaml_file
            return {}
    else:
        # Check default locations
        default_paths = [
            Path.home() / ".config" / "smart-tiling" / "rules.yaml",
            Path.home() / ".config" / "smart-tiling" / "config.yaml",
            Path("/etc/smart-tiling/config.yaml"),
        ]
        
        for config_path in default_paths:
            if config_path.exists():
                try:
                    config = parse_yaml_file(str(config_path))
                    config_source = str(config_path)
                    break
                except yaml.YAMLError:
                    # Error already printed in parse_yaml_file, continue to next path
                    continue
                except Exception:
                    # Error already printed in parse_yaml_file, continue to next path
                    continue
    
    # Validate configuration if we successfully loaded one
    if config and config_source:
        is_valid, validation_errors = validate_config(config)
        if not is_valid:
            print(f"Configuration validation warnings for {config_source}:", file=sys.stderr)
            for error in validation_errors:
                print(f"  - {error}", file=sys.stderr)
            print("Configuration loaded with warnings - some features may not work correctly.", file=sys.stderr)
    
    return config