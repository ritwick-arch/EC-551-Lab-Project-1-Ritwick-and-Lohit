def table(n, fn):
    """Truth table of fn over n inputs, first input = MSB."""
    return sum(1 << m for m in range(1 << n) if fn(*[(m >> (n - 1 - i)) & 1 for i in range(n)]))
