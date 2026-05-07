from my_toolbox.new_tools import (
    OperatorTools,
    filter_strings_by_pattern,
    get_dict_values,
    get_sequence_bounds,
)


def test_filter_by_method_and_map_method():
    names = ["bob", "james", "billy", "blake", "sandra"]
    assert OperatorTools.filter_by_method(names, "startswith", "b") == ["bob", "billy", "blake"]

    words = ["hello", "world"]
    assert OperatorTools.map_method(words, "upper") == ["HELLO", "WORLD"]


def test_extract_indices_and_keys_and_grouping():
    values = [1, 2, 3, 4, 5]
    assert OperatorTools.extract_indices(values, 0, -1) == (1, 5)

    users = [
        {"name": "Alice", "role": "admin", "age": 30},
        {"name": "Bob", "role": "user", "age": 25},
        {"name": "Charlie", "role": "admin", "age": 35},
    ]
    assert OperatorTools.extract_keys(users, "name", "age") == [
        ("Alice", 30),
        ("Bob", 25),
        ("Charlie", 35),
    ]

    grouped = OperatorTools.group_by_key(users, "role")
    assert set(grouped.keys()) == {"admin", "user"}
    assert len(grouped["admin"]) == 2


def test_convenience_functions():
    assert filter_strings_by_pattern(["alpha", "beta", "alfa"], "al") == ["alpha", "alfa"]
    assert get_dict_values([{"x": 1, "y": 2}, {"x": 3, "y": 4}], "x", "y") == [(1, 2), (3, 4)]
    assert get_sequence_bounds([10, 20, 30]) == (10, 30)
