"""
Tests for rule engine module.
"""

import unittest
import time
from unittest.mock import Mock, patch
from smart_tiling.core.rules import (
    ParentMatcher,
    ChildMatcher,
    Rule,
    RuleEngine,
    rule_engine
)


class TestDataClasses(unittest.TestCase):
    """Test the rule engine data classes."""
    
    def test_parent_matcher_defaults(self):
        """Test ParentMatcher with default values."""
        matcher = ParentMatcher()
        self.assertEqual(matcher.app_id, [])
        self.assertEqual(matcher.window_class, [])
        self.assertEqual(matcher.title_pattern, [])
    
    def test_parent_matcher_with_values(self):
        """Test ParentMatcher with specific values."""
        matcher = ParentMatcher(
            app_id=['kitty'],
            window_class=['Terminal'], 
            title_pattern=['*nvim*']
        )
        self.assertEqual(matcher.app_id, ['kitty'])
        self.assertEqual(matcher.window_class, ['Terminal'])
        self.assertEqual(matcher.title_pattern, ['*nvim*'])
    
    def test_child_matcher_defaults(self):
        """Test ChildMatcher with default values."""
        matcher = ChildMatcher()
        self.assertEqual(matcher.app_id, [])
    
    def test_child_matcher_with_values(self):
        """Test ChildMatcher with specific values."""
        matcher = ChildMatcher(app_id=['terminal'])
        self.assertEqual(matcher.app_id, ['terminal'])
    
    def test_rule_creation(self):
        """Test Rule object creation."""
        parent = ParentMatcher(app_id=['kitty'], title_pattern=['*nvim*'])
        child = ChildMatcher(app_id=['terminal'])
        actions = [{'action': 'place', 'direction': 'below'}]
        
        rule = Rule(name='test_rule', parent=parent, child=child, actions=actions)
        
        self.assertEqual(rule.name, 'test_rule')
        self.assertEqual(rule.parent, parent)
        self.assertEqual(rule.child, child)
        self.assertEqual(rule.actions, actions)


class TestRuleEngine(unittest.TestCase):
    """Test the RuleEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()
    
    def test_ensure_list_string(self):
        """Test _ensure_list with string input."""
        result = self.engine._ensure_list('kitty')
        self.assertEqual(result, ['kitty'])
    
    def test_ensure_list_list(self):
        """Test _ensure_list with list input."""
        result = self.engine._ensure_list(['kitty', 'alacritty'])
        self.assertEqual(result, ['kitty', 'alacritty'])
    
    def test_ensure_list_none(self):
        """Test _ensure_list with None input."""
        result = self.engine._ensure_list(None)
        self.assertEqual(result, [])
    
    def test_ensure_list_number(self):
        """Test _ensure_list with number input."""
        result = self.engine._ensure_list(123)
        self.assertEqual(result, ['123'])
    
    def test_parse_string_action_set_mode(self):
        """Test parsing set_mode string action."""
        result = self.engine._parse_string_action('set_mode: v after')
        expected = {'action': 'set_mode', 'mode': 'v', 'modifier': 'after'}
        self.assertEqual(result, expected)
    
    def test_parse_string_action_place(self):
        """Test parsing place string action."""
        result = self.engine._parse_string_action('place: below')
        expected = {'action': 'place', 'direction': 'below'}
        self.assertEqual(result, expected)
    
    def test_parse_dict_action_size_ratio(self):
        """Test parsing size_ratio dict action."""
        result = self.engine._parse_dict_action('size_ratio', '0.333')
        expected = {'action': 'size_ratio', 'value': 0.333}
        self.assertEqual(result, expected)
    
    def test_parse_dict_action_inherit_cwd_true(self):
        """Test parsing inherit_cwd dict action (true)."""
        result = self.engine._parse_dict_action('inherit_cwd', 'true')
        expected = {'action': 'inherit_cwd', 'enabled': True}
        self.assertEqual(result, expected)
    
    def test_parse_dict_action_preserve_column_false(self):
        """Test parsing preserve_column dict action (false)."""
        result = self.engine._parse_dict_action('preserve_column', 'false')
        expected = {'action': 'preserve_column', 'enabled': False}
        self.assertEqual(result, expected)
    
    def test_parse_dict_action_generic(self):
        """Test parsing generic dict action."""
        result = self.engine._parse_dict_action('custom_action', 'custom_value')
        expected = {'action': 'custom_action', 'value': 'custom_value'}
        self.assertEqual(result, expected)
    
    def test_parse_rule_complete(self):
        """Test parsing a complete rule dictionary."""
        rule_dict = {
            'name': 'neovim_terminal',
            'parent': {
                'app_id': ['kitty'],
                'class': ['Terminal'],
                'title_pattern': ['*nvim*']
            },
            'child': {
                'app_id': ['terminal']
            },
            'actions': [
                'place: below',
                {'size_ratio': 0.333},
                'inherit_cwd: true'
            ]
        }
        
        rule = self.engine._parse_rule(rule_dict)
        
        self.assertEqual(rule.name, 'neovim_terminal')
        self.assertEqual(rule.parent.app_id, ['kitty'])
        self.assertEqual(rule.parent.window_class, ['Terminal'])
        self.assertEqual(rule.parent.title_pattern, ['*nvim*'])
        self.assertEqual(rule.child.app_id, ['terminal'])
        
        expected_actions = [
            {'action': 'place', 'direction': 'below'},
            {'action': 'size_ratio', 'value': 0.333},
            {'action': 'inherit_cwd', 'enabled': True}
        ]
        self.assertEqual(rule.actions, expected_actions)
    
    def test_load_rules_success(self):
        """Test successful rule loading."""
        rules_list = [
            {
                'name': 'test_rule',
                'parent': {'app_id': 'kitty'},
                'child': {'app_id': 'terminal'},
                'actions': ['place: below']
            }
        ]
        
        self.engine.load_rules(rules_list)
        
        self.assertEqual(len(self.engine.rules), 1)
        self.assertEqual(self.engine.rules[0].name, 'test_rule')
    
    def test_load_rules_error_handling(self):
        """Test rule loading with invalid rules."""
        rules_list = [
            {'name': 'valid_rule', 'parent': {}, 'child': {}, 'actions': []},
            {'invalid': 'rule'},  # This should cause an error
            {'name': 'another_valid', 'parent': {}, 'child': {}, 'actions': []}
        ]
        
        # Should not raise exception, but should skip invalid rule
        self.engine.load_rules(rules_list)
        
        # Should load 2 valid rules, skip the invalid one
        self.assertEqual(len(self.engine.rules), 2)
        rule_names = [rule.name for rule in self.engine.rules]
        self.assertIn('valid_rule', rule_names)
        self.assertIn('another_valid', rule_names)


class TestRuleMatching(unittest.TestCase):
    """Test rule matching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()
        
        # Load test rules
        rules = [
            {
                'name': 'neovim_terminal',
                'parent': {
                    'app_id': ['kitty'],
                    'title_pattern': ['*nvim*']
                },
                'child': {
                    'app_id': ['terminal']
                },
                'actions': [{'place': 'below'}]
            }
        ]
        self.engine.load_rules(rules)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_match_parent_success(self, mock_matches):
        """Test successful parent matching."""
        mock_matches.return_value = True
        container = Mock(app_id='kitty', name='nvim file.py')
        
        result = self.engine.match_parent(container)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'neovim_terminal')
        mock_matches.assert_called_once()
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_match_parent_no_match(self, mock_matches):
        """Test parent matching with no matches."""
        mock_matches.return_value = False
        container = Mock(app_id='firefox', name='Browser')
        
        result = self.engine.match_parent(container)
        
        self.assertIsNone(result)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_match_child_success(self, mock_matches):
        """Test successful child matching."""
        mock_matches.return_value = True
        container = Mock(app_id='terminal')
        rule = self.engine.rules[0]
        
        result = self.engine.match_child(container, rule)
        
        self.assertTrue(result)
        mock_matches.assert_called_once_with(
            container,
            app_id_list=['terminal']
        )
    
    def test_match_child_no_criteria(self):
        """Test child matching with no criteria (should match any)."""
        container = Mock(app_id='anything')
        
        # Create rule with empty child criteria
        rule = Rule(
            name='test',
            parent=ParentMatcher(),
            child=ChildMatcher(),
            actions=[]
        )
        
        result = self.engine.match_child(container, rule)
        
        self.assertTrue(result)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_should_apply_rule_success(self, mock_matches):
        """Test successful full rule matching."""
        mock_matches.side_effect = [True, True]  # Parent match, then child match
        
        parent_container = Mock(app_id='kitty', name='nvim file.py')
        child_container = Mock(app_id='terminal')
        
        result = self.engine.should_apply_rule(parent_container, child_container)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'neovim_terminal')
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_should_apply_rule_parent_no_match(self, mock_matches):
        """Test rule matching when parent doesn't match."""
        mock_matches.return_value = False
        
        parent_container = Mock(app_id='firefox')
        child_container = Mock(app_id='terminal')
        
        result = self.engine.should_apply_rule(parent_container, child_container)
        
        self.assertIsNone(result)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_should_apply_rule_child_no_match(self, mock_matches):
        """Test rule matching when child doesn't match."""
        mock_matches.side_effect = [True, False]  # Parent matches, child doesn't
        
        parent_container = Mock(app_id='kitty', name='nvim file.py')
        child_container = Mock(app_id='firefox')
        
        result = self.engine.should_apply_rule(parent_container, child_container)
        
        self.assertIsNone(result)


class TestRuleState(unittest.TestCase):
    """Test rule state management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()
        
        # Load test rule
        rules = [
            {
                'name': 'test_rule',
                'parent': {'app_id': ['kitty']},
                'child': {'app_id': ['terminal']},
                'actions': [{'place': 'below'}]
            }
        ]
        self.engine.load_rules(rules)
        
        # Clear any existing state
        from smart_tiling.core.state import state_manager
        state_manager._pending_rules.clear()
    
    @patch('smart_tiling.core.rules.detect_app_context')
    def test_store_pending_rule(self, mock_detect):
        """Test storing a pending rule."""
        mock_detect.return_value = {'app_id': 'kitty', 'title': 'nvim file.py'}
        
        rule = self.engine.rules[0]
        parent_container = Mock(id='parent_123', app_id='kitty')
        
        self.engine.store_pending_rule('workspace_1', rule, parent_container)
        
        result = self.engine.get_pending_rule('workspace_1')
        self.assertIsNotNone(result)
        self.assertEqual(result['rule'], rule)
        self.assertEqual(result['parent_id'], 'parent_123')
    
    def test_get_pending_rule_not_found(self):
        """Test getting pending rule when none exists."""
        result = self.engine.get_pending_rule('nonexistent_workspace')
        self.assertIsNone(result)
    
    def test_get_pending_rule_expired(self):
        """Test getting expired pending rule."""
        rule = self.engine.rules[0]
        parent_container = Mock(id='parent_123')
        
        # Store rule with very short expiration
        self.engine.store_pending_rule('workspace_1', rule, parent_container, expires_in=0.1)
        
        # Wait for expiration
        time.sleep(0.2)
        
        result = self.engine.get_pending_rule('workspace_1')
        self.assertIsNone(result)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    @patch('smart_tiling.core.rules.detect_app_context')
    def test_check_child_against_pending_rules_match(self, mock_detect, mock_matches):
        """Test checking child against pending rules with match."""
        mock_detect.return_value = {'app_id': 'kitty'}
        mock_matches.return_value = True
        
        # Store a pending rule
        rule = self.engine.rules[0]
        parent_container = Mock(id='parent_123')
        self.engine.store_pending_rule('workspace_1', rule, parent_container)
        
        # Check child container
        child_container = Mock(id='child_456', app_id='terminal')
        result = self.engine.check_child_against_pending_rules(child_container, 'workspace_1')
        
        self.assertIsNotNone(result)
        self.assertEqual(result, rule)
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_check_child_against_pending_rules_no_match(self, mock_matches):
        """Test checking child against pending rules with no match."""
        mock_matches.return_value = False
        
        # Store a pending rule
        rule = self.engine.rules[0]
        parent_container = Mock(id='parent_123')
        self.engine.store_pending_rule('workspace_1', rule, parent_container)
        
        # Check child container that doesn't match
        child_container = Mock(id='child_456', app_id='firefox')
        result = self.engine.check_child_against_pending_rules(child_container, 'workspace_1')
        
        self.assertIsNone(result)


class TestPrimaryUseCase(unittest.TestCase):
    """Test the primary use case: Neovim→Terminal rule matching."""
    
    def setUp(self):
        """Set up the primary use case rule."""
        self.engine = RuleEngine()
        
        # Primary use case rule: Neovim parent → Terminal child
        neovim_rule = {
            'name': 'neovim_terminal',
            'parent': {
                'app_id': ['kitty', 'alacritty'],
                'title_pattern': ['*nvim*', '*vim*']
            },
            'child': {
                'app_id': ['kitty', 'alacritty', 'terminal']
            },
            'actions': [
                {'place': 'below'},
                {'size_ratio': 0.333},
                {'inherit_cwd': True}
            ]
        }
        
        self.engine.load_rules([neovim_rule])
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_neovim_terminal_workflow(self, mock_matches):
        """Test the complete Neovim→Terminal workflow."""
        # Simulate parent matching (Kitty with Neovim)
        mock_matches.return_value = True
        
        parent_container = Mock(
            id='kitty_nvim_123',
            app_id='kitty',
            name='nvim ~/project/main.py'
        )
        
        # Step 1: Match parent container
        matched_rule = self.engine.match_parent(parent_container)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule.name, 'neovim_terminal')
        
        # Step 2: Store as pending rule
        self.engine.store_pending_rule('workspace_1', matched_rule, parent_container)
        
        # Step 3: New terminal appears, check against pending rules
        child_container = Mock(
            id='terminal_456', 
            app_id='kitty'
        )
        
        matched_child_rule = self.engine.check_child_against_pending_rules(
            child_container, 'workspace_1'
        )
        
        self.assertIsNotNone(matched_child_rule)
        self.assertEqual(matched_child_rule.name, 'neovim_terminal')
        
        # Verify expected actions
        expected_actions = [
            {'action': 'place', 'direction': 'below'},
            {'action': 'size_ratio', 'value': 0.333},
            {'action': 'inherit_cwd', 'value': True}
        ]
        
        self.assertEqual(len(matched_child_rule.actions), 3)
        self.assertEqual(matched_child_rule.actions[0]['action'], 'place')
        self.assertEqual(matched_child_rule.actions[1]['action'], 'size_ratio')
        self.assertEqual(matched_child_rule.actions[2]['action'], 'inherit_cwd')
    
    @patch('smart_tiling.core.rules.matches_app_context')
    def test_rule_expiration(self, mock_matches):
        """Test that rules expire after timeout."""
        mock_matches.return_value = True
        
        parent_container = Mock(id='kitty_nvim_123', app_id='kitty')
        matched_rule = self.engine.match_parent(parent_container)
        
        # Store with short expiration
        self.engine.store_pending_rule('workspace_1', matched_rule, parent_container, expires_in=0.1)
        
        # Verify rule exists initially
        pending = self.engine.get_pending_rule('workspace_1')
        self.assertIsNotNone(pending)
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Verify rule has expired
        expired = self.engine.get_pending_rule('workspace_1')
        self.assertIsNone(expired)
    
    def test_action_parsing_comprehensive(self):
        """Test comprehensive action parsing for the primary use case."""
        rule_dict = {
            'name': 'comprehensive_test',
            'parent': {'app_id': ['kitty']},
            'child': {'app_id': ['terminal']},
            'actions': [
                'set_mode: v after',
                'place: below',
                {'size_ratio': '0.333'},
                {'inherit_cwd': 'true'},
                {'preserve_column': 'false'},
                'custom_action: custom_value'
            ]
        }
        
        rule = self.engine._parse_rule(rule_dict)
        
        expected_actions = [
            {'action': 'set_mode', 'mode': 'v', 'modifier': 'after'},
            {'action': 'place', 'direction': 'below'},
            {'action': 'size_ratio', 'value': 0.333},
            {'action': 'inherit_cwd', 'enabled': True},
            {'action': 'preserve_column', 'enabled': False},
            {'action': 'custom_action', 'value': 'custom_value'}
        ]
        
        self.assertEqual(rule.actions, expected_actions)


if __name__ == '__main__':
    unittest.main()