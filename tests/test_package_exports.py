import my_toolbox


def test_expected_exports_are_available():
    assert hasattr(my_toolbox, "before_after")
    assert hasattr(my_toolbox, "log_calls")
    assert hasattr(my_toolbox, "requires")
    assert hasattr(my_toolbox, "run_if")
