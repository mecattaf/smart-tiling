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


def handle_smart_rules(i3, event, config):
    """
    Handle smart rule matching and execution.
    
    Args:
        i3: i3ipc connection
        event: Window event
        config: Configuration dict
        
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
        
        # Example smart rule: Detect Kitty terminal with Neovim
        # This demonstrates how the context detection works
        if matches_app_context(container, 
                             app_id_list=['kitty', 'alacritty'], 
                             title_patterns=['*nvim*', '*vim*']):
            # For demonstration, we'll log that we detected this case
            # In a full implementation, this would apply specific rules
            print(f"Smart rule detected: Terminal with editor (app_id: {container.app_id}, title: {container.name})", file=sys.stderr)
            
            # Could apply custom tiling behavior here
            # For now, return False to fall back to normal tiling
            return {'handled': False}
        
        # No rules matched
        return {'handled': False}
        
    except Exception as e:
        print(f"Error in smart rule handling: {e}", file=sys.stderr)
        return {'handled': False}


def smart_switch_splitting(i3, e, debug, outputs, workspaces, depth_limit, splitwidth, splitheight, splitratio, config):
    """
    Smart tiling handler with context-aware placement.
    This is the main integration point between smart rules and geometry-based tiling.
    """
    try:
        # INJECTION POINT: Before geometry decision
        if config and config.get('rules'):
            # Smart rule matching and execution
            result = handle_smart_rules(i3, e, config)
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