from my_toolbox import before_after, log_calls, requires, run_if


def test_run_if_returns_fallback_when_disabled():
    @run_if(lambda *_args, **_kwargs: False, fallback="blocked")
    def func():
        return "ok"

    assert func() == "blocked"


def test_requires_raises_permission_error():
    @requires(lambda *_args, **_kwargs: False, message="denied")
    def func():
        return "ok"

    try:
        func()
        assert False, "PermissionError was not raised"
    except PermissionError as exc:
        assert str(exc) == "denied"


def test_before_after_executes_callbacks():
    calls = []

    def before(*_args, **_kwargs):
        calls.append("before")

    def after(result, *_args, **_kwargs):
        calls.append(f"after:{result}")

    @before_after(before=before, after=after)
    def add(a, b):
        return a + b

    assert add(2, 3) == 5
    assert calls == ["before", "after:5"]


def test_log_calls_keeps_function_result():
    @log_calls(logfile=None, console=False)
    def mul(a, b):
        return a * b

    assert mul(3, 4) == 12
