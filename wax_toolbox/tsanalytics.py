"""
A module with timeseries analysis tools.
"""
import logging
from datetime import datetime, timedelta

import pandas as pd
import pytz
from pandas.api.types import is_datetimetz
from pandas.core.algorithms import mode
from pandas.tseries.frequencies import to_offset


def tz_convert_multiindex(ts, to_tz='UTC'):
    """Convert all aware indexes of multiIndex timeserie.
    It also checks first if the indexes are effectively aware.

    Args:
        ts (pd.Series with pd.DatetimeIndex): timeserie with multiindex.
        to_tz (str): timezone to be converted into.

    Returns:
        (pd.Series) with timezone converted.
    """
    for i in range(len(ts.index.levels)):
        assert is_datetimetz(ts.index.levels[i])
        ts.index = ts.index.set_levels(ts.index.levels[i].tz_convert(to_tz),
                                       level=i)
    return ts


def tz_localize_multiindex(ts, from_tz='UTC'):
    """Localize all naive indexes of multiIndex timeserie.
    It also checks first if the indexes are effectively naives.

    Args:
        ts (pd.Series with pd.DatetimeIndex): timeserie with multiindex.
        from_tz (str): timezone to be localized into.

    Returns:
        (pd.Series) with localized mutliindex.
    """
    for i in range(len(ts.index.levels)):
        assert not is_datetimetz(ts.index.levels[i])
        ts.index = ts.index.set_levels(ts.index.levels[i].tz_localize(from_tz),
                                       level=i)
    return ts


def detect_frequency(idx):
    """
    Return the most plausible frequency of pd.DatetimeIndex (even when gaps in it).
    It calculates the delta between element of the index (idx[1:] - idx[:1]),
    gets the 'mode' of the delta (most frequent delta) and transforms it into a
    frequency ('H','15T',...)

    Args:
        idx (pd.DatetimeIndex): datetime index to analyse.

    Returns:
        frequency (str)

    Note:
        A solution exists in pandas:

        .. code:: python

            from pandas.tseries.frequencies import _TimedeltaFrequencyInferer
            inferer = _TimedeltaFrequencyInferer(idx)
            freq = inferer.get_freq()

        But for timeseries with nonconstant frequencies
        (like for 'publication_date' of forecast timeseries),
        then the inferer.get_freq() return None.

        In those cases, we are going to return the smallest frequency possible.

    """
    if len(idx) < 2:
        raise ValueError(
            "Cannot detect frequency of index when index as less than two elements")

    # calculates the delta
    delta_idx = idx[1:] - idx[:-1]
    delta_mode = mode(delta_idx)

    if len(delta_mode) == 0:
        # if no clear mode, take the smallest delta_idx
        td = min(delta_idx)
    else:
        # infer frequency from most frequent timedelta
        td = delta_mode[0]

    return to_offset(td)


class TSAnalytics:

    """Wrapper for time serie analysis results.

    Args:
        freq (str): frequency
        sorted (bool): whether timeindex is sorted.
        continuous (list of datetime tuples): continuous segments.
        gaps (list of datetime tuples): gaps segments.
        duplicates (list of datetime): duplicated index.
    """

    def __init__(self, freq, sorted, continuous, gaps, duplicates):
        self.freq = freq
        self.sorted = sorted
        self.continuous = continuous
        self.gaps = gaps
        self.duplicates = duplicates

    def __repr__(self):
        s = "freq: {}\n".format(self.freq)
        s += "sorted: {}\n".format(self.sorted)
        s += "continuous: {}\n".format(self.continuous)
        s += "gaps: {}\n".format(self.gaps)
        s += "duplicates: {}\n".format(self.duplicates)
        return s


def analyse_datetimeindex(idx, start=None, end=None, freq=None):
    """Check if the given index is of type DatetimeIndex & is aware.
    Returns the implied frequency, a sorted flag, the list of continuous segment, the list of gap segments and the list of duplicated indices.
    Continuous and gaps segments are expressed as [start:end] (both side inclusive).
    If the index is not sorted, it will be sorted before checking for continuity.
    Specifying start and end check for gaps at beginning and end of the index.
    Specifying freq enforces control of gaps according to frequency.


    Args:
        idx (pd.DatetimeIndex): datetimeindex aware to be analysed
        start (datetime expression): from when to start the analysis.
            Defaults to None, which means from the lower bound of idx.
        start (datetime expression): from when to end the analysis.
            Defaults to None, which means from the upper bound of idx.
        freq (str): analyise on this frequency.
            Defaults to None, which means the idx actual frequency.

    Returns:
        (TSAnalytics namedtuple): freq, sorted, continuous, gaps, duplicates
    """
    assert isinstance(idx, pd.DatetimeIndex)

    if not is_datetimetz(idx):
        raise ValueError("Naive DatetimeIndex is forbidden for your own sake."
                         "idx={}".format(idx))

    if len(idx) < 2:
        return TSAnalytics(None, True, [], [], [])

    if start is None:
        start = idx[0]
    else:
        start = pd.Timestamp(start)

    if end is None:
        end = idx[-1]
    else:
        end = pd.Timestamp(end)

    if not is_datetimetz(pd.DatetimeIndex([start, end])):
        raise ValueError("One of the following date is not aware:\n"
                         "start={}\nend={}".format(
                             start, end))

    if freq is None:
        freq = detect_frequency(idx)

    if not idx.is_unique:
        duplicates_flag = idx.duplicated(keep="first")
        duplicates = idx[duplicates_flag].tolist()
        idx = idx[~duplicates_flag]
    else:
        duplicates = []

    sorted = idx.is_monotonic_increasing

    idx_full = pd.date_range(
        start=start, end=end, tz=idx.tz, freq=freq)
    sr_full = pd.Series(index=idx, data=1).reindex(idx_full, fill_value=0)
    sr_shift = sr_full.diff(1)

    # detect first item in start, stop
    first_changes = sr_full[sr_shift != 0.]
    last_changes = sr_full[sr_shift.shift(-1) != 0.]
    # stops = sr_full[sr_shift == -1.]
    assert len(first_changes) == len(last_changes)
    segments = {0: [], 1: []}
    for (ts, modes), (te, modee) in zip(first_changes.iteritems(), last_changes.iteritems()):
        assert modes == modee
        segments[modes].append((ts, te))

    return TSAnalytics(freq, sorted, segments[1], segments[0], duplicates)


def get_tz_info(tzname, limit_year=2000):
    """Get DST informations.

    Args:
        tzname (str): a timezone.
        limit_year (int): filter the DST transitions datetimes older than this
            given year.

    Returns:
        (tuple): 2-elements tuple containing:

            * tz (pytz.timezone): the converted string into timezone object.
            * df (pd.DataFrame): dataframe containing DST informations.

    .. ipython:: python

        from wax_toolbox.tsanalytics import get_tz_info
        tz, df = get_tz_info('CET')

        tz

        df.head(10)
    """
    if hasattr(tzname, "zone"):
        tzname = tzname.zone
    tz = pytz.timezone(tzname)
    df = pd.DataFrame({
        'timestamp': tz._utc_transition_times,
        'dstoffset': [i[1] for i in tz._transition_info],
    })

    # Keep only recent info
    df = df[df.timestamp > datetime(limit_year, 1, 1)]

    # Convert to aware the utc transition times
    df['timestamp'] = df['timestamp']

    return tz, df


class TzFixFail(Exception):
    def __init__(self, colname):
        msg = ("Unable to fix timezone for {}".format(colname))
        super().__init__(msg)


def tz_fix(df, time_col, from_tz='Europe/Brussels', split_by=None,
           dropval_on_fail=False):
    """Try to fix the timezone of a datetime column.

    Args:
        df (pd.DataFrame): dataframe to process.
        time_col (str): name of the column to be processed.
        from_tz (str): initial timezone of the naive time_col.
            Defaults to 'Europe/Brussels'
        split_by (str): Name of the column to split by.
            It is necessary when the dataframe go several series.
            Defaults to None.
        dropval_on_fail (bool):
            - if false, raise TzFixFail if couldn't resolve
            - if true, drop dst values if case of TzFixFail.

            Defaults to False.
    """
    # Convert `time_col` from tz timezone to UTC. Try to
    # correct dst transition inconsistencies if any.

    # split_by is necessary when the df contains several series
    if split_by:
        def fn(sub_df):
            return tz_fix(sub_df.copy(), time_col, from_tz)
        return pd.concat([fn(g) for _, g in df.groupby(split_by)])

    try:
        # convert timezone
        df[time_col] = df[time_col].dt.tz_localize(from_tz, ambiguous='infer')
        df[time_col] = df[time_col].dt.tz_convert('UTC')
        return df
    except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
        pass

    # Consider dst transitions over the df horizon
    tz, trans_df = get_tz_info(from_tz)
    trans_cond = ((
        trans_df['timestamp'] >= df[time_col].min() - timedelta(hours=2)
    ) & (
        trans_df['timestamp'] <= df[time_col].max()
    ))
    matches = trans_df[trans_cond][['dstoffset', 'timestamp']].values

    # Loop on the transitions and try to patch the dataframe
    for dstoffset, dst_hour_utc in matches:
        total_seconds = dstoffset.total_seconds()
        # Identify the naive dst_hour (in the previous timezone)
        dst_hour = tz.fromutc(dst_hour_utc)
        dst_hour = dst_hour.replace(tzinfo=None) - dstoffset

        logging.debug(
            'Fix timeseries @ %s', dst_hour)
        cond = (df[time_col] >= dst_hour) & (
            df[time_col] < dst_hour + timedelta(hours=1))
        if total_seconds == 3600:
            # Winter -> Summer transition, dst hour is skipped
            df = df[~cond].copy()

        elif total_seconds == 0:
            # Summer -> Winter transition, dst hour is repeated
            before = df[df[time_col] < dst_hour]
            after = df[df[time_col] >= dst_hour + timedelta(hours=1)]
            slot = df[cond].copy()
            unduplicated = slot.drop_duplicates(time_col)

            if len(slot) == len(unduplicated):
                df = pd.concat([before, slot, slot, after])
            elif len(slot) == 2 * len(unduplicated):
                # Sometimes mercure give us duplicated timestamp (good)
                # but sorted (bad, especially for sub-hourly series)
                slot['_duplicated'] = slot.duplicated(subset=time_col)
                slot['_hour'] = slot[time_col].dt.hour
                slot = slot.sort_values(by=['_hour', '_duplicated', time_col])
                slot = slot.drop(['_duplicated', '_hour'], axis=1)
                df = pd.concat([before, slot, after])
            else:
                if not dropval_on_fail:
                    raise TzFixFail(time_col)
                else:
                    df = pd.concat([before, after])

            # XXX the above may be incorrect if the dst hour is the
            # latest hour
        else:
            raise ValueError('Timezone transition unexpected (%s at %s)' % (
                from_tz, dst_hour_utc
            ))

    df[time_col] = df[time_col].dt.tz_localize(from_tz, ambiguous='infer')
    df[time_col] = df[time_col].dt.tz_convert('UTC')
    return df
