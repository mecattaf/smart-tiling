"""
Scroll command building and execution module.
Handles command construction and batching for atomic execution.
"""
from typing import List, Dict, Any


class CommandBuilder:
    """Builder for Scroll-specific commands."""
    
    def __init__(self):
        self.commands: List[str] = []
    
    def set_mode(self, mode: str, modifier: str = None) -> 'CommandBuilder':
        """Add a mode setting command."""
        cmd = f"set_mode {mode}"
        if modifier:
            cmd += f" {modifier}"
        self.commands.append(cmd)
        return self
    
    def resize(self, dimension: str, value: str) -> 'CommandBuilder':
        """Add a resize command."""
        self.commands.append(f"resize set {dimension} {value}")
        return self
    
    def build(self) -> List[str]:
        """Build and return the command list."""
        return self.commands.copy()


def execute_command_batch(connection, commands: List[str], atomic: bool = True):
    """Execute a batch of commands."""
    results = []
    for cmd in commands:
        try:
            result = connection.command(cmd)
            results.append(result)
        except Exception as e:
            results.append({'success': False, 'error': str(e)})
    return results


def build_neovim_terminal_commands(size_ratio: float = 0.333) -> List[str]:
    """Build command sequence for Neovim terminal placement."""
    builder = CommandBuilder()
    return (builder
            .set_mode('v', 'after')
            .resize('width', f'{int(size_ratio * 100)} ppt')
            .build())