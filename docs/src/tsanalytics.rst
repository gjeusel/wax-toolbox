Timeserie Analytics
---------------------

Examples:

.. ipython:: python

    from wax_toolbox.tsanalytics import analyse_datetimeindex

    idx_gap  # let's look at that pd.DatetimeIndex

    tsinfo = analyse_datetimeindex(idx_gap, start=start, end=end)
    tsinfo

    print('This timeserie got a (minimal) frequency of {}'.format(tsinfo.freq))
    print('This timeserie is sorted ? {}'.format(tsinfo.sorted))

    # continuous parts:
    tsinfo.continuous

    # gaps parts:
    tsinfo.gaps

    # duplicates if any:
    tsinfo.duplicates


.. automodule:: wax_toolbox.tsanalytics
    :members:
    :private-members: TSAnalytics, TzFixFail
