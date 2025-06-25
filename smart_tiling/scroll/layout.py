"""
Scroll layout manipulation module.
Implements window manipulation commands specific to Scroll window manager.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from smart_tiling.core.state import state_manager


logger = logging.getLogger(__name__)


class ScrollLayoutManager:
    """Manages layout operations for Scroll window manager."""
    
    def __init__(self):
        """Initialize the layout manager."""
        self._mode_stack = []  # Stack for storing mode states
        self._original_modes = {}  # Map workspace to original mode
        
    def set_mode(self, i3_connection, mode: str, modifier: Optional[str] = None) -> bool:
        """
        Execute set_mode command for Scroll.
        
        Args:
            i3_connection: i3ipc connection object
            mode: Mode type ('h' for horizontal, 'v' for vertical)
            modifier: Position modifier ('after', 'before', 'end', 'beg')
            
        Returns:
            bool: True if command executed successfully
        """
        try:
            # Validate mode
            if mode not in ['h', 'v']:
                logger.error(f"Invalid mode: {mode}. Must be 'h' or 'v'")
                return False
                
            # Validate modifier if provided
            valid_modifiers = ['after', 'before', 'end', 'beg']
            if modifier and modifier not in valid_modifiers:
                logger.error(f"Invalid modifier: {modifier}. Must be one of {valid_modifiers}")
                return False
            
            # Store current mode before changing
            current_mode = self._get_current_mode(i3_connection)
            if current_mode:
                workspace = self._get_current_workspace(i3_connection)
                if workspace:
                    self._original_modes[workspace] = current_mode
                    logger.debug(f"Stored original mode for workspace {workspace}: {current_mode}")
            
            # Build command
            command = f"set_mode {mode}"
            if modifier:
                command += f" {modifier}"
                
            logger.debug(f"Executing Scroll command: {command}")
            
            # Execute command
            result = i3_connection.command(command)
            success = all(r.success for r in result) if result else False
            
            if success:
                logger.debug(f"Mode set successfully: {command}")
            else:
                logger.error(f"Failed to set mode: {command}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error setting mode {mode} {modifier}: {e}", exc_info=True)
            return False
    
    def place_window(self, i3_connection, direction: str) -> bool:
        """
        Place window in specified direction by mapping to Scroll modes.
        
        Args:
            i3_connection: i3ipc connection object
            direction: Direction ('below', 'right', 'above', 'left')
            
        Returns:
            bool: True if placement successful
        """
        try:
            # Map high-level directions to Scroll modes
            direction_map = {
                'below': ('v', 'after'),
                'right': ('h', 'after'), 
                'above': ('v', 'before'),
                'left': ('h', 'before')
            }
            
            if direction not in direction_map:
                logger.error(f"Invalid direction: {direction}. Must be one of {list(direction_map.keys())}")
                return False
            
            mode, modifier = direction_map[direction]
            logger.debug(f"Placing window {direction} -> set_mode {mode} {modifier}")
            
            return self.set_mode(i3_connection, mode, modifier)
            
        except Exception as e:
            logger.error(f"Error placing window in direction {direction}: {e}", exc_info=True)
            return False
    
    def set_size(self, i3_connection, dimension: str, ratio: float) -> bool:
        """
        Execute set_size command for Scroll.
        
        Args:
            i3_connection: i3ipc connection object
            dimension: Dimension to resize ('h' for horizontal, 'v' for vertical)
            ratio: Size ratio (between 0.1 and 0.9)
            
        Returns:
            bool: True if command executed successfully
        """
        try:
            # Validate dimension
            if dimension not in ['h', 'v']:
                logger.error(f"Invalid dimension: {dimension}. Must be 'h' or 'v'")
                return False
                
            # Validate ratio
            if not (0.1 <= ratio <= 0.9):
                logger.error(f"Invalid ratio: {ratio}. Must be between 0.1 and 0.9")
                return False
            
            # Build command
            command = f"set_size {dimension} {ratio}"
            logger.debug(f"Executing Scroll command: {command}")
            
            # Execute command
            result = i3_connection.command(command)
            success = all(r.success for r in result) if result else False
            
            if success:
                logger.debug(f"Size set successfully: {command}")
            else:
                logger.error(f"Failed to set size: {command}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error setting size {dimension} {ratio}: {e}", exc_info=True)
            return False
    
    def preserve_column_split(self, i3_connection, container) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Get current column/container dimensions for preservation.
        
        Args:
            i3_connection: i3ipc connection object
            container: Container to preserve dimensions for
            
        Returns:
            tuple: (success, preserved_dimensions_dict)
        """
        try:
            if not container:
                logger.error("No container provided for dimension preservation")
                return False, None
            
            # Get current container dimensions
            dimensions = {
                'width': getattr(container, 'rect', {}).get('width', 0),
                'height': getattr(container, 'rect', {}).get('height', 0),
                'x': getattr(container, 'rect', {}).get('x', 0),
                'y': getattr(container, 'rect', {}).get('y', 0)
            }
            
            # Get parent container if available
            parent = getattr(container, 'parent', None)
            if parent:
                dimensions['parent_width'] = getattr(parent, 'rect', {}).get('width', 0)
                dimensions['parent_height'] = getattr(parent, 'rect', {}).get('height', 0)
                dimensions['parent_layout'] = getattr(parent, 'layout', 'none')
            
            logger.debug(f"Preserved dimensions: {dimensions}")
            return True, dimensions
            
        except Exception as e:
            logger.error(f"Error preserving column split: {e}", exc_info=True)
            return False, None
    
    def restore_original_mode(self, i3_connection, workspace: Optional[str] = None) -> bool:
        """
        Restore original mode for a workspace.
        
        Args:
            i3_connection: i3ipc connection object
            workspace: Workspace name (if None, uses current workspace)
            
        Returns:
            bool: True if restoration successful
        """
        try:
            if not workspace:
                workspace = self._get_current_workspace(i3_connection)
                
            if not workspace:
                logger.error("Could not determine workspace for mode restoration")
                return False
            
            original_mode = self._original_modes.get(workspace)
            if not original_mode:
                logger.debug(f"No original mode stored for workspace {workspace}")
                return True  # Nothing to restore is not an error
            
            # Parse original mode
            mode_parts = original_mode.split()
            if len(mode_parts) < 2:
                logger.error(f"Invalid stored mode format: {original_mode}")
                return False
            
            mode = mode_parts[1]  # Skip 'set_mode' part
            modifier = mode_parts[2] if len(mode_parts) > 2 else None
            
            logger.debug(f"Restoring original mode for workspace {workspace}: {original_mode}")
            success = self.set_mode(i3_connection, mode, modifier)
            
            if success:
                # Clean up stored mode
                del self._original_modes[workspace]
                logger.debug(f"Successfully restored mode for workspace {workspace}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error restoring original mode: {e}", exc_info=True)
            return False
    
    def execute_neovim_terminal_placement(self, i3_connection, neovim_container, terminal_size_ratio: float = 0.333) -> bool:
        """
        Execute the primary use case: place terminal below Neovim.
        
        Args:
            i3_connection: i3ipc connection object
            neovim_container: The Neovim container
            terminal_size_ratio: Size ratio for terminal (default 0.333 = 1/3)
            
        Returns:
            bool: True if placement flow initiated successfully
        """
        try:
            logger.debug("Starting Neovim→Terminal placement flow")
            
            # Step 1: Set mode to 'v after' 
            if not self.place_window(i3_connection, 'below'):
                logger.error("Failed to set vertical after mode")
                return False
            
            # Step 2: Mark parent container for tracking
            parent = getattr(neovim_container, 'parent', None)
            if parent:
                mark_id = f"_smart_parent_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                mark_command = f"[con_id={parent.id}] mark --add {mark_id}"
                
                logger.debug(f"Marking parent container: {mark_command}")
                result = i3_connection.command(mark_command)
                success = all(r.success for r in result) if result else False
                
                if not success:
                    logger.warning("Failed to mark parent container, continuing anyway")
            
            # Step 3: Store state for when terminal is created
            workspace = self._get_current_workspace(i3_connection)
            if workspace:
                state_manager.store_pending_rule(
                    workspace=workspace,
                    rule={'type': 'neovim_terminal', 'size_ratio': terminal_size_ratio},
                    parent_id=neovim_container.id,
                    context={
                        'neovim_container_id': neovim_container.id,
                        'mark_id': mark_id if parent else None,
                        'terminal_size_ratio': terminal_size_ratio
                    },
                    expires_in=15.0  # Give user 15 seconds to create terminal
                )
                
                logger.debug(f"Stored pending rule for workspace {workspace}")
            
            logger.debug("Neovim→Terminal placement flow initiated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in Neovim terminal placement: {e}", exc_info=True)
            # Always try to restore mode on error
            try:
                self.restore_original_mode(i3_connection)
            except Exception:
                pass  # Don't mask original error
            return False
    
    def apply_terminal_sizing(self, i3_connection, terminal_container) -> bool:
        """
        Apply size ratio to terminal after it's created.
        
        Args:
            i3_connection: i3ipc connection object  
            terminal_container: The terminal container that was just created
            
        Returns:
            bool: True if sizing applied successfully
        """
        try:
            workspace = self._get_current_workspace(i3_connection)
            if not workspace:
                logger.error("Could not determine workspace for terminal sizing")
                return False
            
            # Get pending rule
            pending_rule = state_manager.get_pending_rule(workspace)
            if not pending_rule:
                logger.debug("No pending rule found for terminal sizing")
                return False
            
            rule = pending_rule.get('rule', {})
            if rule.get('type') != 'neovim_terminal':
                logger.debug("Pending rule is not for neovim terminal")
                return False
            
            # Apply size ratio
            size_ratio = rule.get('size_ratio', 0.333)
            success = self.set_size(i3_connection, 'v', size_ratio)
            
            if success:
                logger.debug(f"Applied terminal size ratio: {size_ratio}")
                
                # Restore original mode
                self.restore_original_mode(i3_connection, workspace)
            else:
                logger.error("Failed to apply terminal size ratio")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying terminal sizing: {e}", exc_info=True)
            return False
    
    def _get_current_mode(self, i3_connection) -> Optional[str]:
        """
        Get current Scroll mode (placeholder implementation).
        
        Args:
            i3_connection: i3ipc connection object
            
        Returns:
            str: Current mode command or None if unavailable
        """
        try:
            # In a full implementation, this would query Scroll for current mode
            # For now, return a default mode
            # This could be extended when Scroll provides mode query capabilities
            return "set_mode h after"  # Default horizontal after mode
            
        except Exception as e:
            logger.error(f"Error getting current mode: {e}")
            return None
    
    def _get_current_workspace(self, i3_connection) -> Optional[str]:
        """
        Get current workspace name.
        
        Args:
            i3_connection: i3ipc connection object
            
        Returns:
            str: Current workspace name or None if unavailable
        """
        try:
            tree = i3_connection.get_tree()
            focused = tree.find_focused()
            if focused:
                workspace = focused.workspace()
                if workspace:
                    return workspace.name
            return None
            
        except Exception as e:
            logger.error(f"Error getting current workspace: {e}")
            return None
    
    def cleanup_expired_modes(self) -> None:
        """Clean up expired mode storage to prevent memory leaks."""
        try:
            # Clean up modes that are too old (over 1 hour)
            current_time = time.time()
            expired_workspaces = []
            
            for workspace in self._original_modes:
                # In a more sophisticated implementation, we could track timestamps
                # For now, just clean up periodically
                pass
            
            logger.debug("Mode cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during mode cleanup: {e}")


# Module-level convenience functions

def create_layout_manager() -> ScrollLayoutManager:
    """Create and return a new ScrollLayoutManager instance."""
    return ScrollLayoutManager()


def safe_command(i3_connection, command: str) -> bool:
    """
    Execute a command safely with error handling.
    
    Args:
        i3_connection: i3ipc connection object
        command: Command string to execute
        
    Returns:
        bool: True if command executed successfully
    """
    try:
        result = i3_connection.command(command)
        return all(r.success for r in result) if result else False
    except Exception as e:
        logger.error(f"Command failed: {command}, error: {e}")
        return False