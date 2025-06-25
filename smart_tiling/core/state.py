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
        self._parent_cwds: Dict[str, Dict[str, Any]] = {}
        self._preserved_dimensions: Dict[str, Dict[str, Any]] = {}
    
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
    
    def store_parent_cwd(self, workspace: str, parent_id: str, cwd: str, expires_in: float = 60.0):
        """Store parent's working directory for child windows to inherit."""
        with self._lock:
            self._parent_cwds[workspace] = {
                'parent_id': parent_id,
                'cwd': cwd,
                'expires_at': time.time() + expires_in
            }
    
    def get_parent_cwd(self, workspace: str) -> Optional[str]:
        """Get stored parent working directory for a workspace."""
        with self._lock:
            cwd_info = self._parent_cwds.get(workspace)
            if cwd_info and cwd_info['expires_at'] > time.time():
                return cwd_info['cwd']
            elif cwd_info:
                del self._parent_cwds[workspace]
            return None
    
    def store_preserved_dimensions(self, workspace: str, container_id: str, dimensions: Dict[str, Any], expires_in: float = 60.0):
        """Store container dimensions for restoration."""
        with self._lock:
            self._preserved_dimensions[workspace] = {
                'container_id': container_id,
                'dimensions': dimensions,
                'expires_at': time.time() + expires_in
            }
    
    def get_preserved_dimensions(self, workspace: str) -> Optional[Dict[str, Any]]:
        """Get stored container dimensions for a workspace."""
        with self._lock:
            dim_info = self._preserved_dimensions.get(workspace)
            if dim_info and dim_info['expires_at'] > time.time():
                return dim_info['dimensions']
            elif dim_info:
                del self._preserved_dimensions[workspace]
            return None
    
    def cleanup_expired_state(self):
        """Clean up all expired state data."""
        current_time = time.time()
        with self._lock:
            # Clean up expired pending rules
            expired_rules = [ws for ws, info in self._pending_rules.items() 
                           if info['expires_at'] <= current_time]
            for ws in expired_rules:
                del self._pending_rules[ws]
            
            # Clean up expired CWDs
            expired_cwds = [ws for ws, info in self._parent_cwds.items() 
                          if info['expires_at'] <= current_time]
            for ws in expired_cwds:
                del self._parent_cwds[ws]
            
            # Clean up expired dimensions
            expired_dims = [ws for ws, info in self._preserved_dimensions.items() 
                          if info['expires_at'] <= current_time]
            for ws in expired_dims:
                del self._preserved_dimensions[ws]


# Global state manager instance
state_manager = StateManager()