"""
Rule engine module for smart-tiling.
Handles rule parsing, matching, and action execution planning.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .context import matches_app_context
from .state import state_manager


@dataclass
class ParentMatcher:
    """Criteria for matching parent containers."""
    app_id: List[str] = field(default_factory=list)
    window_class: List[str] = field(default_factory=list, metadata={'key': 'class'})
    title_pattern: List[str] = field(default_factory=list)


@dataclass  
class ChildMatcher:
    """Criteria for matching child containers."""
    app_id: List[str] = field(default_factory=list)


@dataclass
class Rule:
    """A complete rule definition with parent/child matching and actions."""
    name: str
    parent: ParentMatcher
    child: ChildMatcher
    actions: List[Dict[str, Any]]


class RuleEngine:
    """Rule engine for matching containers and managing rule state."""
    
    def __init__(self):
        self.rules: List[Rule] = []
    
    def load_rules(self, rules_list: List[Dict]) -> None:
        """Parse rule dictionaries into Rule objects.
        
        Args:
            rules_list: List of rule dictionaries from configuration
        """
        self.rules = []
        for rule_dict in rules_list:
            try:
                rule = self._parse_rule(rule_dict)
                self.rules.append(rule)
            except Exception as e:
                print(f"Error parsing rule {rule_dict.get('name', 'unnamed')}: {e}")
    
    def _parse_rule(self, rule_dict: Dict) -> Rule:
        """Parse a rule dictionary into a Rule object.
        
        Args:
            rule_dict: Rule configuration dictionary
            
        Returns:
            Rule: Parsed rule object
        """
        name = rule_dict.get('name', 'unnamed')
        
        # Parse parent matcher
        parent_config = rule_dict.get('parent', {})
        parent = ParentMatcher(
            app_id=self._ensure_list(parent_config.get('app_id', [])),
            window_class=self._ensure_list(parent_config.get('class', [])),
            title_pattern=self._ensure_list(parent_config.get('title_pattern', []))
        )
        
        # Parse child matcher  
        child_config = rule_dict.get('child', {})
        child = ChildMatcher(
            app_id=self._ensure_list(child_config.get('app_id', []))
        )
        
        # Parse actions
        actions = self._parse_actions(rule_dict.get('actions', []))
        
        return Rule(name=name, parent=parent, child=child, actions=actions)
    
    def _ensure_list(self, value) -> List[str]:
        """Ensure value is a list of strings."""
        if isinstance(value, str):
            return [value]
        elif isinstance(value, list):
            return [str(v) for v in value]
        else:
            return []
    
    def _parse_actions(self, actions_config: List) -> List[Dict[str, Any]]:
        """Parse action configurations into standardized format.
        
        Args:
            actions_config: List of action configurations
            
        Returns:
            List of parsed action dictionaries
        """
        parsed_actions = []
        
        for action_config in actions_config:
            if isinstance(action_config, str):
                # Handle string format like "set_mode: v after"
                parsed_action = self._parse_string_action(action_config)
                if parsed_action:
                    parsed_actions.append(parsed_action)
            elif isinstance(action_config, dict):
                # Handle dict format
                for key, value in action_config.items():
                    parsed_action = self._parse_dict_action(key, value)
                    if parsed_action:
                        parsed_actions.append(parsed_action)
        
        return parsed_actions
    
    def _parse_string_action(self, action_str: str) -> Optional[Dict[str, Any]]:
        """Parse string-format actions."""
        try:
            if ':' in action_str:
                key, value = action_str.split(':', 1)
                key = key.strip()
                value = value.strip()
                return self._parse_dict_action(key, value)
        except Exception:
            pass
        return None
    
    def _parse_dict_action(self, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """Parse dictionary-format actions into standardized format.
        
        Action format examples:
        - set_mode: v after → {'action': 'set_mode', 'mode': 'v', 'modifier': 'after'}
        - place: below → {'action': 'place', 'direction': 'below'}
        - size_ratio: 0.333 → {'action': 'size_ratio', 'value': 0.333}
        - inherit_cwd: true → {'action': 'inherit_cwd', 'enabled': True}
        - preserve_column: true → {'action': 'preserve_column', 'enabled': True}
        """
        try:
            if key == 'set_mode':
                # Parse "set_mode: v after" format
                parts = str(value).split()
                if len(parts) >= 1:
                    result = {'action': 'set_mode', 'mode': parts[0]}
                    if len(parts) >= 2:
                        result['modifier'] = parts[1]
                    return result
            
            elif key == 'place':
                return {'action': 'place', 'direction': str(value)}
            
            elif key == 'size_ratio':
                return {'action': 'size_ratio', 'value': float(value)}
            
            elif key in ['inherit_cwd', 'preserve_column']:
                enabled = value in [True, 'true', 'True', '1', 1]
                return {'action': key, 'enabled': enabled}
            
            else:
                # Generic action format
                return {'action': key, 'value': value}
                
        except Exception:
            pass
        
        return None
    
    def match_parent(self, container, workspace_state=None) -> Optional[Rule]:
        """Check if container matches any parent criteria.
        
        Args:
            container: i3ipc container object
            workspace_state: Optional workspace state information
            
        Returns:
            Optional[Rule]: Matched rule or None
        """
        for rule in self.rules:
            if self._matches_parent_criteria(container, rule.parent):
                return rule
        return None
    
    def _matches_parent_criteria(self, container, parent_matcher: ParentMatcher) -> bool:
        """Check if container matches parent matcher criteria."""
        # Use existing context matching functionality
        return matches_app_context(
            container,
            app_id_list=parent_matcher.app_id,
            window_class_list=parent_matcher.window_class,
            title_patterns=parent_matcher.title_pattern
        )
    
    def match_child(self, container, rule: Rule) -> bool:
        """Check if container matches child criteria for a specific rule.
        
        Args:
            container: i3ipc container object
            rule: Rule to match against
            
        Returns:
            bool: True if container matches child criteria
        """
        if not rule.child.app_id:
            # If no child criteria specified, any child matches
            return True
        
        return matches_app_context(
            container,
            app_id_list=rule.child.app_id
        )
    
    def should_apply_rule(self, parent_container, child_container) -> Optional[Rule]:
        """Full matching logic for parent-child relationship.
        
        Args:
            parent_container: Parent container object
            child_container: Child container object
            
        Returns:
            Optional[Rule]: Rule to apply or None
        """
        # First check if parent matches any rule
        matched_rule = self.match_parent(parent_container)
        if not matched_rule:
            return None
        
        # Then check if child matches the rule's child criteria
        if self.match_child(child_container, matched_rule):
            return matched_rule
        
        return None
    
    def store_pending_rule(self, workspace: str, rule: Rule, parent_container, expires_in: float = 10.0):
        """Store a rule as pending for a workspace.
        
        Args:
            workspace: Workspace identifier
            rule: Rule to store as pending
            parent_container: Parent container that matched
            expires_in: Seconds until rule expires (default 10)
        """
        from .context import detect_app_context
        
        parent_context = detect_app_context(parent_container)
        parent_id = getattr(parent_container, 'id', None)
        
        state_manager.store_pending_rule(
            workspace=workspace,
            rule=rule,
            parent_id=parent_id,
            context=parent_context,
            expires_in=expires_in
        )
    
    def get_pending_rule(self, workspace: str) -> Optional[Dict[str, Any]]:
        """Get any pending rule for a workspace.
        
        Args:
            workspace: Workspace identifier
            
        Returns:
            Optional[Dict]: Pending rule information or None
        """
        return state_manager.get_pending_rule(workspace)
    
    def check_child_against_pending_rules(self, child_container, workspace: str) -> Optional[Rule]:
        """Check if a new child container matches any pending rules.
        
        Args:
            child_container: New child container
            workspace: Workspace identifier
            
        Returns:
            Optional[Rule]: Matching rule or None
        """
        pending_rule_info = self.get_pending_rule(workspace)
        if not pending_rule_info:
            return None
        
        rule = pending_rule_info['rule']
        if self.match_child(child_container, rule):
            # Store the relationship
            parent_id = pending_rule_info['parent_id']
            child_id = getattr(child_container, 'id', None)
            
            if child_id and parent_id:
                state_manager.store_relationship(
                    child_id=child_id,
                    parent_id=parent_id,
                    rule_name=rule.name,
                    context=pending_rule_info['context']
                )
            
            return rule
        
        return None
    
    def matches_rule(self, container, rule_dict: Dict[str, Any]) -> bool:
        """Check if a container matches a rule definition.
        
        Args:
            container: i3ipc container object
            rule_dict: Rule configuration dictionary
            
        Returns:
            bool: True if container matches the rule's parent criteria
        """
        try:
            rule = self._parse_rule(rule_dict)
            return self._matches_parent_criteria(container, rule.parent)
        except Exception:
            return False
    
    def execute_rule(self, i3_connection, container, rule_dict: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """Execute a rule's actions on a container.
        
        Args:
            i3_connection: i3ipc connection object
            container: i3ipc container object that matched the rule
            rule_dict: Rule configuration dictionary
            debug: Enable debug logging
            
        Returns:
            Dict with 'handled' flag and execution results
        """
        import sys
        
        try:
            rule = self._parse_rule(rule_dict)
            
            if debug:
                print(f"Executing rule '{rule.name}' with {len(rule.actions)} actions", file=sys.stderr)
            
            # Get layout manager
            from ..scroll.layout import create_layout_manager
            layout_manager = create_layout_manager()
            
            # Get process detection functions
            from .process import get_process_cwd
            
            # Results tracking
            results = {
                'handled': False,
                'rule_name': rule.name,
                'actions_executed': [],
                'actions_failed': []
            }
            
            # Execute actions in order
            for i, action in enumerate(rule.actions):
                action_type = action.get('action', 'unknown')
                action_success = False
                
                if debug:
                    print(f"  Executing action {i+1}/{len(rule.actions)}: {action_type}", file=sys.stderr)
                
                try:
                    if action_type == 'set_mode':
                        # Execute set_mode action
                        mode = action.get('mode', 'v')
                        modifier = action.get('modifier', None)
                        action_success = layout_manager.set_mode(i3_connection, mode, modifier)
                        
                    elif action_type == 'place':
                        # Execute place action
                        direction = action.get('direction', 'below')
                        action_success = layout_manager.place_window(i3_connection, direction)
                        
                    elif action_type == 'size_ratio':
                        # Execute size_ratio action
                        ratio = action.get('value', 0.333)
                        direction = self._get_placement_direction_from_actions(rule.actions)
                        dimension = self._map_direction_to_dimension(direction)
                        action_success = layout_manager.set_size(i3_connection, dimension, ratio)
                        
                    elif action_type == 'inherit_cwd':
                        # Execute inherit_cwd action
                        if action.get('enabled', False):
                            container_pid = getattr(container, 'pid', None)
                            if container_pid:
                                cwd = get_process_cwd(container_pid)
                                if cwd:
                                    # Store CWD in state for child windows to inherit
                                    workspace = layout_manager._get_current_workspace(i3_connection)
                                    if workspace:
                                        state_manager.store_parent_cwd(workspace, container.id, cwd)
                                        action_success = True
                                        if debug:
                                            print(f"    Stored CWD: {cwd}", file=sys.stderr)
                                    else:
                                        if debug:
                                            print("    Failed to get current workspace for CWD storage", file=sys.stderr)
                                else:
                                    if debug:
                                        print(f"    Failed to get CWD for PID {container_pid}", file=sys.stderr)
                            else:
                                if debug:
                                    print("    Container has no PID for CWD extraction", file=sys.stderr)
                        else:
                            action_success = True  # Not enabled, but not an error
                            
                    elif action_type == 'preserve_column':
                        # Execute preserve_column action
                        if action.get('enabled', False):
                            success, dimensions = layout_manager.preserve_column_split(i3_connection, container)
                            if success and dimensions:
                                # Store dimensions for restoration
                                workspace = layout_manager._get_current_workspace(i3_connection)
                                if workspace:
                                    state_manager.store_preserved_dimensions(workspace, container.id, dimensions)
                                    action_success = True
                                    if debug:
                                        print(f"    Preserved dimensions: {dimensions}", file=sys.stderr)
                                else:
                                    if debug:
                                        print("    Failed to get current workspace for dimension storage", file=sys.stderr)
                            else:
                                if debug:
                                    print("    Failed to preserve column dimensions", file=sys.stderr)
                        else:
                            action_success = True  # Not enabled, but not an error
                            
                    else:
                        # Unknown action type
                        if debug:
                            print(f"    Unknown action type: {action_type}", file=sys.stderr)
                        action_success = False
                    
                    # Track results
                    if action_success:
                        results['actions_executed'].append(action_type)
                    else:
                        results['actions_failed'].append(action_type)
                        
                except Exception as e:
                    results['actions_failed'].append(f"{action_type}: {str(e)}")
                    if debug:
                        print(f"    Action {action_type} failed: {e}", file=sys.stderr)
            
            # Rule is considered handled if at least one action succeeded
            results['handled'] = len(results['actions_executed']) > 0
            
            if debug:
                print(f"  Rule execution complete. Handled: {results['handled']}, "
                      f"Success: {len(results['actions_executed'])}, "
                      f"Failed: {len(results['actions_failed'])}", file=sys.stderr)
            
            return results
            
        except Exception as e:
            if debug:
                print(f"Error executing rule: {e}", file=sys.stderr)
            return {'handled': False, 'error': str(e), 'rule_name': rule_dict.get('name', 'unnamed')}

    def _get_placement_direction_from_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Extract placement direction from actions list."""
        for action in actions:
            if action.get('action') == 'place':
                return action.get('direction', 'below')
        return 'below'  # default

    def _map_direction_to_dimension(self, direction: str) -> str:
        """Map placement direction to sizing dimension."""
        direction_map = {
            'below': 'v',
            'above': 'v',
            'left': 'h', 
            'right': 'h'
        }
        return direction_map.get(direction, 'v')


# Global rule engine instance
rule_engine = RuleEngine()