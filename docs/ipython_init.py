import pandas as pd

start = pd.Timestamp("2016-03-01", tz='CET')
end = pd.Timestamp("2016-03-31", tz='CET')
idx = pd.date_range(start, end, freq='H', closed=None, tz='CET')

gaps = [(0, 2), (5, 7), (10, 14)]

# build index with gaps
mask = pd.Series(True, index=idx)
for s, e in gaps:
    mask[s:e] = False
idx_gap = idx[mask]

# rework gaps to include end point
# -10000 are sentinel values never used
gaps = [(-10000, 0)] + gaps + [(0, -10000)]
gaps = [(s, min(e, len(idx) - 1)) for (s, e) in gaps]  # cap the index

# calculate segments
base_gap_segments = [(idx[s - 1], idx[e]) for s, e in gaps[1:-1]]
base_cont_segments = [(idx[s], idx[e - 1])
                      for (_, s), (e, _) in zip(gaps, gaps[1:])]

# handle special cases
if len(gaps) == 2:
    # original gap was empty
    base_cont_segments = [(idx[0], idx[-1])]
    base_gap_segments = []
elif gaps[1][0] == 0:
    base_cont_segments = base_cont_segments[1:]
    base_gap_segments = base_gap_segments[1:]
elif gaps[-2][1] == len(idx) - 1:
    base_cont_segments = base_cont_segments[:-1]
    base_gap_segments = base_gap_segments[:-1]
