from isd_str_compare.legacy.EntireCompareTree.test.in_variant_matcher import rank_candidates, score_candidate


def test_case_1_typo_ranking():
    query = "natl taiwan univ"
    cands = ["natl taiwan university", "natl taiwan univeristy"]
    ranked = rank_candidates(query, cands)
    assert ranked[0][0] == "natl taiwan university"
    print(ranked, '\n')


def test_case_2_extra_words_penalty():
    query = "natl taiwan univ"
    cands = [
        "national tiawan university",
        "university national taiwan",
        "national taiwan university",
        "national taiwan university of science and technology",
    ]
    ranked = rank_candidates(query, cands)
    # assert ranked[0][0] == "national taiwan university"
    print(ranked, '\n')


def test_case_3_negative_prompt():
    query = "chang gang univ"
    cands = ["chang gang univ dept", "chang gang univ hosp", "chang gang univ hospital", "chang gang univ coll"]
    ranked = rank_candidates(query, cands, negative_tokens=["-hosp", "-dept"])
    # assert ranked[0][0] == "chang gang univ coll"
    assert score_candidate(query, "chang gang univ dept", negative_tokens=["-dept"]).rejected_by_negative_prompt
    print(ranked, '\n')


if __name__ == "__main__":
    test_case_1_typo_ranking()
    test_case_2_extra_words_penalty()
    test_case_3_negative_prompt()


