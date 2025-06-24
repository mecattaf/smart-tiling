"""
State management module for smart-tiling.
Tracks relationships between windows and manages time-based state.
"""
import time
import threading
from typing import Dict, Any, Optional


class StateManager:
    """Thread-safe state manager for tracking window relationships and pending rules."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._relationships: Dict[str, Dict[str, Any]] = {}
        self._pending_rules: Dict[str, Dict[str, Any]] = {}
    
    def store_relationship(self, child_id: str, parent_id: str, rule_name: str, context: Dict[str, Any]):
        """Store a parent-child window relationship."""
        with self._lock:
            self._relationships[child_id] = {
                'parent_id': parent_id,
                'rule_name': rule_name,
                'created_at': time.time(),
                'parent_context': context
            }
    
    def get_relationship(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship information for a child container."""
        with self._lock:
            return self._relationships.get(child_id)
    
    def store_pending_rule(self, workspace: str, rule: Any, parent_id: str, context: Dict[str, Any], expires_in: float = 10.0):
        """Store a pending rule for application."""
        with self._lock:
            self._pending_rules[workspace] = {
                'rule': rule,
                'parent_id': parent_id,
                'context': context,
                'expires_at': time.time() + expires_in
            }
    
    def get_pending_rule(self, workspace: str) -> Optional[Dict[str, Any]]:
        """Get pending rule for a workspace."""
        with self._lock:
            rule_info = self._pending_rules.get(workspace)
            if rule_info and rule_info['expires_at'] > time.time():
                return rule_info
            elif rule_info:
                del self._pending_rules[workspace]
            return None


# Global state manager instance
state_manager = StateManager()