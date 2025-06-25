#!/usr/bin/env python3

"""
This script uses the i3ipc python module to switch the layout splith / splitv
for the currently focused window, depending on its dimensions.
It works on both sway and i3 window managers.

Inspired by https://github.com/olemartinorg/i3-alternating-layout

Copyright: 2019-2021 Piotr Miller & Contributors
e-mail: nwg.piotr@gmail.com
Project: https://github.com/nwg-piotr/autotiling
License: GPL3

Dependencies: python-i3ipc>=2.0.1 (i3ipc-python)
"""
import argparse
import os
import sys
from functools import partial

from i3ipc import Connection, Event

try:
    from .__about__ import __version__
except ImportError:
    __version__ = "unknown"

# Import smart-tiling modules
from .core.geometry import switch_splitting
from .core.context import matches_app_context

# Import optional modules that may not exist yet
try:
    from .config.parser import load_config
except ImportError:
    def load_config(path):
        """Fallback config loader when parser module not available."""
        return {} if not path else {}

try:
    from .core.rules import rule_engine
except ImportError:
    class MockRuleEngine:
        """Mock rule engine when not available."""
        def load_rules(self, rules): pass
    rule_engine = MockRuleEngine()

try:
    from .core.state import state_manager
except ImportError:
    class MockStateManager:
        """Mock state manager when not available."""
        pass
    state_manager = MockStateManager()


def temp_dir():
    return os.getenv("TMPDIR") or os.getenv("TEMP") or os.getenv("TMP") or "/tmp"


def save_string(string, file_path):
    try:
        with open(file_path, "wt") as file:
            file.write(string)
    except Exception as e:
        print(e)


def handle_smart_rules(i3, event, config, debug=False):
    """
    Handle smart rule matching and execution based on event type.
    
    Args:
        i3: i3ipc connection
        event: Window event
        config: Configuration dict
        debug: Enable debug logging
        
    Returns:
        dict: Result with 'handled' flag indicating if rule was applied
    """
    try:
        if not config.get('rules'):
            return {'handled': False}
        
        # Get the container from the event
        container = event.container
        if not container:
            return {'handled': False}
        
        # Get current workspace for state management
        workspace = _get_current_workspace_name(i3)
        if not workspace:
            if debug:
                print("Could not determine current workspace", file=sys.stderr)
            return {'handled': False}
        
        # Handle different event types
        if hasattr(event, 'change'):
            event_type = event.change
            
            if event_type == 'focus':
                # Parent focus event - check for matching rules and store as pending
                return _handle_parent_focus_event(i3, container, config, workspace, debug)
                
            elif event_type == 'new':
                # New window event - check for pending rules and execute
                return _handle_new_window_event(i3, container, config, workspace, debug)
        
        # For other events, fall back to immediate rule matching
        return _handle_immediate_rule_matching(i3, container, config, debug)
        
    except Exception as e:
        if debug:
            print(f"Error in smart rule handling: {e}", file=sys.stderr)
        return {'handled': False}


def _get_current_workspace_name(i3):
    """Get current workspace name."""
    try:
        tree = i3.get_tree()
        focused = tree.find_focused()
        if focused:
            workspace = focused.workspace()
            if workspace:
                return workspace.name
    except Exception:
        pass
    return None


def _handle_parent_focus_event(i3, container, config, workspace, debug=False):
    """Handle parent window focus events."""
    try:
        # Check if this container matches any parent criteria
        for rule_dict in config.get('rules', []):
            if rule_engine.matches_rule(container, rule_dict):
                rule = rule_engine._parse_rule(rule_dict)
                
                if debug:
                    print(f"Parent focus matched rule: {rule.name} (app_id: {container.app_id}, title: {container.name})", file=sys.stderr)
                
                # Pre-execute set_mode actions immediately
                _pre_execute_mode_actions(i3, rule, debug)
                
                # Store rule as pending
                rule_engine.store_pending_rule(
                    workspace=workspace,
                    rule=rule,
                    parent_container=container,
                    expires_in=config.get('rule_timeout', 15.0)
                )
                
                if debug:
                    print(f"Stored pending rule: {rule.name} for workspace: {workspace}", file=sys.stderr)
                
                return {'handled': True, 'rule_name': rule.name, 'action': 'pending'}
        
        return {'handled': False}
        
    except Exception as e:
        if debug:
            print(f"Error in parent focus handling: {e}", file=sys.stderr)
        return {'handled': False}


def _handle_new_window_event(i3, container, config, workspace, debug=False):
    """Handle new window creation events."""
    try:
        # Check if there's a pending rule for this workspace
        rule = rule_engine.check_child_against_pending_rules(container, workspace)
        if rule:
            if debug:
                print(f"New window matched pending rule: {rule.name} (app_id: {container.app_id})", file=sys.stderr)
            
            # Execute remaining actions (non-mode actions)
            result = _execute_child_actions(i3, container, rule, debug)
            
            if result.get('handled'):
                return result
        
        return {'handled': False}
        
    except Exception as e:
        if debug:
            print(f"Error in new window handling: {e}", file=sys.stderr)
        return {'handled': False}


def _handle_immediate_rule_matching(i3, container, config, debug=False):
    """Handle immediate rule matching for non-focus/new events."""
    try:
        # Apply smart rules from configuration immediately
        for rule_dict in config.get('rules', []):
            if rule_engine.matches_rule(container, rule_dict):
                if debug:
                    print(f"Immediate rule matched: {rule_dict.get('name', 'unnamed')} (app_id: {container.app_id}, title: {container.name})", file=sys.stderr)
                
                # Execute all rule actions immediately
                result = rule_engine.execute_rule(i3, container, rule_dict, debug)
                if result.get('handled'):
                    return result
        
        return {'handled': False}
        
    except Exception as e:
        if debug:
            print(f"Error in immediate rule matching: {e}", file=sys.stderr)
        return {'handled': False}


def _pre_execute_mode_actions(i3, rule, debug=False):
    """Pre-execute set_mode actions when parent gets focus."""
    try:
        from .scroll.layout import create_layout_manager
        layout_manager = create_layout_manager()
        
        for action in rule.actions:
            if action.get('action') == 'set_mode':
                mode = action.get('mode', 'v')
                modifier = action.get('modifier', None)
                
                if debug:
                    print(f"  Pre-executing set_mode: {mode} {modifier or ''}", file=sys.stderr)
                
                success = layout_manager.set_mode(i3, mode, modifier)
                if not success and debug:
                    print(f"  Failed to pre-execute set_mode: {mode} {modifier or ''}", file=sys.stderr)
                    
    except Exception as e:
        if debug:
            print(f"Error pre-executing mode actions: {e}", file=sys.stderr)


def _execute_child_actions(i3, container, rule, debug=False):
    """Execute non-mode actions for child windows."""
    try:
        from .scroll.layout import create_layout_manager
        layout_manager = create_layout_manager()
        
        results = {
            'handled': False,
            'rule_name': rule.name,
            'actions_executed': [],
            'actions_failed': []
        }
        
        # Execute non-mode actions
        for action in rule.actions:
            action_type = action.get('action', 'unknown')
            
            # Skip set_mode actions (already executed in pre-execute phase)
            if action_type == 'set_mode':
                continue
                
            action_success = False
            
            if debug:
                print(f"  Executing child action: {action_type}", file=sys.stderr)
            
            try:
                if action_type == 'place':
                    # Execute place action
                    direction = action.get('direction', 'below')
                    action_success = layout_manager.place_window(i3, direction)
                    
                elif action_type == 'size_ratio':
                    # Execute size_ratio action
                    ratio = action.get('value', 0.333)
                    direction = _get_placement_direction_from_rule(rule)
                    dimension = _map_direction_to_dimension(direction)
                    action_success = layout_manager.set_size(i3, dimension, ratio)
                    
                elif action_type == 'inherit_cwd':
                    # Execute inherit_cwd action
                    if action.get('enabled', False):
                        workspace = layout_manager._get_current_workspace(i3)
                        if workspace:
                            cwd = state_manager.get_parent_cwd(workspace)
                            if cwd and debug:
                                print(f"    Child can inherit CWD: {cwd}", file=sys.stderr)
                                # Note: Actual CWD inheritance would need to be handled by the terminal
                                # This just confirms the CWD is available
                            action_success = True
                    else:
                        action_success = True
                        
                elif action_type == 'preserve_column':
                    # Execute preserve_column action
                    if action.get('enabled', False):
                        workspace = layout_manager._get_current_workspace(i3)
                        if workspace:
                            dimensions = state_manager.get_preserved_dimensions(workspace)
                            if dimensions and debug:
                                print(f"    Preserved dimensions available: {dimensions}", file=sys.stderr)
                                # Note: Actual column restoration would need additional implementation
                            action_success = True
                    else:
                        action_success = True
                        
                else:
                    if debug:
                        print(f"    Unknown child action type: {action_type}", file=sys.stderr)
                    action_success = False
                
                # Track results
                if action_success:
                    results['actions_executed'].append(action_type)
                else:
                    results['actions_failed'].append(action_type)
                    
            except Exception as e:
                results['actions_failed'].append(f"{action_type}: {str(e)}")
                if debug:
                    print(f"    Child action {action_type} failed: {e}", file=sys.stderr)
        
        # Rule is considered handled if at least one action succeeded
        results['handled'] = len(results['actions_executed']) > 0
        
        if debug:
            print(f"  Child actions complete. Handled: {results['handled']}, "
                  f"Success: {len(results['actions_executed'])}, "
                  f"Failed: {len(results['actions_failed'])}", file=sys.stderr)
        
        return results
        
    except Exception as e:
        if debug:
            print(f"Error executing child actions: {e}", file=sys.stderr)
        return {'handled': False, 'error': str(e), 'rule_name': rule.name}


def _get_placement_direction_from_rule(rule):
    """Extract placement direction from rule actions."""
    for action in rule.actions:
        if action.get('action') == 'place':
            return action.get('direction', 'below')
    return 'below'  # default


def _map_direction_to_dimension(direction):
    """Map placement direction to sizing dimension."""
    direction_map = {
        'below': 'v',
        'above': 'v',
        'left': 'h', 
        'right': 'h'
    }
    return direction_map.get(direction, 'v')


def smart_switch_splitting(i3, e, debug, outputs, workspaces, depth_limit, splitwidth, splitheight, splitratio, config):
    """
    Smart tiling handler with context-aware placement.
    This is the main integration point between smart rules and geometry-based tiling.
    """
    try:
        # INJECTION POINT: Before geometry decision
        if config and config.get('rules'):
            # Smart rule matching and execution
            result = handle_smart_rules(i3, e, config, debug)
            if result and result.get('handled'):
                return
        
        # Fall back to original geometry-based logic
        switch_splitting(i3, e, debug, outputs, workspaces, depth_limit, splitwidth, splitheight, splitratio)
        
    except Exception as e:
        print(f"Error in smart_switch_splitting: {e}", file=sys.stderr)
        # Ultimate fallback: try geometry-based tiling
        try:
            switch_splitting(i3, e, debug, outputs, workspaces, depth_limit, splitwidth, splitheight, splitratio)
        except Exception as fallback_e:
            print(f"Error in fallback: {fallback_e}", file=sys.stderr)


def get_parser():
    parser = argparse.ArgumentParser(prog="smart-tiling", description="Context-aware window tiling for Scroll window manager")

    parser.add_argument("-d", "--debug", action="store_true",
                        help="print debug messages to stderr")
    parser.add_argument("-v", "--version", action="version",
                        version=f"%(prog)s {__version__}, Python {sys.version}",
                        help="display version information")
    parser.add_argument("-o", "--outputs", nargs="*", type=str, default=[],
                        help="restricts autotiling to certain output; example: smart-tiling --output  DP-1 HDMI-0")
    parser.add_argument("-w", "--workspaces", nargs="*", type=str, default=[],
                        help="restricts autotiling to certain workspaces; example: smart-tiling --workspaces 8 9")
    parser.add_argument("-l", "--limit", type=int, default=0,
                        help='limit how often autotiling will split a container; '
                             'try "2" if you like master-stack layouts; default: 0 (no limit)')
    parser.add_argument("-sw",
                        "--splitwidth",
                        help='set the width of the vertical split (as factor); default: 1.0;',
                        type=float,
                        default=1.0, )
    parser.add_argument("-sh",
                        "--splitheight",
                        help='set the height of the horizontal split (as factor); default: 1.0;',
                        type=float,
                        default=1.0, )
    parser.add_argument("-sr",
                        "--splitratio",
                        help='Split direction ratio - based on window height/width; default: 1;'
                             'try "1.61", for golden ratio - window has to be 61%% wider for left/right split; default: 1.0;',
                        type=float,
                        default=1.0, )

    """
    Changing event subscription has already been the objective of several pull request. To avoid doing this again
    and again, let's allow to specify them in the `--events` argument.
    """
    parser.add_argument("-e", "--events", nargs="*", type=str, default=["WINDOW", "MODE"],
                        help="list of events to trigger switching split orientation; default: WINDOW MODE")
    parser.add_argument("--config", type=str, help="path to smart-tiling configuration file")

    return parser

def main():
    args = get_parser().parse_args()

    # Load configuration
    config = load_config(args.config)
    if config.get('rules'):
        rule_engine.load_rules(config['rules'])
        if args.debug:
            print(f"Loaded {len(config['rules'])} smart-tiling rules")

    if args.debug:
        if args.outputs:
            print(f"smart-tiling is only active on outputs: {','.join(args.outputs)}")
        if args.workspaces:
            print(f"smart-tiling is only active on workspaces: {','.join(args.workspaces)}")

    # For use w/ nwg-panel
    ws_file = os.path.join(temp_dir(), "smart-tiling")
    if args.workspaces:
        save_string(','.join(args.workspaces), ws_file)
    else:
        if os.path.isfile(ws_file):
            os.remove(ws_file)

    if not args.events:
        print("No events specified", file=sys.stderr)
        sys.exit(1)

    # Use smart handler instead of original switch_splitting
    handler = partial(
        smart_switch_splitting,
        debug=args.debug,
        outputs=args.outputs,
        workspaces=args.workspaces,
        depth_limit=args.limit,
        splitwidth=args.splitwidth,
        splitheight=args.splitheight,
        splitratio=args.splitratio,
        config=config
    )
    i3 = Connection()
    for e in args.events:
        try:
            i3.on(Event[e], handler)
            print(f"{Event[e]} subscribed")
        except KeyError:
            print(f"'{e}' is not a valid event", file=sys.stderr)

    i3.main()


if __name__ == "__main__":
    main()