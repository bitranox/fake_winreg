import platform

collect_ignore = ['build_docs.py', '__main__.py']


def pytest_cmdline_preparse(args):
    """
    # run tests on multiple processes if pytest-xdist plugin is available
    # unfortunately it does not work with codecov
    import sys
    if "xdist" in sys.modules:  # pytest-xdist plugin
        import multiprocessing

        num = int(max(multiprocessing.cpu_count() / 2, 1))
        args[:] = ["-n", str(num)] + args
    """

    # add mypy option if not pypy - so mypy will be called with setup.py install test
    if platform.python_implementation() != "PyPy":
        args[:] = ["--mypy"] + args
