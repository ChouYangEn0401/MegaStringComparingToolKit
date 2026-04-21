import sys
import pprint

# ensure the test module directory is on path
sys.path.insert(0, r"c:\Users\629\Desktop\周暘恩\NTUAuthorityControlAnalysis2025\NTUAuthorityControlMain\src\lib\multi_condition_clean\EntireCompareTree\test")
from isd_str_compare.legacy.EntireCompareTree.test.in_variant_matcher import rank_candidates

q = "NATL TAIWAN UNIV"
cands = [
    "NATL TAI WAN UNIV",
    "NATLTAIWAN UNIV",
    "NALT TIAWAN UVNIVERSITY",
]

print('Query:', q)
print('Candidates:')
for c in cands:
    print('-', c)

res = rank_candidates(q, cands)
print('\nRanked results:')
pp = pprint.PrettyPrinter(width=140)
pp.pprint(res)
