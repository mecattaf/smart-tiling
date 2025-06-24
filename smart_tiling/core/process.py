"""
Process tree analysis module for smart-tiling.
Handles process tree traversal and working directory extraction.
"""
import os
from typing import List, Dict, Optional, Any


def get_process_cwd(pid):
    """
    Extract working directory from /proc/{pid}/cwd.
    
    Args:
        pid: Process ID
        
    Returns:
        str: Working directory path or None if not accessible
    """
    try:
        return os.readlink(f'/proc/{pid}/cwd')
    except (OSError, FileNotFoundError):
        return None


def find_child_processes(parent_pid: int) -> List[int]:
    """
    Find child processes of a given parent PID.
    
    Args:
        parent_pid: Parent process ID
        
    Returns:
        list: List of child process IDs
    """
    child_pids = []
    
    try:
        # Parse /proc directory to find all processes
        for proc_dir in os.listdir('/proc'):
            if not proc_dir.isdigit():
                continue
                
            try:
                # Read /proc/{pid}/stat to get parent PID
                with open(f'/proc/{proc_dir}/stat', 'r') as f:
                    stat_fields = f.read().split()
                    if len(stat_fields) >= 4:
                        # Field 4 (index 3) is the parent PID
                        ppid = int(stat_fields[3])
                        if ppid == parent_pid:
                            child_pids.append(int(proc_dir))
            except (OSError, ValueError, IndexError):
                # Skip processes we can't read or parse
                continue
                
    except OSError:
        # Can't access /proc directory
        pass
    
    return child_pids


def traverse_process_tree(pid: int, max_depth: int = 3) -> Dict[str, Any]:
    """
    Traverse process tree starting from given PID.
    
    Args:
        pid: Starting process ID
        max_depth: Maximum depth to traverse
        
    Returns:
        dict: Process tree information
    """
    def _traverse_recursive(current_pid: int, depth: int) -> Dict[str, Any]:
        if depth > max_depth:
            return {}
        
        process_info = get_process_info(current_pid)
        if not process_info:
            return {}
        
        # Find children and traverse them
        children = find_child_processes(current_pid)
        child_info = {}
        
        for child_pid in children:
            child_info[child_pid] = _traverse_recursive(child_pid, depth + 1)
        
        return {
            'pid': current_pid,
            'info': process_info,
            'children': child_info
        }
    
    return _traverse_recursive(pid, 0)


def get_process_info(pid: int) -> Dict[str, Optional[str]]:
    """
    Get detailed process information.
    
    Args:
        pid: Process ID
        
    Returns:
        dict: Process information including name, command, cwd
    """
    info = {
        'name': None,
        'command': None,
        'cwd': None
    }
    
    try:
        # Read process name from /proc/{pid}/comm
        try:
            with open(f'/proc/{pid}/comm', 'r') as f:
                info['name'] = f.read().strip()
        except (OSError, FileNotFoundError):
            pass
        
        # Read command line from /proc/{pid}/cmdline
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmdline = f.read()
                # cmdline is null-separated, convert to space-separated
                if cmdline:
                    info['command'] = ' '.join(cmdline.split('\0')).strip()
        except (OSError, FileNotFoundError):
            pass
        
        # Get working directory
        info['cwd'] = get_process_cwd(pid)
        
    except Exception:
        # Return empty info if we can't read anything
        pass
    
    return info