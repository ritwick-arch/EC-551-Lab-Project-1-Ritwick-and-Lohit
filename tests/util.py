def table(n, fn):
    """Truth table of fn over n inputs, first input = MSB."""
    return sum(1 << m for m in range(1 << n) if fn(*[(m >> (n - 1 - i)) & 1 for i in range(n)]))


def tool(env, default):
    """Path to an external tool (overridable through an environment variable), or skip the test."""
    import os
    from pathlib import Path

    import pytest
    path = os.environ.get(env, default)
    if not Path(path).exists():
        pytest.skip(f"{path} not found; set {env}")
    return path
