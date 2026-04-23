"""
# 直接呼叫
from isd_str_sdk.matching_tools import fuzzy_compare, lcs_similarity
score = fuzzy_compare("MIT", "M.I.T.")

# Dispatcher（字串 key 或 callable 都支援）
from isd_str_sdk.matching_tools import matcher
score = matcher("fuzzy_compare", "abc", "zyx")
score = matcher(fuzzy_compare, "abc", "zyx")

# 清洗
from isd_str_sdk.cleaning_tools import lowercase, cleaner
s = cleaner("normalize_whitespace", "  hello   world  ")
s = cleaner(lowercase, "MIT University")
# 帶參數的清洗函式
s = cleaner("remove_specific_symbols", "hello!", ["!"])


from isd_str_sdk.cleaning_tools import func1
str_ = func1("zyx", ...)
或者
from isd_str_sdk.cleaning_tools import func1
cleaner("func1", "abc", ...)
cleaner(func1, "abc", ...)

"""

我想要這麼用