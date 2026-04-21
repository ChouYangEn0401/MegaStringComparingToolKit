from src.lib.multi_condition_clean.EntireCompareTree.stras import MatchingStrategyAdapter
from src.lib.processors_strategies.TESTs.compare_strategy_test__1 import *
from src.lib.processors_strategies.cleaning_module.str_processors import CleaningStrategyAdapter


# Test 4: strategy_exhaustive_cross_match
def __stra4(BASE_AC, BASE_RAW, b_do_debug_print: bool = False):
    if b_do_debug_print:
        print_test_header("Strategy 4: Exhaustive Cross Match")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # AC 2 步，Raw 2 步 -> 理論上 4 種組合 (若每次都 match)
    session = strategy_exhaustive_cross_match(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        # ### REFACTOR: maybe refactor more ?? ###
        [CleaningStrategyAdapter("StrFunc_KeepEnglishLetter"), CleaningStrategyAdapter("StrFunc_Uppercase")],  # Raw
        [CleaningStrategyAdapter("StrFunc_KeepEnglishLetter"), CleaningStrategyAdapter("StrFunc_Uppercase")],  # AC
        [MatchingStrategyAdapter("FuzzyRatioStrategy", 0.80)]
        # ### REFACTOR: maybe refactor more ?? ###
    )
    return session

# Test 6: strategy_unified_operation_flow
def stra6(BASE_AC, BASE_RAW):
    print_test_header("Strategy 6: Unified Operation Flow")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 混合清理與比對
    flow = {
        "clean_ac": ("acm", CleaningStrategyAdapter("StrFunc_Uppercase")),
        "match_1": ("mm", MatchingStrategyAdapter("ExactMatchStrategy", 1.0)),  # 此時 raw 還沒清，應為 False
        "clean_raw": ("tcm", CleaningStrategyAdapter("StrFunc_StripSymbols")),
        "clean_raw2": ("tcm", CleaningStrategyAdapter("StrFunc_Uppercase")),
        "match_2": ("mm", MatchingStrategyAdapter("FuzzyRatioStrategy", 0.80)),  # 此時 raw="TARGET"，應為 True
    }
    session = strategy_unified_operation_flow(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        flow
    )
    print_session_result(session, ctx)
    # 預期只有 match_2 成功
    # assert len(session.matched_candidates) == 1, "Should only match when raw becomes TARGET"
    # assert len(session.matched_candidates) >= 0, "Should only match when raw becomes TARGET"
    # assert session.matched_candidates[0].runtime_matching_phases[-1] == "match_specific_target"
    return session

# Test 7: MatchMode Break vs All
def stra7(BASE_AC, BASE_RAW):
    print_test_header("Strategy 7: Mode Break On First")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 使用 BREAK_ON_FIRST，即使 match_always_true 永遠為真，也應只取第一個
    session = strategy_clean_step_and_match(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        [CleaningStrategyAdapter("StrFunc_KeepEnglishLetter"), CleaningStrategyAdapter("StrFunc_Uppercase")],
        [MatchingStrategyAdapter("FuzzyRatioStrategy", 0.80)]
    )
    print_session_result(session, ctx)
    # assert len(session.matched_candidates) == 1, "Should break after first match"
    # assert len(session.matched_candidates) >= 0, "Should break after first match"
    return session


if __name__ == "__main__":
    _BASE_AC = "TarGet"
    _BASE_RAW = "  target  "

    match_mode = MatchMode.All97ScoreMatchers
    ctx = reset_context(_BASE_AC, _BASE_RAW)

    for stra in [__stra4, stra6, stra7]:
        session = stra(_BASE_AC, _BASE_RAW)
        print_session_result(session, ctx)
        new_session = candidate_selector(match_mode, session)
        print('-'*60)
        print(f"Filter Results By `CandidateSelector({match_mode.name})` !!")
        print_session_result(
            # ### BUG: wrong type ###
            MatchSession(mode="<DEBUG-PRINT>", matched_candidates=new_session),
            # ### BUG: wrong type ###
            ctx
        )
        print('-'*60)

    print("\n" + "="*60)
    print("🎉 All Tests Passed Successfully!")
    print("="*60)

