from my_toolbox import (
    catch_exception,
    memoize,
    not_none,
    singleton,
    throttle,
    timing_with_threshold,
    type_check,
    validate_args,
)


def test_memoize_caches_calls():
    counter = {"count": 0}

    @memoize
    def add(a, b):
        counter["count"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert counter["count"] == 1


def test_validate_and_type_and_not_none_guards():
    @validate_args(x=lambda v: v > 0)
    @type_check(x=int)
    @not_none
    def square(x):
        return x * x

    assert square(3) == 9

    try:
        square(-1)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        square("3")
        assert False, "Expected TypeError"
    except TypeError:
        pass


def test_singleton_and_catch_exception_and_throttle():
    @singleton
    class Cfg:
        def __init__(self, v=0):
            self.v = v

    a = Cfg(v=1)
    b = Cfg(v=2)
    assert a is b
    assert b.v == 1

    @catch_exception(ZeroDivisionError, fallback=-1)
    def div(x, y):
        return x / y

    assert div(6, 2) == 3
    assert div(6, 0) == -1

    calls = []

    @throttle(delay=999)
    def mark():
        calls.append(1)
        return True

    assert mark() is True
    assert mark() is None
    assert len(calls) == 1


def test_timing_with_threshold_preserves_result():
    @timing_with_threshold(threshold_ms=0)
    def f():
        return "ok"

    assert f() == "ok"
