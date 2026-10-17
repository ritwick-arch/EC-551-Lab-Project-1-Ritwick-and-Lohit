
"""Op number -> function returning the report for one output."""

from . import canonical, reports

OPS = {
    1: canonical.op1,
    2: canonical.op2,
    3: canonical.op3,
    4: canonical.op4,
    5: reports.op5,
    6: reports.op6,
    7: reports.op7,
    8: reports.op8,
    9: canonical.op9,
    10: canonical.op10,
    11: reports.op11,
    12: reports.op12,
}
