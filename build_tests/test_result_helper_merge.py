import sys
import pandas as pd
sys.path.insert(0, '.')
from gui._tab_result_helper import _ensure_unique_columns

# Simulate match results
match_df = pd.DataFrame([
    ("q1", "b1", 0.8),
    ("q2", "b2", 0.9),
], columns=["query", "best_match", "score"])

# Simulate Table A where key is 'id' but there's another column literally named 'query'
pa_df = pd.DataFrame({
    'id': ['q1', 'q2'],
    'query': ['x1', 'x2'],
    'colA': ['a1', 'a2'],
})
sel_a = ['query', 'colA']
key_col = 'id'

# Build a_sub like the GUI code
a_sub = pa_df[[key_col] + [c for c in sel_a if c != key_col]].copy()
a_sub = a_sub.rename(columns={key_col: 'query'})
a_sub = _ensure_unique_columns(a_sub, suffix='_A')

base = match_df[['query', 'best_match', 'score']].copy()

try:
    res = base.merge(a_sub, on='query', how='left', suffixes=('', '_A'))
    print('MERGE OK')
    print(res)
except Exception as e:
    print('MERGE FAILED:', e)

# Also test unmatched frames uniqueness
ua_out = pa_df[[key_col, 'query', 'colA']].copy()
ua_out = ua_out.rename(columns={key_col: 'query'})
ua_out = _ensure_unique_columns(ua_out, suffix='_A')
print('\nUA_OUT columns:', ua_out.columns.tolist())
