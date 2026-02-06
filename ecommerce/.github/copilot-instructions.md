# Copilot Instructions

## Docstrings

- **Always** include docstrings for all classes, methods, and functions.
- Use the following format for docstrings:

### Module Docstrings

```python
"""
Brief description of the module's purpose.
"""
```

### Class Docstrings

```python
class MyClass:
    """
    Brief description of the class.

    Attributes:
        attribute_name (type): Description of the attribute.
    """
```

### Function/Method Docstrings

```python
def my_function(param1, param2):
    """
    Brief description of the function.

    Args:
        param1 (type): Description of param1.
        param2 (type): Description of param2.

    Returns:
        type: Description of return value.

    Raises:
        ExceptionType: Description of when this exception is raised.
    """
```

## Flake8 Formatting

Follow flake8 style guidelines:

- **Line Length**: Maximum 79 characters for code, 72 for docstrings/comments.
- **Indentation**: Use 4 spaces per indentation level. Never use tabs.
- **Blank Lines**:
  - 2 blank lines before top-level function and class definitions.
  - 1 blank line between method definitions inside a class.
- **Imports**:
  - Place imports at the top of the file.
  - Group imports in the following order: standard library, third-party, local.
  - Use absolute imports over relative imports when possible.
  - Avoid wildcard imports (`from module import *`).
- **Whitespace**:
  - No trailing whitespace.
  - No whitespace immediately inside parentheses, brackets, or braces.
  - Use a single space around binary operators (`=`, `+=`, `==`, etc.).
  - No space before a colon in slices (`list[1:2]`).
- **Naming Conventions**:
  - `snake_case` for functions, methods, and variables.
  - `PascalCase` for class names.
  - `UPPER_CASE` for constants.
- **Avoid**:
  - Unused imports and variables.
  - Bare `except:` clauses; always specify the exception type.
  - Mutable default arguments in function definitions.

## Type Hints

- **Always** include type hints for function parameters and return types.
- Use type hints for class attributes where applicable.
- Import types from `typing` module when needed (e.g., `List`, `Dict`, `Optional`, `Union`).
- Use the following format for type hints:

### Function/Method Type Hints

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Args:
        param1 (str): Description of param1.
        param2 (int): Description of param2.

    Returns:
        bool: Description of return value.
    """
    return True
```

### Optional and Union Types

```python
from typing import Optional, Union

def get_user(user_id: int) -> Optional[User]:
    """Return user or None if not found."""
    pass

def process_input(data: Union[str, bytes]) -> str:
    """Process string or bytes input."""
    pass
```

### Class Attributes with Type Hints

```python
from typing import List

class MyClass:
    """
    Brief description of the class.

    Attributes:
        name (str): The name of the instance.
        items (List[str]): A list of item names.
    """

    name: str
    items: List[str]

    def __init__(self, name: str) -> None:
        self.name = name
        self.items = []
```

### Common Type Hints

- `str`, `int`, `float`, `bool` for primitive types.
- `List[T]`, `Dict[K, V]`, `Set[T]`, `Tuple[T, ...]` for collections.
- `Optional[T]` for values that can be `None`.
- `Union[T1, T2]` for multiple possible types.
- `Any` when the type is truly dynamic (use sparingly).
- `Callable[[ArgTypes], ReturnType]` for function types.
