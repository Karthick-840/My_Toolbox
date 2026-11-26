"""
Operator utilities for functional programming and data extraction.

Useful for filtering, mapping, and extracting data from collections
in web apps, ETL pipelines, and data processing workflows.
Uses operator.methodcaller and operator.itemgetter for clean, efficient operations.
"""

from operator import methodcaller, itemgetter
from typing import Any, Callable, List, Tuple, TypeVar, Generic

T = TypeVar('T')


class OperatorTools:
    """Tools for functional programming using Python's operator module."""

    @staticmethod
    def filter_by_method(collection: List[Any], method_name: str, *args, **kwargs) -> List[Any]:
        """
        Filter items in a collection by calling a method on each.
        
        Args:
            collection: List of objects to filter
            method_name: Name of method to call (e.g., 'startswith')
            *args: Arguments to pass to method
            **kwargs: Keyword arguments to pass to method
            
        Returns:
            List of items where method call returned True
            
        Example:
            names = ["bob", "james", "billy", "blake", "sandra"]
            starts_with_b = OperatorTools.filter_by_method(names, 'startswith', 'b')
            # Returns: ["bob", "billy", "blake"]
        """
        caller = methodcaller(method_name, *args, **kwargs)
        return list(filter(caller, collection))

    @staticmethod
    def extract_indices(sequence: List[T], *indices: int) -> Tuple[T, ...]:
        """
        Extract specific indices from a sequence.
        
        Args:
            sequence: List or sequence to extract from
            *indices: Index positions to extract (can be negative)
            
        Returns:
            Tuple of items at specified indices
            
        Example:
            elements = [1, 2, 3, 4, 5]
            first_and_last = OperatorTools.extract_indices(elements, 0, -1)
            # Returns: (1, 5)
        """
        getter = itemgetter(*indices)
        return getter(sequence)

    @staticmethod
    def extract_keys(dict_list: List[dict], *keys: str) -> List[Tuple]:
        """
        Extract specific keys from list of dictionaries.
        
        Args:
            dict_list: List of dictionaries
            *keys: Keys to extract
            
        Returns:
            List of tuples containing values for specified keys
            
        Example:
            users = [
                {'name': 'Alice', 'age': 30, 'city': 'NYC'},
                {'name': 'Bob', 'age': 25, 'city': 'LA'}
            ]
            names_ages = OperatorTools.extract_keys(users, 'name', 'age')
            # Returns: [('Alice', 30), ('Bob', 25)]
        """
        getter = itemgetter(*keys)
        return [getter(d) for d in dict_list]

    @staticmethod
    def map_method(collection: List[Any], method_name: str, *args, **kwargs) -> List[Any]:
        """
        Map a method call across all items in a collection.
        
        Args:
            collection: List of objects
            method_name: Name of method to call
            *args: Arguments to pass to method
            **kwargs: Keyword arguments to pass to method
            
        Returns:
            List of method call results
            
        Example:
            words = ["hello", "world", "python"]
            uppercase = OperatorTools.map_method(words, 'upper')
            # Returns: ["HELLO", "WORLD", "PYTHON"]
        """
        caller = methodcaller(method_name, *args, **kwargs)
        return list(map(caller, collection))

    @staticmethod
    def group_by_key(dict_list: List[dict], key: str) -> dict:
        """
        Group list of dictionaries by a specific key value.
        
        Args:
            dict_list: List of dictionaries
            key: Key to group by
            
        Returns:
            Dictionary with key values as keys and lists of dicts as values
            
        Example:
            users = [
                {'name': 'Alice', 'role': 'admin'},
                {'name': 'Bob', 'role': 'user'},
                {'name': 'Charlie', 'role': 'admin'}
            ]
            by_role = OperatorTools.group_by_key(users, 'role')
            # Returns: {
            #     'admin': [{'name': 'Alice', ...}, {'name': 'Charlie', ...}],
            #     'user': [{'name': 'Bob', ...}]
            # }
        """
        result = {}
        getter = itemgetter(key)
        for item in dict_list:
            group_val = getter(item)
            if group_val not in result:
                result[group_val] = []
            result[group_val].append(item)
        return result

    @staticmethod
    def chain_operations(value: Any, *operations: Tuple[Callable, Tuple]) -> Any:
        """
        Chain multiple operations/method calls on a value.
        
        Args:
            value: Initial value
            *operations: Tuples of (callable, args) to apply sequentially
            
        Returns:
            Result after all operations applied
            
        Example:
            # Chain: "  hello  " -> strip -> upper
            result = OperatorTools.chain_operations(
                "  hello  ",
                (str.strip, ()),
                (str.upper, ())
            )
            # Returns: "HELLO"
        """
        result = value
        for func, args in operations:
            result = func(result, *args) if args else func(result)
        return result


# Convenience functions for common operations
def filter_strings_by_pattern(strings: List[str], pattern: str, method: str = 'startswith') -> List[str]:
    """Filter list of strings by a pattern using specified string method."""
    return OperatorTools.filter_by_method(strings, method, pattern)


def get_dict_values(dict_list: List[dict], *keys: str) -> List[Tuple]:
    """Extract specific keys from list of dictionaries."""
    return OperatorTools.extract_keys(dict_list, *keys)


def get_sequence_bounds(sequence: List[T]) -> Tuple[T, T]:
    """Get first and last elements of a sequence."""
    return OperatorTools.extract_indices(sequence, 0, -1)
