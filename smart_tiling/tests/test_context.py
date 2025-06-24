"""
Tests for context detection module.
"""

import unittest
from unittest.mock import Mock
from smart_tiling.core.context import (
    detect_app_context,
    extract_app_id,
    extract_window_class,
    match_title_pattern,
    matches_app_context
)


class TestContextDetection(unittest.TestCase):
    """Test cases for context detection functions."""

    def test_extract_app_id(self):
        """Test app_id extraction from containers."""
        # Test with app_id present
        container = Mock(app_id='kitty')
        self.assertEqual(extract_app_id(container), 'kitty')
        
        # Test with no app_id
        container = Mock()
        del container.app_id
        self.assertIsNone(extract_app_id(container))

    def test_extract_window_class_string(self):
        """Test window class extraction when it's a string."""
        container = Mock(window_class='Terminal')
        self.assertEqual(extract_window_class(container), 'Terminal')

    def test_extract_window_class_list(self):
        """Test window class extraction when it's a list (X11 format)."""
        # Test with [instance, class] format
        container = Mock(window_class=['kitty', 'kitty'])
        self.assertEqual(extract_window_class(container), 'kitty')
        
        # Test with empty list
        container = Mock(window_class=[])
        self.assertIsNone(extract_window_class(container))

    def test_extract_window_class_none(self):
        """Test window class extraction when None."""
        container = Mock()
        del container.window_class
        self.assertIsNone(extract_window_class(container))

    def test_match_title_pattern_basic(self):
        """Test basic title pattern matching."""
        # Test matching patterns
        self.assertTrue(match_title_pattern('nvim file.py', ['*nvim*']))
        self.assertTrue(match_title_pattern('NVIM', ['*nvim*']))  # Case insensitive
        self.assertTrue(match_title_pattern('vim ~/.bashrc', ['*vim*']))
        
        # Test non-matching patterns
        self.assertFalse(match_title_pattern('nano file.txt', ['*nvim*']))

    def test_match_title_pattern_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = ['*nvim*', '*vim*', '*emacs*']
        
        self.assertTrue(match_title_pattern('nvim config.py', patterns))
        self.assertTrue(match_title_pattern('vim .vimrc', patterns))
        self.assertTrue(match_title_pattern('emacs init.el', patterns))
        self.assertFalse(match_title_pattern('nano file.txt', patterns))

    def test_match_title_pattern_edge_cases(self):
        """Test edge cases for pattern matching."""
        # Test with None title
        self.assertFalse(match_title_pattern(None, ['*nvim*']))
        
        # Test with empty patterns
        self.assertFalse(match_title_pattern('nvim file.py', []))
        
        # Test with None in patterns
        self.assertFalse(match_title_pattern('nvim file.py', [None, '*vim*']))

    def test_detect_app_context_wayland(self):
        """Test context detection for Wayland applications."""
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim ~/project/file.py',
            pid=12345
        )
        del container.window_class
        
        context = detect_app_context(container)
        
        expected = {
            'app_id': 'kitty',
            'window_class': None,
            'window_instance': None,
            'title': 'nvim ~/project/file.py',
            'pid': 12345
        }
        self.assertEqual(context, expected)

    def test_detect_app_context_x11(self):
        """Test context detection for X11 applications."""
        container = Mock(
            app_id=None,
            window_class=['kitty', 'kitty'],
            name='vim ~/.vimrc',
            pid=54321
        )
        del container.app_id
        
        context = detect_app_context(container)
        
        expected = {
            'app_id': None,
            'window_class': 'kitty',
            'window_instance': 'kitty',
            'title': 'vim ~/.vimrc',
            'pid': 54321
        }
        self.assertEqual(context, expected)

    def test_matches_app_context_app_id(self):
        """Test matching by app_id."""
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim file.py',
            pid=12345
        )
        del container.window_class
        
        # Should match
        self.assertTrue(matches_app_context(
            container, 
            app_id_list=['kitty', 'alacritty']
        ))
        
        # Should not match
        self.assertFalse(matches_app_context(
            container,
            app_id_list=['firefox', 'chrome']
        ))

    def test_matches_app_context_window_class(self):
        """Test matching by window class."""
        container = Mock(
            app_id=None,
            window_class=['Terminal', 'xterm'],
            name='bash',
            pid=12345
        )
        del container.app_id
        
        # Should match
        self.assertTrue(matches_app_context(
            container,
            window_class_list=['Terminal', 'kitty']
        ))
        
        # Should not match
        self.assertFalse(matches_app_context(
            container,
            window_class_list=['Firefox', 'Chrome']
        ))

    def test_matches_app_context_title_patterns(self):
        """Test matching by title patterns."""
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim ~/project/main.py',
            pid=12345
        )
        del container.window_class
        
        # Should match
        self.assertTrue(matches_app_context(
            container,
            title_patterns=['*nvim*', '*vim*']
        ))
        
        # Should not match
        self.assertFalse(matches_app_context(
            container,
            title_patterns=['*nano*', '*emacs*']
        ))

    def test_matches_app_context_multiple_criteria(self):
        """Test matching with multiple criteria (OR logic)."""
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim file.py',
            pid=12345
        )
        del container.window_class
        
        # Should match on app_id even if title doesn't match
        self.assertTrue(matches_app_context(
            container,
            app_id_list=['kitty'],
            title_patterns=['*nano*']  # This won't match
        ))
        
        # Should match on title even if app_id doesn't match
        self.assertTrue(matches_app_context(
            container,
            app_id_list=['firefox'],  # This won't match
            title_patterns=['*nvim*']
        ))

    def test_matches_app_context_no_criteria(self):
        """Test behavior with no matching criteria."""
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim file.py',
            pid=12345
        )
        del container.window_class
        
        # Should not match if no criteria provided
        self.assertFalse(matches_app_context(container))
        
        # Should not match if criteria don't match
        self.assertFalse(matches_app_context(
            container,
            app_id_list=['firefox'],
            window_class_list=['Chrome'],
            title_patterns=['*nano*']
        ))

    def test_primary_use_case_kitty_neovim(self):
        """Test the primary use case: Kitty terminal with Neovim running."""
        # This is the main use case specified in the issue
        container = Mock(
            app_id='kitty',
            window_class=None,
            name='nvim ~/project/file.py',
            pid=12345
        )
        del container.window_class
        
        # This should work as specified in the issue
        result = matches_app_context(
            container,
            app_id_list=['kitty'],
            title_patterns=['*nvim*']
        )
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()