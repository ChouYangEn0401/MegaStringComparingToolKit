from isd_str_sdk.str_cleaning import StrFunc_KeepEnglishParenthesesAndSpaces
from .run_strategy_tests import run_str_processor_test

TESTS = [
    ("N><_=ational %@#@Taiwan U@$nive^@rsity (NTU)", "National Taiwan University (NTU)",),
    ("<N>ati_on=al Ta%@iw#an@ U@$nive^@rsity (NTU)", "National Taiwan University (NTU)",),
]

run_str_processor_test(
    StrFunc_KeepEnglishParenthesesAndSpaces,
    TESTS,
    "show_all",
)
