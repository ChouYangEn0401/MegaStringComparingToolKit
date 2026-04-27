from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test
from isd_str_sdk.str_matching.adapters import AbbrevExactMatchStrategy, PreprocessedAbbrevExactStrategy

TESTS = [
    ("National Taiwan University (NTU)", "National Taiwan University", True),
    ("National Taiwan University", "NTU", False),
    ("The University of California", "University California", False),
    ("Harvard University (HU)", "Harvard University", True),
    ("Massachusetts Institute of Technology", "MIT", False),
    ("MIT", "Massachusetts Institute of Technology (MIT)", True),
    ("MIT", "Massachusetts Institute of Technology, MIT", False),
    ("MIT", "Massachusetts Institute of Technology MIT", False),
    ("Massachusetts Institute of Technology", "MIT", False),
    # ("MIT", "Massachusetts Institute of Technology (MIT)", True),
    ("MIT", "Massachusetts Institute of Technology (MIT)", False),
    ("University of Oxford", "Oxford University", False),
    ("The National University of Singapore", "National University Singapore", False),
    # ("National Taiwan University", "N.T.U.", False),
    ("National Taiwan University", "N.T.U.", True),
    ("Random School", "Completely Different School", False),
    ("Vietnam National University - Ho Chi Minh City (VNU-HCM)", "Vietnam National University, Hochiminh City", True),
    ("Manipal Academy of Higher Education - Manipal University (MAHE)", "Manipal Academy of Higher Education", True),
    ("Central Queensland University Australia (CQUniversity)", "Central Queensland University", True),
]

if __name__ == "__main__":
    # run_strategy_test(AbbrevExactMatchStrategy, TESTS, "show_all")
    run_strategy_test(PreprocessedAbbrevExactStrategy, TESTS, "wrong_answer")
