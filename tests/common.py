# encoding: utf-8

import contextlib
from colorama import Fore, Style
import time


def output_wrapper(fn):
    def shim(*args, **kwargs):
        name = fn.__name__
        try:
            print("{} starting".format(name) + Style.RESET_ALL)
            fn(*args, **kwargs)
            print(Fore.GREEN + "{} completed".format(name) + Fore.RESET)
        except NotImplementedError as e:
            print(Fore.YELLOW + "{} not implemented: {}".format(name, e) + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + "{} failed ({}): {}".format(name, type(e).__name__, e) + Style.RESET_ALL)

    shim.__name__ = fn.__name__
    return shim


class Test(object):
    def __init__(self):
        self.all_tests = []

    def __call__(self, fn):
        self.all_tests.append(output_wrapper(fn))


test = Test()


def file_exists(client, path):
    return must_run(client, "[ -e {} ]".format(path)) == 0


def must_run(client, command):
    chan = client.get_transport().open_session()
    chan.exec_command(command)
    ret = chan.recv_exit_status()
    chan.close()
    return ret
