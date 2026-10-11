"""Op number -> function that returns that op's report for one output."""
from . import canonical

OPS = {
    1: canonical.op1, 2: canonical.op2, 3: canonical.op3, 4: canonical.op4,
    9: canonical.op9, 10: canonical.op10,
}
