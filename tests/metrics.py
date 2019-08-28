import time
import contextlib
import collections
from colorama import Fore, Style


class Metrics(object):
    def __init__(self):
        self.measurements = collections.defaultdict(list)

    def measure(self, caller, name, started_at, yielded_at, external_completed_at, cleanup_completed_at):
        startup_time = yielded_at - started_at
        external_time = external_completed_at - yielded_at
        cleanup_time = cleanup_completed_at - external_completed_at
        self.measurements[caller].append({
            "name": name,
            "startup_time": startup_time,
            "external_time": external_time,
            "cleanup_time": cleanup_time,
        })

    def output(self):
        for (caller, measurements) in self.measurements.items():
            print("")
            print(Fore.WHITE + Style.BRIGHT + caller + Style.RESET_ALL)
            prefix = iter((["├"] * (len(measurements)-1)) + ["└"])

            for measurement in measurements:
                print(" {prefix} {name} startup {startup_time:0.2f}s external {external_time:0.2f}s cleanup {cleanup_time:0.2f}s".format(prefix=next(prefix), **measurement))

    def __call__(self, fn):
        @contextlib.contextmanager
        def inner(*args, **kwargs):
            import inspect
            caller = inspect.stack()[2].function

            started_at = time.time()
            with fn(*args, **kwargs) as d:
                yielded_at = time.time()
                yield d
                external_completed_at = time.time()
            cleanup_completed_at = time.time()
            self.measure(caller, fn.__name__, started_at, yielded_at, external_completed_at, cleanup_completed_at)
        inner.has_metrics = True
        return inner

metrics = Metrics()
