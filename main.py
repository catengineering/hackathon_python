# encoding: utf-8

import sys
import datetime as dt

# Please do not remove this check; this test suite is intended to only run
# on Python 3. This may be backwards portable to Python 2.7 fairly easily,
# but there's no intention of doing so at this time.
if sys.version_info.major != 3:
    days_until_eol = (dt.datetime(year=2020, month=1, day=1) - dt.datetime.utcnow()).days
    print("""\
This test suite only runs on Python 3. Python 2.7 will be end of life on
January 1st, 2020. That's in {} days.

Key integrations on the platform will all depend on a modern Python runtime.

Please ensure that all submissions run correctly under Python 3.
""".format(days_until_eol))
    sys.exit(1)


def dep_check(*modules):
    error = False
    for module in modules:
        import importlib
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            error = True
            print("Dependency missing: {}".format(module))
    if error:
        sys.exit(2)

dep_check("colorama", "sqlalchemy", "paramiko")


from colorama import Fore, Style
import contextlib
from tests import test, metrics
import vendor


@contextlib.contextmanager
def test_environment():
    print(Fore.WHITE + Style.BRIGHT + "Initializing environment" + Style.RESET_ALL)
    vendor.setup_environment()
    try:
        yield
    finally:
        print(Fore.WHITE + Style.BRIGHT + "Tearing down environment" + Style.RESET_ALL)
        vendor.teardown_environment()


def main(*args):

    for helper in [
        vendor.create_compute_instance,
        vendor.create_object_storage_instance,
        vendor.create_block_storage_instance,
        vendor.create_relational_database_instance,
    ]:
        if not hasattr(helper, "has_metrics"):
            print(Fore.RED + Style.BRIGHT +
                  "Metrics decorator has been removed from {}".format(
                      helper.__name__) + Style.RESET_ALL)


    with test_environment():
        print("")
        for case in test.all_tests:
            case()
            print("")
    print(Fore.GREEN + Style.BRIGHT + "\nRun complete. Metrics:" + Style.RESET_ALL)
    metrics.output()


if __name__ == "__main__":
    main(*sys.argv[1:])
