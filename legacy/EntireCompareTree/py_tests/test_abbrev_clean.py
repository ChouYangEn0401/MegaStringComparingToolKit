from src.lib.multi_condition_clean.EntireCompareTree.py_tests.run_strategy_tests import run_strategy_test
from src.lib.multi_condition_clean.EntireCompareTree.stras import AbbrevExactMatchStrategy, PreprocessedAbbrevExactStrategy

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
