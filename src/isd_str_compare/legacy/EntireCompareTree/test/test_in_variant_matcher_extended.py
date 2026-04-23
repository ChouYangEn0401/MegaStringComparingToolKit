from isd_str_compare.legacy.EntireCompareTree.test.in_variant_matcher import (
    score_candidate,
    rank_candidates,
    rank_typo_candidates,
)


def test_negative_modes_exact():
    q = "chang gang univ"
    c = "chang gang univ dept"
    assert score_candidate(q, c, negative_tokens=['-dept'], negative_mode='exact').rejected_by_negative_prompt


def test_negative_modes_boundary():
    q = "chang gang univ"
    # use a token that starts with 'dept' so boundary mode triggers
    c = "chang gang univ depthosp"
    assert score_candidate(q, c, negative_tokens=['-dept'], negative_mode='boundary').rejected_by_negative_prompt


def test_negative_modes_in():
    q = "chang gang univ"
    c = "chang gang univ superdept"
    assert score_candidate(q, c, negative_tokens=['-dept'], negative_mode='in').rejected_by_negative_prompt


def test_negative_modes_fuzzy():
    q = "chang gang univ"
    c = "chang gang univ dpt"
    # 'dpt' should be fuzzy-similar to 'dept'
    assert score_candidate(q, c, negative_tokens=['-dept'], negative_mode='fuzzy', negative_fuzzy_threshold=0.7).rejected_by_negative_prompt


def test_out_of_order_default_no_penalty():
    q = "a b c"
    c1 = "a b c"
    c2 = "c b a"
    r = rank_candidates(q, [c1, c2])
    assert r[0][0] == c1


def test_out_of_order_with_penalty():
    q = "a b c"
    c1 = "a b c"
    c2 = "c b a"
    r = rank_candidates(q, [c1, c2], penalize_out_of_order=True, out_of_order_penalty=0.5)
    assert r[0][0] == c1


def test_tie_breaking_coverage():
    q = "natl taiwan univ"
    cands = [
        "natl taiwan university",
        "natl taiwan univeristy",
    ]
    r = rank_candidates(q, cands)
    assert r[0][0] == "natl taiwan university"


def test_rank_typo_candidates_natlexamples():
    q = "NATL TAIWAN UNIV"
    cands = [
        "NATL TAI WAN UNIV",
        "NATLTAIWAN UNIV",
        "NALT TIAWAN UVNIVERSITY",
    ]
    r = rank_typo_candidates(q, cands)
    assert r[0][0] == "NATL TAI WAN UNIV"
    assert r[1][0] == "NATLTAIWAN UNIV"


if __name__ == '__main__':
    test_negative_modes_exact()
    test_negative_modes_boundary()
    test_negative_modes_in()
    test_negative_modes_fuzzy()
    test_out_of_order_default_no_penalty()
    test_out_of_order_with_penalty()
    test_tie_breaking_coverage()
    test_rank_typo_candidates_natlexamples()
    print('extended tests ran successfully')
