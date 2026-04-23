from src.lib.processors_strategies.TESTs.compare_strategy_test__1 import *

def core_runner(
        acs, raws,
        text_cleaning_methods: list, ac_cleaning_methods: list,
        matching_methods: list,
        b_return_only_matched: bool = True, b_do_debug_print: bool = False
):
    """
    Core matching algorithm to find best AC (Authority Control) match for each raw text.
    
    Algorithm:
    1. For each (ac, raw) pair: Run exhaustive matching strategy and keep best candidate
    2. Group candidates by raw_text (candidates from different ACs for same raw)
    3. For each raw_text group: Select the single best candidate using match_mode
    4. Result: Each raw_text has at most ONE best_candidate
    
    Args:
        acs: List of authority control terms
        raws: List of raw text to match
        text_cleaning_methods: Text cleaning strategies for raw text
        ac_cleaning_methods: Text cleaning strategies for AC terms
        matching_methods: Matching strategies to apply
        b_return_only_matched: If False, include unmatched raw texts in results
        b_do_debug_print: If True, print detailed debug information
        
    Returns:
        DataFrame where each row represents one raw_text with its best_candidate (or None)
    """
    new_sessions = []
    match_mode = MatchMode.BestScoreMatcher
    for _raw in raws:
        for _ac in acs:
            ctx = reset_context(_ac, _raw)
            ctx.compile()

            if b_do_debug_print:
                print_test_header("Strategy 4: Exhaustive Cross Match")
            # AC 2 步，Raw 2 步 -> 理論上 4 種組合 (若每次都 match)
            session = strategy_exhaustive_cross_match(
                match_mode, RuntimeMatchingController.AllMatch,
                ctx,
                text_cleaning_methods, ac_cleaning_methods,
                matching_methods,
            )

            if b_do_debug_print:
                print_session_result(session, ctx)

            new_session = candidate_selector(match_mode, session)
            if b_do_debug_print:
                print('-' * 60)
                print(f"Filter Results By `CandidateSelector({match_mode.name})` !!")
                # display what candidate_selector returned for this (ac,raw)
                debug_sess = MatchSession(mode="<DEBUG-PRINT>", matched_candidates=new_session)
                print_session_result(debug_sess, ctx)
                print('-' * 60)

            new_sessions.extend(new_session)

    if b_do_debug_print:
        print("\n\n" + ('=' * 60))

    # === post-process accumulated candidates ===
    # We want to make sure each *raw_text* has at most one best candidate.
    # The previous attempt (calling candidate_selector on the flat list) was wrong
    # because it picked the single best candidate across all raws. Instead we
    # need to group by raw_text and run the selector on each group.
    grouped = {}
    for cand in new_sessions:
        grouped.setdefault(cand.raw_text, []).append(cand)

    filtered = []
    for raw, group in grouped.items():
        # Guard: ensure we have candidates in this group
        if not group:
            continue
        
        # wrap group into a temporary session for reuse of candidate_selector
        temp = MatchSession(mode=RuntimeMatchingController.AllMatch, matched_candidates=group)
        chosen = candidate_selector(match_mode, temp)
        
        if b_do_debug_print:
            print(f"Final selection for raw='{raw}': {len(chosen)} candidate(s) chosen")
        
        # chosen may be a list; extend results
        filtered.extend(chosen)

    new_sessions = filtered
    
    if b_do_debug_print:
        print(f"\n✓ After final filtering: {len(new_sessions)} total best candidates")
        print(f"  (covering {len(grouped)} unique raw_text values)\n")

    final_table = build_final_result_showcase_table(new_sessions, in_dataframe=True)
    if not b_return_only_matched:
        final_table = add_all_raws_to_final_dataframe(final_table, raws)
    if b_do_debug_print:
        display_table = display_results_table(final_table)
        print(display_table)
        print(("=" * 60) + "\n")
    return final_table


if __name__ == "__main__":

    m_acs = ["target", "TarGet", "TARGGET"]
    m_raws = [
        "  target  ", "%^#tar.324g683e.02t/-*+*", "tAR gE t",
        "  targett  ", "%^#ttar.324g683e.02t/-*+*", "tAR ggE t",
    ]

    text_cleaning_methods = [CleaningStrategyAdapter("StrFunc_KeepEnglishLetter"), CleaningStrategyAdapter("StrFunc_Uppercase")]
    ac_cleaning_methods = [CleaningStrategyAdapter("StrFunc_KeepEnglishLetter"), CleaningStrategyAdapter("StrFunc_Uppercase")]
    matching_methods = [MatchingStrategyAdapter("ExactMatchStrategy", 1.0)]

    core_runner(m_acs, m_raws, text_cleaning_methods, ac_cleaning_methods, matching_methods, b_return_only_matched=False, b_do_debug_print=True)
    # print(core_runner(m_acs, m_raws, text_cleaning_methods, ac_cleaning_methods, matching_methods))
    print("\n🎉 All Tests Passed Successfully!")

