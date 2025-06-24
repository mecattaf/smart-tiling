"""
Scroll IPC integration module.
Extends i3ipc with Scroll-specific events and functionality.
"""
from i3ipc import Connection, Event
from typing import Dict, Any, Optional


class ScrollConnection(Connection):
    """Extended i3ipc connection with Scroll-specific functionality."""
    
    def __init__(self):
        super().__init__()
        # Scroll-specific initialization
        self._scroll_mode = {'h_mode': False, 'v_mode': False}
        self._modifier_state = {'scroll_mod': False}
        self._scroller_events_subscribed = False
    
    def subscribe_scroller_events(self):
        """Subscribe to Scroll-specific events."""
        # IPC_EVENT_SCROLLER subscription
        if not self._scroller_events_subscribed:
            try:
                # Note: This would need to be adapted when Scroll implements IPC_EVENT_SCROLLER
                # For now, we set up the framework for future implementation
                self.on('scroller', handle_scroller_event)
                self._scroller_events_subscribed = True
            except Exception as e:
                # Scroll may not support this event type yet
                print(f"Could not subscribe to scroller events: {e}")
                pass
    
    def get_scroller_mode(self) -> Dict[str, Any]:
        """Get current Scroll mode information."""
        # Mode retrieval - return current tracked state
        # In a full implementation, this would query Scroll directly
        return {
            'h_mode': self._scroll_mode.get('h_mode', False),
            'v_mode': self._scroll_mode.get('v_mode', False),
            'scroll_mod': self._modifier_state.get('scroll_mod', False)
        }


def handle_scroller_event(i3, event) -> None:
    """Handle Scroll-specific IPC events."""
    try:
        # Parse IPC_EVENT_SCROLLER events
        if hasattr(event, 'change') and hasattr(event, 'container'):
            change = event.change
            
            # Update mode tracking state based on event
            if hasattr(i3, '_scroll_mode'):
                if change == 'h_mode_enter':
                    i3._scroll_mode['h_mode'] = True
                elif change == 'h_mode_exit':
                    i3._scroll_mode['h_mode'] = False
                elif change == 'v_mode_enter':
                    i3._scroll_mode['v_mode'] = True
                elif change == 'v_mode_exit':
                    i3._scroll_mode['v_mode'] = False
                elif change == 'scroll_mod_press':
                    i3._modifier_state['scroll_mod'] = True
                elif change == 'scroll_mod_release':
                    i3._modifier_state['scroll_mod'] = False
            
            # Trigger appropriate responses based on mode changes
            # This could be extended to send notifications or update UI
            
    except Exception as e:
        print(f"Error handling scroller event: {e}")


def setup_scroll_integration(connection) -> None:
    """Set up Scroll-specific IPC integration."""
    try:
        # Ensure we have a ScrollConnection or enhance regular connection
        if not isinstance(connection, ScrollConnection):
            # Add Scroll-specific attributes to regular connection
            connection._scroll_mode = {'h_mode': False, 'v_mode': False}
            connection._modifier_state = {'scroll_mod': False}
            connection._scroller_events_subscribed = False
        
        # Subscribe to additional Scroll events
        if hasattr(connection, 'subscribe_scroller_events'):
            connection.subscribe_scroller_events()
        else:
            # Set up event handlers for regular connection
            try:
                connection.on('scroller', handle_scroller_event)
            except Exception:
                # Scroller events may not be available
                pass
        
        # Initialize Scroll-specific state tracking
        print("Scroll integration initialized")
        
    except Exception as e:
        print(f"Error setting up Scroll integration: {e}")