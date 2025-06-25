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


# Global rule engine instance
rule_engine = RuleEngine()