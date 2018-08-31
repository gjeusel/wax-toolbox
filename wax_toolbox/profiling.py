import logging
from timeit import default_timer as timer

logger = logging.getLogger(__name__)


class Timer:
    """Simple timer focused on practical use.

    Args:
        label (str): label of the timer
        at_enter (bool): whether it should be also displayed when entering the context.
            Defaults to False.
        report (func): function to use for reporting. Defaults to logger.info
    """

    def __init__(self, label, at_enter=False, report=print):
        self.label = label
        self.at_enter = at_enter
        self.report = report

    def __enter__(self):
        if self.at_enter:
            self.report("{} in progress...".format(self.label))
        self.start = timer()
        return self

    def __exit__(self, *args):
        self.end = timer()
        self.interval = self.end - self.start
        self.report("{0:s} took {1:.3f} sec".format(self.label, self.interval))
