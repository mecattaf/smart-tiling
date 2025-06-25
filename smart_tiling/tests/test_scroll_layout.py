"""
Tests for Scroll layout manipulation module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import uuid

from smart_tiling.scroll.layout import ScrollLayoutManager, create_layout_manager, safe_command
from smart_tiling.core.state import state_manager


class TestScrollLayoutManager(unittest.TestCase):
    """Test cases for ScrollLayoutManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.layout_manager = ScrollLayoutManager()
        self.mock_i3 = Mock()
        self.mock_container = Mock()
        
        # Mock successful command response
        self.mock_success_result = [Mock(success=True)]
        self.mock_failure_result = [Mock(success=False)]
        
        # Setup mock container
        self.mock_container.id = 12345
        self.mock_container.rect = {
            'width': 800,
            'height': 600,
            'x': 100,
            'y': 100
        }
        self.mock_container.parent = Mock()
        self.mock_container.parent.id = 67890
        self.mock_container.parent.rect = {
            'width': 1920,
            'height': 1080,
            'x': 0,
            'y': 0
        }
        self.mock_container.parent.layout = 'horizontal'
        
    def tearDown(self):
        """Clean up after tests."""
        # Clear any stored state
        self.layout_manager._original_modes.clear()
        
    def test_set_mode_horizontal_after(self):
        """Test setting horizontal mode with after modifier."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.set_mode(self.mock_i3, 'h', 'after')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_once_with('set_mode h after')
        
    def test_set_mode_vertical_before(self):
        """Test setting vertical mode with before modifier."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.set_mode(self.mock_i3, 'v', 'before')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_once_with('set_mode v before')
        
    def test_set_mode_no_modifier(self):
        """Test setting mode without modifier."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.set_mode(self.mock_i3, 'h')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_once_with('set_mode h')
        
    def test_set_mode_invalid_mode(self):
        """Test setting invalid mode."""
        result = self.layout_manager.set_mode(self.mock_i3, 'invalid')
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_mode_invalid_modifier(self):
        """Test setting mode with invalid modifier."""
        result = self.layout_manager.set_mode(self.mock_i3, 'h', 'invalid')
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_mode_command_failure(self):
        """Test handling of command execution failure."""
        self.mock_i3.command.return_value = self.mock_failure_result
        
        result = self.layout_manager.set_mode(self.mock_i3, 'h', 'after')
        
        self.assertFalse(result)
        self.mock_i3.command.assert_called_once_with('set_mode h after')
        
    def test_set_mode_exception_handling(self):
        """Test exception handling during mode setting."""
        self.mock_i3.command.side_effect = Exception("IPC error")
        
        result = self.layout_manager.set_mode(self.mock_i3, 'h', 'after')
        
        self.assertFalse(result)
        
    def test_place_window_below(self):
        """Test placing window below (vertical after)."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.place_window(self.mock_i3, 'below')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_with('set_mode v after')
        
    def test_place_window_right(self):
        """Test placing window to the right (horizontal after)."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.place_window(self.mock_i3, 'right')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_with('set_mode h after')
        
    def test_place_window_above(self):
        """Test placing window above (vertical before)."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.place_window(self.mock_i3, 'above')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_with('set_mode v before')
        
    def test_place_window_left(self):
        """Test placing window to the left (horizontal before)."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.place_window(self.mock_i3, 'left')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_with('set_mode h before')
        
    def test_place_window_invalid_direction(self):
        """Test placing window with invalid direction."""
        result = self.layout_manager.place_window(self.mock_i3, 'invalid')
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_size_horizontal(self):
        """Test setting horizontal size."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.set_size(self.mock_i3, 'h', 0.5)
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_once_with('set_size h 0.5')
        
    def test_set_size_vertical(self):
        """Test setting vertical size."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.set_size(self.mock_i3, 'v', 0.333)
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_once_with('set_size v 0.333')
        
    def test_set_size_invalid_dimension(self):
        """Test setting size with invalid dimension."""
        result = self.layout_manager.set_size(self.mock_i3, 'invalid', 0.5)
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_size_ratio_too_small(self):
        """Test setting size with ratio too small."""
        result = self.layout_manager.set_size(self.mock_i3, 'h', 0.05)
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_size_ratio_too_large(self):
        """Test setting size with ratio too large."""
        result = self.layout_manager.set_size(self.mock_i3, 'h', 0.95)
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_set_size_ratio_at_boundaries(self):
        """Test setting size with ratio at valid boundaries."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        # Test lower boundary
        result = self.layout_manager.set_size(self.mock_i3, 'h', 0.1)
        self.assertTrue(result)
        
        # Test upper boundary
        result = self.layout_manager.set_size(self.mock_i3, 'h', 0.9)
        self.assertTrue(result)
        
    def test_preserve_column_split_success(self):
        """Test successful column split preservation."""
        success, dimensions = self.layout_manager.preserve_column_split(
            self.mock_i3, self.mock_container
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(dimensions)
        self.assertEqual(dimensions['width'], 800)
        self.assertEqual(dimensions['height'], 600)
        self.assertEqual(dimensions['parent_width'], 1920)
        self.assertEqual(dimensions['parent_height'], 1080)
        self.assertEqual(dimensions['parent_layout'], 'horizontal')
        
    def test_preserve_column_split_no_container(self):
        """Test column split preservation with no container."""
        success, dimensions = self.layout_manager.preserve_column_split(
            self.mock_i3, None
        )
        
        self.assertFalse(success)
        self.assertIsNone(dimensions)
        
    def test_preserve_column_split_no_parent(self):
        """Test column split preservation with container having no parent."""
        container = Mock()
        container.rect = {'width': 800, 'height': 600, 'x': 100, 'y': 100}
        container.parent = None
        
        success, dimensions = self.layout_manager.preserve_column_split(
            self.mock_i3, container
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(dimensions)
        self.assertEqual(dimensions['width'], 800)
        self.assertEqual(dimensions['height'], 600)
        # Parent dimensions should be 0 when no parent
        self.assertEqual(dimensions.get('parent_width', 0), 0)
        
    @patch('smart_tiling.scroll.layout.state_manager')
    def test_execute_neovim_terminal_placement(self, mock_state_manager):
        """Test the primary use case: Neovim terminal placement."""
        self.mock_i3.command.return_value = self.mock_success_result
        
        # Mock workspace detection
        with patch.object(self.layout_manager, '_get_current_workspace', return_value='workspace1'):
            result = self.layout_manager.execute_neovim_terminal_placement(
                self.mock_i3, self.mock_container, 0.333
            )
        
        self.assertTrue(result)
        
        # Verify set_mode was called for 'below' placement
        expected_calls = [
            unittest.mock.call('set_mode v after'),
            unittest.mock.call(f'[con_id={self.mock_container.parent.id}] mark --add _smart_parent_')
        ]
        
        # Check first call matches (set_mode)
        actual_calls = self.mock_i3.command.call_args_list
        self.assertEqual(actual_calls[0][0][0], 'set_mode v after')
        
        # Check that mark command was called
        self.assertEqual(len(actual_calls), 2)
        self.assertTrue(actual_calls[1][0][0].startswith('[con_id=67890] mark --add _smart_parent_'))
        
        # Verify state was stored
        mock_state_manager.store_pending_rule.assert_called_once()
        
    @patch('smart_tiling.scroll.layout.state_manager')
    def test_apply_terminal_sizing(self, mock_state_manager):
        """Test applying terminal sizing after creation."""
        # Mock pending rule
        mock_pending_rule = {
            'rule': {'type': 'neovim_terminal', 'size_ratio': 0.333},
            'parent_id': 12345,
            'context': {'neovim_container_id': 12345}
        }
        mock_state_manager.get_pending_rule.return_value = mock_pending_rule
        
        self.mock_i3.command.return_value = self.mock_success_result
        
        with patch.object(self.layout_manager, '_get_current_workspace', return_value='workspace1'):
            with patch.object(self.layout_manager, 'restore_original_mode', return_value=True):
                result = self.layout_manager.apply_terminal_sizing(
                    self.mock_i3, self.mock_container
                )
        
        self.assertTrue(result)
        
        # Verify set_size was called
        self.mock_i3.command.assert_called_with('set_size v 0.333')
        
    @patch('smart_tiling.scroll.layout.state_manager')
    def test_apply_terminal_sizing_no_pending_rule(self, mock_state_manager):
        """Test applying terminal sizing when no pending rule exists."""
        mock_state_manager.get_pending_rule.return_value = None
        
        with patch.object(self.layout_manager, '_get_current_workspace', return_value='workspace1'):
            result = self.layout_manager.apply_terminal_sizing(
                self.mock_i3, self.mock_container
            )
        
        self.assertFalse(result)
        self.mock_i3.command.assert_not_called()
        
    def test_restore_original_mode(self):
        """Test restoring original mode."""
        # Store an original mode
        self.layout_manager._original_modes['workspace1'] = 'set_mode h before'
        self.mock_i3.command.return_value = self.mock_success_result
        
        result = self.layout_manager.restore_original_mode(self.mock_i3, 'workspace1')
        
        self.assertTrue(result)
        self.mock_i3.command.assert_called_with('set_mode h before')
        
        # Verify mode was cleaned up
        self.assertNotIn('workspace1', self.layout_manager._original_modes)
        
    def test_restore_original_mode_no_stored_mode(self):
        """Test restoring original mode when none is stored."""
        result = self.layout_manager.restore_original_mode(self.mock_i3, 'workspace1')
        
        self.assertTrue(result)  # Should return True as there's nothing to restore
        self.mock_i3.command.assert_not_called()
        
    def test_get_current_workspace(self):
        """Test getting current workspace."""
        # Mock workspace structure
        mock_workspace = Mock()
        mock_workspace.name = 'workspace1'
        
        mock_focused = Mock()
        mock_focused.workspace.return_value = mock_workspace
        
        mock_tree = Mock()
        mock_tree.find_focused.return_value = mock_focused
        
        self.mock_i3.get_tree.return_value = mock_tree
        
        result = self.layout_manager._get_current_workspace(self.mock_i3)
        
        self.assertEqual(result, 'workspace1')
        
    def test_get_current_workspace_no_focused(self):
        """Test getting current workspace when no focused window."""
        mock_tree = Mock()
        mock_tree.find_focused.return_value = None
        
        self.mock_i3.get_tree.return_value = mock_tree
        
        result = self.layout_manager._get_current_workspace(self.mock_i3)
        
        self.assertIsNone(result)
        
    def test_get_current_mode(self):
        """Test getting current mode (placeholder implementation)."""
        result = self.layout_manager._get_current_mode(self.mock_i3)
        
        # Should return default mode
        self.assertEqual(result, "set_mode h after")
        
    def test_cleanup_expired_modes(self):
        """Test cleanup of expired modes."""
        # Add some modes
        self.layout_manager._original_modes['workspace1'] = 'set_mode h after'
        self.layout_manager._original_modes['workspace2'] = 'set_mode v before'
        
        # Cleanup should not raise exceptions
        self.layout_manager.cleanup_expired_modes()
        
        # For now, modes should still be there (no actual cleanup logic implemented)
        self.assertIn('workspace1', self.layout_manager._original_modes)
        self.assertIn('workspace2', self.layout_manager._original_modes)


class TestModuleFunctions(unittest.TestCase):
    """Test module-level functions."""
    
    def test_create_layout_manager(self):
        """Test creating layout manager instance."""
        manager = create_layout_manager()
        
        self.assertIsInstance(manager, ScrollLayoutManager)
        self.assertEqual(manager._original_modes, {})
        
    def test_safe_command_success(self):
        """Test safe command execution with success."""
        mock_i3 = Mock()
        mock_i3.command.return_value = [Mock(success=True)]
        
        result = safe_command(mock_i3, 'test command')
        
        self.assertTrue(result)
        mock_i3.command.assert_called_once_with('test command')
        
    def test_safe_command_failure(self):
        """Test safe command execution with failure."""
        mock_i3 = Mock()
        mock_i3.command.return_value = [Mock(success=False)]
        
        result = safe_command(mock_i3, 'test command')
        
        self.assertFalse(result)
        mock_i3.command.assert_called_once_with('test command')
        
    def test_safe_command_exception(self):
        """Test safe command execution with exception."""
        mock_i3 = Mock()
        mock_i3.command.side_effect = Exception("IPC error")
        
        result = safe_command(mock_i3, 'test command')
        
        self.assertFalse(result)
        mock_i3.command.assert_called_once_with('test command')
        
    def test_safe_command_empty_result(self):
        """Test safe command execution with empty result."""
        mock_i3 = Mock()
        mock_i3.command.return_value = []
        
        result = safe_command(mock_i3, 'test command')
        
        self.assertFalse(result)
        mock_i3.command.assert_called_once_with('test command')


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios for common use cases."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.layout_manager = ScrollLayoutManager()
        self.mock_i3 = Mock()
        self.mock_i3.command.return_value = [Mock(success=True)]
        
    def test_neovim_terminal_complete_workflow(self):
        """Test complete Neovim→Terminal workflow."""
        # Create mock Neovim container
        neovim_container = Mock()
        neovim_container.id = 12345
        neovim_container.parent = Mock()
        neovim_container.parent.id = 67890
        
        # Create mock terminal container
        terminal_container = Mock()
        terminal_container.id = 54321
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.name = 'workspace1'
        mock_focused = Mock()
        mock_focused.workspace.return_value = mock_workspace
        mock_tree = Mock()
        mock_tree.find_focused.return_value = mock_focused
        self.mock_i3.get_tree.return_value = mock_tree
        
        # Step 1: Execute placement
        with patch('smart_tiling.scroll.layout.state_manager') as mock_state_manager:
            result = self.layout_manager.execute_neovim_terminal_placement(
                self.mock_i3, neovim_container, 0.333
            )
            
            self.assertTrue(result)
            
            # Verify state was stored
            mock_state_manager.store_pending_rule.assert_called_once()
            
            # Step 2: Apply terminal sizing
            mock_pending_rule = {
                'rule': {'type': 'neovim_terminal', 'size_ratio': 0.333},
                'parent_id': 12345,
                'context': {'neovim_container_id': 12345}
            }
            mock_state_manager.get_pending_rule.return_value = mock_pending_rule
            
            result = self.layout_manager.apply_terminal_sizing(
                self.mock_i3, terminal_container
            )
            
            self.assertTrue(result)
        
        # Verify commands were executed
        command_calls = self.mock_i3.command.call_args_list
        
        # Should have at least set_mode and set_size calls
        self.assertGreater(len(command_calls), 2)
        
        # Check for set_mode v after
        set_mode_found = False
        for call in command_calls:
            if call[0][0] == 'set_mode v after':
                set_mode_found = True
                break
        self.assertTrue(set_mode_found, "set_mode v after command not found")
        
        # Check for set_size v 0.333
        set_size_found = False
        for call in command_calls:
            if call[0][0] == 'set_size v 0.333':
                set_size_found = True
                break
        self.assertTrue(set_size_found, "set_size v 0.333 command not found")
        
    def test_error_recovery_workflow(self):
        """Test error recovery and mode restoration."""
        # Mock command failure
        self.mock_i3.command.side_effect = [
            [Mock(success=True)],  # First command succeeds (set_mode)
            Exception("IPC error"),  # Second command fails (mark)
        ]
        
        neovim_container = Mock()
        neovim_container.id = 12345
        neovim_container.parent = Mock()
        neovim_container.parent.id = 67890
        
        with patch.object(self.layout_manager, '_get_current_workspace', return_value='workspace1'):
            result = self.layout_manager.execute_neovim_terminal_placement(
                self.mock_i3, neovim_container
            )
            
            # Should still succeed despite mark command failure
            self.assertTrue(result)
        
        # Verify mode restoration works
        self.layout_manager._original_modes['workspace1'] = 'set_mode h after'
        self.mock_i3.command.side_effect = [Mock(success=True)]
        
        result = self.layout_manager.restore_original_mode(self.mock_i3, 'workspace1')
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()