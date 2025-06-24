"""
Context detection module for smart-tiling.
Detects application type from container properties.
"""

import fnmatch
from typing import Optional, List, Dict, Any


def detect_app_context(container) -> Dict[str, Any]:
    """
    Detect application type from container properties.
    
    Args:
        container: i3ipc container object
        
    Returns:
        dict: Context information including app_id, window_class, title, pid
    """
    app_id = extract_app_id(container)
    window_class = extract_window_class(container)
    
    # Extract window instance (X11 specific)
    window_instance = None
    raw_window_class = getattr(container, 'window_class', None)
    if isinstance(raw_window_class, list) and len(raw_window_class) > 1:
        window_instance = raw_window_class[1]
    
    return {
        'app_id': app_id,
        'window_class': window_class,
        'window_instance': window_instance,
        'title': getattr(container, 'name', None),
        'pid': getattr(container, 'pid', None)
    }


def extract_app_id(container) -> Optional[str]:
    """Extract app_id from Wayland container."""
    return getattr(container, 'app_id', None)


def extract_window_class(container) -> Optional[str]:
    """Extract window class from X11 container.
    
    Handles case where window_class is a list (X11 returns [instance, class]).
    Returns the class part (usually index 0).
    """
    window_class = getattr(container, 'window_class', None)
    
    if window_class is None:
        return None
    
    if isinstance(window_class, list) and len(window_class) > 0:
        return window_class[0]
    
    return str(window_class) if window_class else None


def match_title_pattern(title: Optional[str], patterns: List[str]) -> bool:
    """Match window title against patterns.
    
    Uses glob pattern matching (fnmatch) that is case-insensitive.
    Safely handles None values.
    
    Args:
        title: Window title to match against
        patterns: List of glob patterns (e.g., ['*nvim*', '*vim*'])
        
    Returns:
        bool: True if title matches any pattern
    """
    if not title or not patterns:
        return False
    
    title_lower = title.lower()
    
    for pattern in patterns:
        if pattern and fnmatch.fnmatch(title_lower, pattern.lower()):
            return True
    
    return False


def matches_app_context(container, **criteria) -> bool:
    """Generic function to match container against application criteria.
    
    Args:
        container: i3ipc container object
        **criteria: Matching criteria including:
            - app_id_list: List of app_ids to match against
            - window_class_list: List of window classes to match against
            - title_patterns: List of glob patterns for title matching
    
    Returns:
        bool: True if container matches any of the provided criteria
    """
    context = detect_app_context(container)
    
    # Check app_id criteria
    app_id_list = criteria.get('app_id_list', [])
    if app_id_list and context['app_id'] in app_id_list:
        return True
    
    # Check window_class criteria  
    window_class_list = criteria.get('window_class_list', [])
    if window_class_list and context['window_class'] in window_class_list:
        return True
    
    # Check title pattern criteria
    title_patterns = criteria.get('title_patterns', [])
    if title_patterns and match_title_pattern(context['title'], title_patterns):
        return True
    
    return False