#!/usr/bin/env python3
"""Docstring template for MarketData skill scripts."""

TEMPLATE = '''"""[One-line summary of what this function does]

[Optional 2-3 line context about when/why to use this]

Args:
    param1 (type): Description with example values (e.g., "AAPL", "SPY")
    param2 (type): Description with default behavior (default: value)

Returns:
    dict: {
        "field1": type,  # Description of field
        "field2": type,  # Description of field
        "nested": {
            "subfield": type  # Description
        }
    }

Example:
    >>> function_name("input_value")
    {
        "output": "value",
        "nested": {"key": "value"}
    }

Use Cases:
    - Primary use case with specific scenario
    - Secondary use case with context
    - When NOT to use this (if relevant)

Notes:
    - Important edge cases or limitations
    - Performance considerations
    - Data quality notes

See Also:
    - related_function.py: Related functionality
    - another_category/function.py: Alternative approach
"""'''


# Validation function
def validate_docstring(docstring: str) -> bool:
    """Check if docstring has all required sections."""
    required = ["Args:", "Returns:", "Example:"]
    recommended = ["Use Cases:", "Notes:", "See Also:"]

    has_required = all(section in docstring for section in required)
    has_recommended = sum(section in docstring for section in recommended) >= 2

    return has_required and has_recommended


if __name__ == "__main__":
    print(TEMPLATE)
