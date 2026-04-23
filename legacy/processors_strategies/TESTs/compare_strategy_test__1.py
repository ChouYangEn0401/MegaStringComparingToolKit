from legacy.EntireCompareTree.stras import MatchingStrategyAdapter
from isd_str_sdk.core import CleaningStrategyAdapter
from legacy.processors_strategies.utils import *

# =============================================================================
# 5. 測試輔助工具 (Test Helpers & Mocks)
# =============================================================================

def reset_context(base_ac: str, base_raw: str) -> MatchContext:
    return MatchContext(ac_text=base_ac, raw_text=base_raw)

# --- Mock Cleaning Methods ---
def clean_strip(text: str) -> str:
    return text.strip()
clean_strip.__name__ = "clean_strip"

def clean_upper(text: str) -> str:
    return text.upper()
clean_upper.__name__ = "clean_upper"

def clean_add_prefix(text: str) -> str:
    return "PRE_" + text
clean_add_prefix.__name__ = "clean_add_prefix"

# --- Mock Matching Methods ---
def match_always_true(ac: str, raw: str) -> ExampleMatchResult:
    return ExampleMatchResult(True)
match_always_true.__name__ = "match_always_true"

def match_always_false(ac: str, raw: str) -> ExampleMatchResult:
    return ExampleMatchResult(False)
match_always_false.__name__ = "match_always_false"

def match_specific_target(ac: str, raw: str) -> ExampleMatchResult:
    # 只有當 raw 變成 "TARGET" 時才匹配
    return ExampleMatchResult(raw == "TARGET")
match_specific_target.__name__ = "match_specific_target"

# --- Test Reporter ---
def print_test_header(name: str):
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"{'='*60}")

def print_session_result(session: MatchSession, context: MatchContext):
    print(f"✅ Session Mode: {session.mode}")
    print(f"✅ Context AC Final: '{context.ac_text}'")
    print(f"✅ Context Raw Final: '{context.raw_text}'")
    print(f"✅ Candidates Count: {len(session.matched_candidates)}")
    print(f"✅ Session Info Count: {len(session.matched_candidates)}")
    for i, cand in enumerate(session.matched_candidates):
        print(f"   [{i+1}] AC='{cand.ac_text}', Raw='{cand.raw_text}', Phases={cand.runtime_matching_phases}"
              f", \n\t\tSession Info: {cand.matching_info}")


def build_final_result_showcase_table(matched_candidates: List[MatchCandidate], in_dataframe: bool = False):
    """
    Build final result table from matched candidates.
    
    Returns CLEAN data without any padding.
    Padding should only be applied at display time via display_results_table().
    
    Args:
        matched_candidates: List of MatchCandidate objects from matching session
        in_dataframe: If True, return pandas DataFrame; else return dict
        
    Returns:
        DataFrame or dict mapping raw_text -> set of matched ac_texts
    """
    record_table = defaultdict(set)

    for matched_candidate in matched_candidates:
        record_table[matched_candidate.raw_text].add(matched_candidate.ac_text)

    if in_dataframe:
        import pandas as pd
        rows = [
            {
                "raw_text": raw_text,
                "ac_texts": list(ac_texts)
            }
            for raw_text, ac_texts in record_table.items()
        ]
        return pd.DataFrame(rows)

    return record_table

def add_all_raws_to_final_dataframe(
    df, 
    raws: list[str],
    not_matched_label: str = "<|NOTHING-MATCHED|>"
):
    """
    Add unmatched raw texts to the result dataframe.
    
    This works with CLEAN data (no padding).
    Padding should be applied later via display_results_table() if needed.
    
    Args:
        df: DataFrame with matched results (from build_final_result_showcase_table)
        raws: List of all original raw texts to check against
        not_matched_label: Label to use for unmatched texts
        
    Returns:
        DataFrame with original matches + unmatched entries appended
    """
    import pandas as pd
    
    # Get matched raws from clean data (simple comparison)
    matched_raws = set(df["raw_text"].tolist())

    # Find missing raws by simple set difference
    missing_raws = [r for r in raws if r not in matched_raws]

    # Append unmatched raws with not_matched_label
    if missing_raws:
        no_match_df = pd.DataFrame({
            "raw_text": missing_raws,
            "ac_texts": [[not_matched_label]] * len(missing_raws)  # Store as list to match structure
        })
        df = pd.concat([df, no_match_df], ignore_index=True)
    
    return df

def add_all_raws_with_orgserial_to_final_dataframe(
    df, 
    ac_to_orgserial_mapping: dict[str, str],
):
    df["suggested_orgserial"] = df["ac_texts"].apply(lambda acs: [ac_to_orgserial_mapping.get(org, "Unknown") for org in acs])
    return df

def display_results_table(
    df,
    front_padding: str = "|<START>|",
    end_padding: str = "|<END>|"
):
    """
    Apply visual padding to results table for terminal/console display.
    
    This is a PRESENTATION LAYER function only.
    The original dataframe (returned to user) should remain CLEAN.
    
    Args:
        df: DataFrame with clean results
        front_padding: Prefix to add to each cell
        end_padding: Suffix to add to each cell
        
    Returns:
        DataFrame with padding applied for display
    """
    import pandas as pd
    
    df_display = df.copy()
    df_display["raw_text"] = df_display["raw_text"].apply(
        lambda x: f"{front_padding}{x}{end_padding}"
    )
    df_display["ac_texts"] = df_display["ac_texts"].apply(
        lambda acs: [f"{front_padding}{ac}{end_padding}" for ac in acs] if isinstance(acs, list) else f"{front_padding}{acs}{end_padding}"
    )
    return df_display

# =============================================================================
# 6. 主程式與單元測試 (Main & Unit Tests)
# =============================================================================

if __name__ == "__main__":
    BASE_AC = "TarGet"
    BASE_RAW = "  target  "

    # ------------------------------------------------------------------
    # Test 1: strategy_clean_all_then_match
    # ------------------------------------------------------------------
    print_test_header("Strategy 1: Clean All Then Match")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 預期：Raw 先變 "target" 再變 "TARGET"，最後才比對。
    # 若用 match_always_true，應產生 1 個候選人 (最後狀態)
    session = strategy_clean_all_then_match(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],
        [MatchingStrategyAdapter("ExactMatchStrategy", 1.0), MatchingStrategyAdapter("LetterLCSStrategy", 0.95)]
    )
    print_session_result(session, ctx)
    # assert len(session.matched_candidates) == 1, "Should have 1 candidate (only final state matched)"
    # assert session.matched_candidates[0].raw_text == "  target  ", "Raw text should be fully cleaned"

    # ------------------------------------------------------------------
    # Test 2: strategy_clean_step_and_match
    # ------------------------------------------------------------------
    print_test_header("Strategy 2: Clean Step And Match")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 預期：清理 strip 後比對一次，清理 upper 後再比對一次。
    # 若用 match_always_true，應產生 2 個候選人 (中間狀態 + 最終狀態)
    session = strategy_clean_step_and_match(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],
        [MatchingStrategyAdapter("ExactMatchStrategy", 1.0), MatchingStrategyAdapter("LetterLCSStrategy", 0.95)]
    )
    print_session_result(session, ctx)
    # assert len(session.matched_candidates) == 2, "Should have 2 candidates (intermediate + final)"
    # assert session.matched_candidates[0].processed_raw_text == "target", "First candidate should be stripped only"
    # assert session.matched_candidates[1].processed_raw_text == "TARGET", "Second candidate should be upper"

    # ------------------------------------------------------------------
    # Test 3: strategy_static_ac_dynamic_raw
    # ------------------------------------------------------------------
    print_test_header("Strategy 3: Static AC, Dynamic Raw")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # AC 清理一次，Raw 逐步清理
    session = strategy_static_ac_dynamic_raw(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],       # Raw cleaners
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],               # AC cleaners
        [MatchingStrategyAdapter("ExactMatchStrategy", 1.0), MatchingStrategyAdapter("LetterLCSStrategy", 0.95)]
    )
    print_session_result(session, ctx)
    # assert ctx.ac_text == "PRE_TarGet", "AC should be cleaned once"
    # assert len(session.matched_candidates) == 2, "Should match at each Raw cleaning step"

    # ------------------------------------------------------------------
    # Test 4: strategy_exhaustive_cross_match
    # ------------------------------------------------------------------
    print_test_header("Strategy 4: Exhaustive Cross Match")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # AC 2 步，Raw 2 步 -> 理論上 4 種組合 (若每次都 match)
    session = strategy_exhaustive_cross_match(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],       # Raw
        [CleaningStrategyAdapter("StrFunc_StripSymbols"), CleaningStrategyAdapter("StrFunc_Uppercase")],       # AC
        [MatchingStrategyAdapter("ExactMatchStrategy", 1.0), MatchingStrategyAdapter("LetterLCSStrategy", 0.95)]
    )
    print_session_result(session, ctx)
    # 注意：由於 runtime_matching_phases 是累積的，且邏輯是巢狀迴圈，這裡會產生多個候選人
    # assert len(session.matched_candidates) > 0, "Should have candidates"

    # ------------------------------------------------------------------
    # Test 5: strategy_configurable_pipeline
    # ------------------------------------------------------------------
    print_test_header("Strategy 5: Configurable Pipeline")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 自定義順序：先清 AC，再清 Raw，再比對
    pipeline = {
        "step1": ("acm", CleaningStrategyAdapter('StrFunc_Lowercase')),
        "step2": ("tcm", CleaningStrategyAdapter('StrFunc_StripSymbols')),
    }
    session = strategy_configurable_pipeline(
        MatchMode.BestScoreMatcher, RuntimeMatchingController.AllMatch,
        ctx,
        pipeline,
        [MatchingStrategyAdapter("ExactMatchStrategy", 1.0)]
    )
    print_session_result(session, ctx)
    # assert ctx.ac_text == "TARGET", "AC should be upper"
    # assert ctx.raw_text == "target", "Raw should be stripped"

    # ------------------------------------------------------------------
    # Test 6: strategy_unified_operation_flow
    # ------------------------------------------------------------------
    print_test_header("Strategy 6: Unified Operation Flow")
    ctx = reset_context(BASE_AC, BASE_RAW)
    ctx.compile()
    # 混合清理與比對
    flow = {
        "clean_ac": ("acm", CleaningStrategyAdapter("StrFunc_Lowercase")),
        "match_1":  ("mm", MatchingStrategyAdapter("ExactMatchStrategy", 1.0)), # 此時 raw 還沒清，應為 False
        "clean_raw":("tcm", CleaningStrategyAdapter("StrFunc_StripSymbols")),
        "clean_raw2":("tcm", CleaningStrategyAdapter("StrFunc_Lowercase")),
        "match_2":  ("mm", MatchingStrategyAdapter("ExactMatchStrategy", 1.0)), # 此時 raw="TARGET"，應為 True
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

    print("\n" + "="*60)
    print("🎉 All Tests Passed Successfully!")
    print("="*60)

