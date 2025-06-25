"""
Configuration schema validation for smart-tiling.

This module provides validation functions to ensure YAML configurations
have the correct structure and valid values, preventing runtime errors
from malformed configurations.
"""

import re
from typing import Dict, List, Tuple, Any, Union


def validate_config(config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate entire configuration structure.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(config, dict):
        return False, ["Configuration must be a dictionary"]
    
    # Check for required 'rules' field
    if 'rules' not in config:
        errors.append("Configuration missing required field: rules")
    elif not isinstance(config['rules'], list):
        errors.append("Field 'rules' must be a list")
    else:
        # Validate each rule
        rule_names = set()
        for i, rule in enumerate(config['rules']):
            rule_valid, rule_errors = validate_rule(rule)
            if not rule_valid:
                for error in rule_errors:
                    errors.append(f"Rule {i}: {error}")
            
            # Check for duplicate rule names
            if isinstance(rule, dict) and 'name' in rule:
                rule_name = rule['name']
                if rule_name in rule_names:
                    errors.append(f"Duplicate rule name: '{rule_name}'")
                else:
                    rule_names.add(rule_name)
    
    # Validate optional settings
    if 'settings' in config:
        settings_valid, settings_errors = validate_settings(config['settings'])
        if not settings_valid:
            errors.extend(settings_errors)
    
    return len(errors) == 0, errors


def validate_rule(rule_dict: Dict) -> Tuple[bool, List[str]]:
    """
    Validate individual rule structure.
    
    Args:
        rule_dict: Rule dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(rule_dict, dict):
        return False, ["Rule must be a dictionary"]
    
    # Check required fields
    required_fields = ['name', 'parent', 'child', 'actions']
    for field in required_fields:
        if field not in rule_dict:
            errors.append(f"Rule missing required field: {field}")
    
    # Validate name field
    if 'name' in rule_dict:
        if not isinstance(rule_dict['name'], str):
            errors.append("Rule 'name' must be a string")
        elif not rule_dict['name'].strip():
            errors.append("Rule 'name' cannot be empty")
    
    # Validate parent field
    if 'parent' in rule_dict:
        parent_valid, parent_errors = validate_parent(rule_dict['parent'])
        if not parent_valid:
            for error in parent_errors:
                errors.append(f"parent: {error}")
    
    # Validate child field
    if 'child' in rule_dict:
        child_valid, child_errors = validate_child(rule_dict['child'])
        if not child_valid:
            for error in child_errors:
                errors.append(f"child: {error}")
    
    # Validate actions field
    if 'actions' in rule_dict:
        actions_valid, actions_errors = validate_actions(rule_dict['actions'])
        if not actions_valid:
            for error in actions_errors:
                errors.append(f"actions: {error}")
    
    return len(errors) == 0, errors


def validate_parent(parent: Dict) -> Tuple[bool, List[str]]:
    """
    Validate parent configuration.
    
    Args:
        parent: Parent dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(parent, dict):
        return False, ["parent must be a dictionary"]
    
    if not parent:
        errors.append("parent cannot be empty")
        return False, errors
    
    # Validate optional fields
    valid_fields = ['app_id', 'class', 'title_pattern']
    for field in parent:
        if field not in valid_fields:
            errors.append(f"Unknown parent field: {field}")
        elif not isinstance(parent[field], list):
            errors.append(f"parent.{field} must be a list")
        elif not parent[field]:
            errors.append(f"parent.{field} cannot be empty")
        else:
            # Check that all items in the list are strings
            for i, item in enumerate(parent[field]):
                if not isinstance(item, str):
                    errors.append(f"parent.{field}[{i}] must be a string")
    
    return len(errors) == 0, errors


def validate_child(child: Dict) -> Tuple[bool, List[str]]:
    """
    Validate child configuration.
    
    Args:
        child: Child dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(child, dict):
        return False, ["child must be a dictionary"]
    
    # Check required app_id field
    if 'app_id' not in child:
        errors.append("child missing required field: app_id")
    elif not isinstance(child['app_id'], list):
        errors.append("child.app_id must be a list")
    elif not child['app_id']:
        errors.append("child.app_id cannot be empty")
    else:
        # Check that all items in app_id list are strings
        for i, item in enumerate(child['app_id']):
            if not isinstance(item, str):
                errors.append(f"child.app_id[{i}] must be a string")
    
    # Check for unknown fields
    valid_fields = ['app_id']
    for field in child:
        if field not in valid_fields:
            errors.append(f"Unknown child field: {field}")
    
    return len(errors) == 0, errors


def validate_actions(actions: List) -> Tuple[bool, List[str]]:
    """
    Validate actions list.
    
    Args:
        actions: Actions list to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(actions, list):
        return False, ["actions must be a list"]
    
    if not actions:
        errors.append("actions cannot be empty")
        return False, errors
    
    # Validate each action
    for i, action in enumerate(actions):
        action_valid, action_errors = validate_action(action)
        if not action_valid:
            for error in action_errors:
                errors.append(f"action[{i}]: {error}")
    
    return len(errors) == 0, errors


def validate_action(action: Dict) -> Tuple[bool, List[str]]:
    """
    Validate individual action.
    
    Args:
        action: Action dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(action, dict):
        return False, ["action must be a dictionary"]
    
    if len(action) != 1:
        errors.append("action must contain exactly one key-value pair")
        return False, errors
    
    action_type = list(action.keys())[0]
    action_value = action[action_type]
    
    # Validate based on action type
    if action_type == 'set_mode':
        mode_valid, mode_errors = validate_set_mode(action_value)
        if not mode_valid:
            errors.extend(mode_errors)
    
    elif action_type == 'place':
        place_valid, place_errors = validate_place(action_value)
        if not place_valid:
            errors.extend(place_errors)
    
    elif action_type == 'size_ratio':
        ratio_valid, ratio_errors = validate_size_ratio(action_value)
        if not ratio_valid:
            errors.extend(ratio_errors)
    
    elif action_type == 'inherit_cwd':
        bool_valid, bool_errors = validate_boolean_action(action_value, 'inherit_cwd')
        if not bool_valid:
            errors.extend(bool_errors)
    
    elif action_type == 'preserve_column':
        bool_valid, bool_errors = validate_boolean_action(action_value, 'preserve_column')
        if not bool_valid:
            errors.extend(bool_errors)
    
    else:
        errors.append(f"unknown action type '{action_type}'")
    
    return len(errors) == 0, errors


def validate_set_mode(value: str) -> Tuple[bool, List[str]]:
    """
    Validate set_mode action value.
    
    Args:
        value: set_mode value to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(value, str):
        return False, ["set_mode value must be a string"]
    
    # Valid pattern: mode [modifier]
    # mode: 'h' or 'v'
    # modifier: 'after', 'before', 'end', 'beg'
    pattern = r'^[hv](\s+(after|before|end|beg))?$'
    
    if not re.match(pattern, value.strip()):
        errors.append(f"invalid set_mode format '{value}'. Expected: '<mode> [modifier]' where mode is 'h' or 'v' and modifier is 'after', 'before', 'end', or 'beg'")
    
    return len(errors) == 0, errors


def validate_place(value: str) -> Tuple[bool, List[str]]:
    """
    Validate place action value.
    
    Args:
        value: place value to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(value, str):
        return False, ["place value must be a string"]
    
    valid_directions = ['below', 'right', 'above', 'left']
    if value not in valid_directions:
        errors.append(f"invalid place direction '{value}'. Must be one of: {', '.join(valid_directions)}")
    
    return len(errors) == 0, errors


def validate_size_ratio(value: Union[int, float]) -> Tuple[bool, List[str]]:
    """
    Validate size_ratio action value.
    
    Args:
        value: size_ratio value to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(value, (int, float)):
        return False, ["size_ratio value must be a number"]
    
    if not (0.1 <= value <= 0.9):
        errors.append(f"size_ratio must be between 0.1 and 0.9, got {value}")
    
    return len(errors) == 0, errors


def validate_boolean_action(value: bool, action_name: str) -> Tuple[bool, List[str]]:
    """
    Validate boolean action value.
    
    Args:
        value: boolean value to validate
        action_name: name of the action for error messages
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(value, bool):
        errors.append(f"{action_name} value must be a boolean")
    
    return len(errors) == 0, errors


def validate_settings(settings: Dict) -> Tuple[bool, List[str]]:
    """
    Validate settings configuration.
    
    Args:
        settings: Settings dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(settings, dict):
        return False, ["settings must be a dictionary"]
    
    # Validate optional fields
    if 'debug' in settings:
        if not isinstance(settings['debug'], bool):
            errors.append("settings.debug must be a boolean")
    
    if 'rule_timeout' in settings:
        if not isinstance(settings['rule_timeout'], (int, float)):
            errors.append("settings.rule_timeout must be a number")
        elif settings['rule_timeout'] <= 0:
            errors.append("settings.rule_timeout must be greater than 0")
    
    # Check for unknown fields
    valid_fields = ['debug', 'rule_timeout']
    for field in settings:
        if field not in valid_fields:
            errors.append(f"Unknown settings field: {field}")
    
    return len(errors) == 0, errors