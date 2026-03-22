from manana.hook import activate
from manana.profiler import register_atexit_reporter

activate()
register_atexit_reporter()

import json
import random
import math

_ = json.dumps({"ok": True})
_ = math.sqrt(9)

