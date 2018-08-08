import logging
from timeit import default_timer as timer

logger = logging.getLogger(__name__)


class Timer:
    """Simple timer focused on practical use.

    Args:
        label (str): label of the timer
        report_at_enter (bool): whether it should be also displayed when entering the context.
            Defaults to False.
        report_func (func): function to use for reporting. Defaults to logger.info
    """

    def __init__(self, label, report_at_enter=False, report_func=logger.info):
        self.label = label
        self.report_at_enter = report_at_enter
        self.report_func = report_func

    def __enter__(self):
        if self.report_at_enter:
            self.report_func("{} in progress...".format(self.label))
        self.start = timer()
        return self

    def __exit__(self, *args):
        self.end = timer()
        self.interval = self.end - self.start
        self.report_func("{0:s} took {1:.3f} sec".format(self.label, self.interval))
