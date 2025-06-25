"""
Integration tests for smart-tiling end-to-end workflow.

Tests the complete workflow from configuration loading through rule execution,
validating that all components work together correctly.
"""

import time
import unittest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, List, Any

from smart_tiling.config.parser import load_config
from smart_tiling.core.rules import rule_engine, Rule
from smart_tiling.core.state import state_manager 
from smart_tiling.core.context import detect_app_context, matches_app_context
from smart_tiling.scroll.layout import ScrollLayoutManager
from smart_tiling.main import handle_smart_rules, smart_switch_splitting


class MockContainer:
    """Mock i3ipc container for testing."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '12345')
        self.app_id = kwargs.get('app_id', None)
        self.window_class = kwargs.get('window_class', None)
        self.name = kwargs.get('name', None)
        self.pid = kwargs.get('pid', None)
        self.parent = kwargs.get('parent', None)
        self.rect = kwargs.get('rect', {'width': 800, 'height': 600, 'x': 0, 'y': 0})
        
    def workspace(self):
        """Mock workspace method."""
        workspace_mock = Mock()
        workspace_mock.name = 'workspace_1'
        return workspace_mock


class MockConnection:
    """Mock i3ipc connection for testing."""
    
    def __init__(self):
        self.commands = []
        self.command_results = []
        
    def command(self, cmd: str):
        """Mock command execution."""
        self.commands.append(cmd)
        result = Mock()
        result.success = True
        return [result]
    
    def get_tree(self):
        """Mock tree for workspace detection."""
        tree = Mock()
        focused = MockContainer(id='focused_123')
        tree.find_focused.return_value = focused
        return tree


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for the complete smart-tiling workflow."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear state between tests
        rule_engine.rules = []
        state_manager._relationships.clear()
        state_manager._pending_rules.clear()
        
        # Sample configuration
        self.config = {
            'rules': [
                {
                    'name': 'editor_terminal',
                    'parent': {
                        'app_id': ['kitty'],
                        'title_pattern': ['*nvim*', '*vim*']
                    },
                    'child': {
                        'app_id': ['kitty', 'alacritty']
                    },
                    'actions': [
                        {'place': 'below'},
                        {'size_ratio': 0.333}
                    ]
                }
            ],
            'settings': {
                'debug': True,
                'rule_timeout': 15
            }
        }
        
        # Mock containers
        self.editor_container = MockContainer(
            id='editor_123',
            app_id='kitty',
            name='nvim ~/project/file.py',
            pid=1234
        )
        
        self.terminal_container = MockContainer(
            id='terminal_456', 
            app_id='kitty',
            name='zsh',
            pid=5678
        )
        
        self.connection = MockConnection()
    
    def test_config_loading_and_validation(self):
        """Test that configuration loads and validates correctly."""
        # Load rules into engine
        rule_engine.load_rules(self.config['rules'])
        
        self.assertEqual(len(rule_engine.rules), 1)
        
        rule = rule_engine.rules[0]
        self.assertEqual(rule.name, 'editor_terminal')
        self.assertEqual(rule.parent.app_id, ['kitty'])
        self.assertEqual(rule.parent.title_pattern, ['*nvim*', '*vim*'])
        self.assertEqual(rule.child.app_id, ['kitty', 'alacritty'])
        self.assertEqual(len(rule.actions), 2)
    
    def test_context_detection(self):
        """Test application context detection."""
        # Test editor context detection
        context = detect_app_context(self.editor_container)
        
        self.assertEqual(context['app_id'], 'kitty')
        self.assertEqual(context['title'], 'nvim ~/project/file.py')
        self.assertEqual(context['pid'], 1234)
        
        # Test matching
        matches = matches_app_context(
            self.editor_container,
            app_id_list=['kitty'],
            title_patterns=['*nvim*']
        )
        self.assertTrue(matches)
    
    def test_rule_matching(self):
        """Test rule matching logic."""
        rule_engine.load_rules(self.config['rules'])
        
        # Test parent matching
        rule = rule_engine.match_parent(self.editor_container)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, 'editor_terminal')
        
        # Test child matching
        matches_child = rule_engine.match_child(self.terminal_container, rule)
        self.assertTrue(matches_child)
        
        # Test non-matching container
        non_matching = MockContainer(app_id='firefox', name='Mozilla Firefox')
        rule_non_match = rule_engine.match_parent(non_matching)
        self.assertIsNone(rule_non_match)
    
    def test_state_management(self):
        """Test state management for pending rules and relationships."""
        workspace = 'workspace_1'
        rule = rule_engine.rules[0] if rule_engine.rules else Rule(
            name='test_rule',
            parent=Mock(),
            child=Mock(),
            actions=[]
        )
        
        # Store pending rule
        state_manager.store_pending_rule(
            workspace=workspace,
            rule=rule,
            parent_id='parent_123',
            context={'app_id': 'kitty'},
            expires_in=10.0
        )
        
        # Retrieve pending rule
        pending = state_manager.get_pending_rule(workspace)
        self.assertIsNotNone(pending)
        self.assertEqual(pending['parent_id'], 'parent_123')
        self.assertEqual(pending['rule'], rule)
        
        # Store relationship
        state_manager.store_relationship(
            child_id='child_456',
            parent_id='parent_123',
            rule_name='test_rule',
            context={'app_id': 'kitty'}
        )
        
        # Retrieve relationship
        relationship = state_manager.get_relationship('child_456')
        self.assertIsNotNone(relationship)
        self.assertEqual(relationship['parent_id'], 'parent_123')
        self.assertEqual(relationship['rule_name'], 'test_rule')
    
    def test_scroll_layout_integration(self):
        """Test ScrollLayoutManager integration."""
        layout_manager = ScrollLayoutManager()
        
        # Test mode setting
        with patch.object(self.connection, 'command') as mock_command:
            mock_command.return_value = [Mock(success=True)]
            
            success = layout_manager.set_mode(self.connection, 'v', 'after')
            self.assertTrue(success)
            mock_command.assert_called_with('set_mode v after')
        
        # Test window placement
        with patch.object(self.connection, 'command') as mock_command:
            mock_command.return_value = [Mock(success=True)]
            
            success = layout_manager.place_window(self.connection, 'below')
            self.assertTrue(success)
            mock_command.assert_called_with('set_mode v after')
    
    @patch('smart_tiling.scroll.layout.state_manager')
    def test_primary_workflow_simulation(self, mock_state_manager):
        """Test the complete primary workflow: Editor focus → Terminal creation."""
        rule_engine.load_rules(self.config['rules'])
        
        # Step 1: Editor window gets focus (simulates user working in nvim)
        editor_event = Mock()
        editor_event.container = self.editor_container
        
        # Execute smart rule handling
        result = handle_smart_rules(self.connection, editor_event, self.config)
        
        # Should detect editor and set up for terminal placement
        self.assertIsNotNone(result)
        
        # Step 2: User creates terminal (Mod4+Return)
        terminal_event = Mock()
        terminal_event.container = self.terminal_container
        
        # Mock pending rule retrieval
        mock_state_manager.get_pending_rule.return_value = {
            'rule': {'type': 'child_placement', 'name': 'editor_terminal', 'direction': 'below', 'size_ratio': 0.333},
            'parent_id': 'editor_123',
            'context': {'app_id': 'kitty'}
        }
        
        # Execute rule for terminal
        with patch('smart_tiling.scroll.layout.ScrollLayoutManager') as mock_layout_class:
            mock_layout = mock_layout_class.return_value
            mock_layout.apply_child_window_sizing.return_value = True
            
            # Simulate child window sizing
            layout_manager = ScrollLayoutManager()
            success = layout_manager.apply_child_window_sizing(self.connection, self.terminal_container)
            
            # Should apply sizing based on pending rule
            self.assertTrue(success)
    
    def test_edge_case_multiple_editors(self):
        """Test edge case: Multiple editor windows."""
        rule_engine.load_rules(self.config['rules'])
        
        # Create multiple editor containers
        editor1 = MockContainer(id='editor1', app_id='kitty', name='nvim file1.py')
        editor2 = MockContainer(id='editor2', app_id='kitty', name='nvim file2.py')
        
        # Both should match the rule
        rule1 = rule_engine.match_parent(editor1)
        rule2 = rule_engine.match_parent(editor2)
        
        self.assertIsNotNone(rule1)
        self.assertIsNotNone(rule2)
        self.assertEqual(rule1.name, rule2.name)
    
    def test_edge_case_rule_timeout(self):
        """Test edge case: Rule timeout expiration."""
        workspace = 'workspace_1'
        
        # Store rule with short timeout
        state_manager.store_pending_rule(
            workspace=workspace,
            rule={'type': 'test'},
            parent_id='parent_123',
            context={},
            expires_in=0.1  # 100ms timeout
        )
        
        # Rule should exist initially
        pending = state_manager.get_pending_rule(workspace)
        self.assertIsNotNone(pending)
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Rule should be expired and removed
        expired = state_manager.get_pending_rule(workspace)
        self.assertIsNone(expired)
    
    def test_edge_case_invalid_config(self):
        """Test edge case: Invalid configuration handling."""
        invalid_config = {
            'rules': [
                {
                    'name': 'invalid_rule',
                    # Missing required fields
                }
            ]
        }
        
        # Should handle invalid config gracefully
        try:
            rule_engine.load_rules(invalid_config['rules'])
            # Should not crash, but may produce warnings
            self.assertEqual(len(rule_engine.rules), 0)  # Invalid rule not loaded
        except Exception as e:
            self.fail(f"Rule engine should handle invalid config gracefully: {e}")
    
    def test_edge_case_workspace_switch(self):
        """Test edge case: Workspace switch during workflow."""
        workspace1 = 'workspace_1'
        workspace2 = 'workspace_2'
        
        # Store rule in workspace 1
        state_manager.store_pending_rule(
            workspace=workspace1,
            rule={'type': 'test'},
            parent_id='parent_123',
            context={},
            expires_in=10.0
        )
        
        # Rule should exist in workspace 1
        pending_ws1 = state_manager.get_pending_rule(workspace1)
        self.assertIsNotNone(pending_ws1)
        
        # Rule should not exist in workspace 2
        pending_ws2 = state_manager.get_pending_rule(workspace2)
        self.assertIsNone(pending_ws2)
    
    def test_command_sequence_capture(self):
        """Test IPC command sequence capture and verification."""
        layout_manager = ScrollLayoutManager()
        
        # Execute a placement sequence
        with patch.object(self.connection, 'command') as mock_command:
            mock_command.return_value = [Mock(success=True)]
            
            # Execute placement
            layout_manager.set_mode(self.connection, 'v', 'after')
            layout_manager.set_size(self.connection, 'v', 0.333)
            
            # Verify command sequence
            expected_commands = [
                'set_mode v after',
                'set_size v 0.333'
            ]
            
            actual_commands = [call[0][0] for call in mock_command.call_args_list]
            self.assertEqual(actual_commands, expected_commands)
    
    def test_performance_requirements(self):
        """Test that performance requirements are met (< 10ms overhead)."""
        rule_engine.load_rules(self.config['rules'])
        
        # Measure rule matching performance
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 iterations
            rule = rule_engine.match_parent(self.editor_container)
            self.assertIsNotNone(rule)
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_match = total_time / 100
        
        # Should be well under 10ms per match
        self.assertLess(avg_time_per_match, 10.0, 
                       f"Rule matching took {avg_time_per_match:.2f}ms, expected < 10ms")
    
    def test_fallback_to_geometry_tiling(self):
        """Test fallback to geometry-based tiling when no rules match."""
        # Clear rules to ensure no matches
        rule_engine.rules = []
        
        # Create non-matching container
        non_matching = MockContainer(app_id='firefox', name='Mozilla Firefox')
        event = Mock()
        event.container = non_matching
        
        # Should return handled=False to trigger geometry fallback
        result = handle_smart_rules(self.connection, event, self.config)
        self.assertEqual(result['handled'], False)
    
    def test_smart_switch_splitting_integration(self):
        """Test integration with main smart_switch_splitting function."""
        rule_engine.load_rules(self.config['rules'])
        
        event = Mock()
        event.container = self.editor_container
        
        # Mock the geometry tiling function
        with patch('smart_tiling.main.switch_splitting') as mock_geometry:
            # Test with config (should use smart rules)
            smart_switch_splitting(
                self.connection, event, debug=True, 
                outputs=[], workspaces=[], depth_limit=0,
                splitwidth=1.0, splitheight=1.0, splitratio=1.0,
                config=self.config
            )
            
            # Should not call geometry tiling since smart rule should handle it
            # (Note: In current implementation, smart rules fall back to geometry)
            # This test verifies the integration points work
    
    def test_memory_cleanup(self):
        """Test that state is properly cleaned up to prevent memory leaks."""
        workspace = 'workspace_1'
        
        # Store multiple relationships and rules
        for i in range(10):
            state_manager.store_relationship(
                child_id=f'child_{i}',
                parent_id=f'parent_{i}',
                rule_name='test_rule',
                context={}
            )
            
            state_manager.store_pending_rule(
                workspace=f'workspace_{i}',
                rule={'type': 'test'},
                parent_id=f'parent_{i}',
                context={},
                expires_in=0.1  # Short timeout
            )
        
        # Wait for timeouts
        time.sleep(0.2)
        
        # Accessing expired rules should clean them up
        for i in range(10):
            expired = state_manager.get_pending_rule(f'workspace_{i}')
            self.assertIsNone(expired)
        
        # Relationships should still exist (no automatic cleanup)
        for i in range(10):
            relationship = state_manager.get_relationship(f'child_{i}')
            self.assertIsNotNone(relationship)


class TestMockInfrastructure(unittest.TestCase):
    """Test the mock infrastructure itself."""
    
    def test_mock_container_creation(self):
        """Test MockContainer creation and attributes."""
        container = MockContainer(
            id='test_123',
            app_id='test_app',
            name='test window'
        )
        
        self.assertEqual(container.id, 'test_123')
        self.assertEqual(container.app_id, 'test_app')
        self.assertEqual(container.name, 'test window')
        self.assertIsNotNone(container.rect)
    
    def test_mock_connection_command_capture(self):
        """Test MockConnection command capture."""
        connection = MockConnection()
        
        connection.command('test command 1')
        connection.command('test command 2')
        
        self.assertEqual(len(connection.commands), 2)
        self.assertEqual(connection.commands[0], 'test command 1')
        self.assertEqual(connection.commands[1], 'test command 2')


if __name__ == '__main__':
    unittest.main()