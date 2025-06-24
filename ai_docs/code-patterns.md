# Code Patterns and Standards

## State Management Pattern
```python
class WindowState:
    def __init__(self):
        self._relationships = {}
        self._pending_rules = {}
        self._lock = threading.Lock()
    
    def add_relationship(self, child_id: str, parent_id: str, rule: str):
        with self._lock:
            self._relationships[child_id] = {
                'parent_id': parent_id,
                'rule': rule,
                'created_at': time.time()
            }
```

## Error Handling Pattern
```python
def apply_rule(container, rule):
    try:
        # Rule application
        result = execute_actions(container, rule.actions)
        if not result.success:
            logger.warning(f"Rule {rule.name} partially failed: {result.errors}")
        return result
    except Exception as e:
        logger.error(f"Rule {rule.name} failed: {e}", exc_info=True)
        # Always fall back to standard autotiling
        return RuleResult(success=False, fallback=True)
```

## IPC Pattern
```python
def safe_command(i3, command: str) -> bool:
    try:
        result = i3.command(command)
        return all(r.success for r in result)
    except Exception as e:
        logger.error(f"Command failed: {command}, error: {e}")
        return False
```

## Configuration Pattern
```python
@dataclass
class Rule:
    name: str
    parent: ParentMatcher
    child: ChildMatcher
    actions: List[Action]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Rule':
        # Validation during parsing
        if not data.get('name'):
            raise ValueError("Rule must have a name")
        # ...
```
