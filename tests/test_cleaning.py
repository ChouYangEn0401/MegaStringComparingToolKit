"""
Tests for isd_str_sdk string-cleaning strategies.

覆蓋範圍
--------
- 所有無參數處理器 (base_str_processors)
- 所有有參數處理器 (param_str_processors)
- StrFunc_RemoveUpperCaseStopwords (contexted_str_processors)
- StrProcessorChain / StrProcessorsChain 鏈式呼叫
- TypeError 保護 (enforce_types / enforce_types_with_pars_check)
- CleaningStrategyAdapter 介面
"""

import pytest

# ── no-param processors ──────────────────────────────────────────────────────
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFuncNoop,
    StrFunc_Lowercase,
    StrFunc_Uppercase,
    StrFunc_SentenceCapitalization,
    StrFunc_WordsCapitalization,
    StrFunc_KeepEnglishLetter,
    StrFunc_KeepDigits,
    StrFunc_KeepEnglishLetterAndDigits,
    StrFunc_KeepEnglishWordsAndSpaces,
    StrFunc_RemoveAllSymbols,
    StrFunc_NormalizeSpacingBetweenWords,
    StrFunc_NormalizeUnicodeSpacing,
    StrFunc_StripSymbols,
    StrFunc_AscendDictionaryOrder,
    StrFunc_DescendDictionaryOrder,
    StrFunc_RemoveHtmlTags,
    StrFunc_CleanEscapedSymbols,
    StrFunc_NormalizeParentheses,
    StrFunc_NormalizeWhitespace,
    StrFunc_KeepEnglishParenthesesAndSpaces,
)

# ── param processors ─────────────────────────────────────────────────────────
from isd_str_sdk.str_cleaning.strategies.param_str_processors import (
    StrFuncWithPars_CaseConvert,
    StrFunc_Capitalize,
    StrFuncWithPars_RemoveSpecificSymbol,
    StrFunc_SortWordsWithDictionaryOrder,
    StrFunc_ReplaceInputToNothing,
    StrFunc_ReplaceInputToSomething,
    StrFunc_MultipleKeepLogic,
)

# ── contexted processors ──────────────────────────────────────────────────────
from isd_str_sdk.str_cleaning.strategies.contexted_str_processors import (
    StrFunc_RemoveUpperCaseStopwords,
)

# ── chain helpers ─────────────────────────────────────────────────────────────
from isd_str_sdk.base.StrProcessorChain import StrProcessorChain
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain

# ── adapter ───────────────────────────────────────────────────────────────────
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter


# ═══════════════════════════════════════════════════════════════════════════════
# 1. No-param processors — StrProcessorBase 子類
#    用法：ClassName(input_str).get_result()
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrFuncNoop:
    def test_returns_input_unchanged(self):
        assert StrFuncNoop("hello world").get_result() == "hello world"

    def test_empty_string(self):
        assert StrFuncNoop("").get_result() == ""

    def test_preserves_whitespace(self):
        assert StrFuncNoop("  a  b  ").get_result() == "  a  b  "


class TestStrFunc_Lowercase:
    def test_all_uppercase(self):
        assert StrFunc_Lowercase("HELLO WORLD").get_result() == "hello world"

    def test_mixed_case(self):
        assert StrFunc_Lowercase("Hello World").get_result() == "hello world"

    def test_already_lowercase(self):
        assert StrFunc_Lowercase("hello").get_result() == "hello"

    def test_empty_string(self):
        assert StrFunc_Lowercase("").get_result() == ""

    def test_type_error_on_non_str(self):
        with pytest.raises(TypeError):
            StrFunc_Lowercase(123)


class TestStrFunc_Uppercase:
    def test_all_lowercase(self):
        assert StrFunc_Uppercase("hello world").get_result() == "HELLO WORLD"

    def test_mixed_case(self):
        assert StrFunc_Uppercase("Hello World").get_result() == "HELLO WORLD"

    def test_already_uppercase(self):
        assert StrFunc_Uppercase("HELLO").get_result() == "HELLO"

    def test_empty_string(self):
        assert StrFunc_Uppercase("").get_result() == ""


class TestStrFunc_SentenceCapitalization:
    def test_basic(self):
        assert StrFunc_SentenceCapitalization("hello world").get_result() == "Hello world"

    def test_uppercased_input(self):
        assert StrFunc_SentenceCapitalization("HELLO WORLD").get_result() == "Hello world"

    def test_empty_string(self):
        assert StrFunc_SentenceCapitalization("").get_result() == ""


class TestStrFunc_WordsCapitalization:
    def test_basic(self):
        assert StrFunc_WordsCapitalization("hello world foo").get_result() == "Hello World Foo"

    def test_already_capitalized(self):
        assert StrFunc_WordsCapitalization("Hello World").get_result() == "Hello World"

    def test_single_word(self):
        assert StrFunc_WordsCapitalization("word").get_result() == "Word"

    def test_empty_string(self):
        assert StrFunc_WordsCapitalization("").get_result() == ""


class TestStrFunc_KeepEnglishLetter:
    def test_removes_digits_and_symbols(self):
        assert StrFunc_KeepEnglishLetter("abc123!@#").get_result() == "abc"

    def test_removes_spaces(self):
        assert StrFunc_KeepEnglishLetter("hello world").get_result() == "helloworld"

    def test_pure_english(self):
        assert StrFunc_KeepEnglishLetter("Hello").get_result() == "Hello"

    def test_empty_string(self):
        assert StrFunc_KeepEnglishLetter("").get_result() == ""


class TestStrFunc_KeepDigits:
    def test_keeps_only_digits(self):
        assert StrFunc_KeepDigits("abc123def456").get_result() == "123456"

    def test_no_digits(self):
        assert StrFunc_KeepDigits("hello!").get_result() == ""

    def test_only_digits(self):
        assert StrFunc_KeepDigits("007").get_result() == "007"


class TestStrFunc_KeepEnglishLetterAndDigits:
    def test_removes_symbols_and_spaces(self):
        assert StrFunc_KeepEnglishLetterAndDigits("abc 123!@#").get_result() == "abc123"

    def test_pure_alphanumeric(self):
        assert StrFunc_KeepEnglishLetterAndDigits("Hello123").get_result() == "Hello123"

    def test_empty_string(self):
        assert StrFunc_KeepEnglishLetterAndDigits("").get_result() == ""


class TestStrFunc_KeepEnglishWordsAndSpaces:
    def test_removes_digits_and_symbols(self):
        assert StrFunc_KeepEnglishWordsAndSpaces("hello 123 world!").get_result() == "hello  world"

    def test_keeps_letters_and_spaces(self):
        assert StrFunc_KeepEnglishWordsAndSpaces("MIT University").get_result() == "MIT University"

    def test_empty_string(self):
        assert StrFunc_KeepEnglishWordsAndSpaces("").get_result() == ""


class TestStrFunc_RemoveAllSymbols:
    def test_removes_punctuation(self):
        assert StrFunc_RemoveAllSymbols("hello, world!").get_result() == "helloworld"

    def test_keeps_alphanumeric(self):
        assert StrFunc_RemoveAllSymbols("abc123").get_result() == "abc123"

    def test_underscore_removed(self):
        result = StrFunc_RemoveAllSymbols("hello_world").get_result()
        assert "_" not in result

    def test_empty_string(self):
        assert StrFunc_RemoveAllSymbols("").get_result() == ""


class TestStrFunc_NormalizeSpacingBetweenWords:
    def test_multiple_spaces(self):
        assert StrFunc_NormalizeSpacingBetweenWords("hello   world").get_result() == "hello world"

    def test_tabs_and_newlines(self):
        assert StrFunc_NormalizeSpacingBetweenWords("hello\t\nworld").get_result() == "hello world"

    def test_single_space_unchanged(self):
        assert StrFunc_NormalizeSpacingBetweenWords("hello world").get_result() == "hello world"

    def test_empty_string(self):
        assert StrFunc_NormalizeSpacingBetweenWords("").get_result() == ""


class TestStrFunc_NormalizeUnicodeSpacing:
    def test_full_width_space(self):
        result = StrFunc_NormalizeUnicodeSpacing("hello\u3000world").get_result()
        assert result == "hello world"

    def test_multiple_spaces(self):
        result = StrFunc_NormalizeUnicodeSpacing("a   b").get_result()
        assert result == "a b"

    def test_no_whitespace(self):
        assert StrFunc_NormalizeUnicodeSpacing("hello").get_result() == "hello"


class TestStrFunc_StripSymbols:
    def test_strips_leading_trailing_spaces(self):
        assert StrFunc_StripSymbols("  hello  ").get_result() == "hello"

    def test_strips_tabs(self):
        assert StrFunc_StripSymbols("\thello\t").get_result() == "hello"

    def test_no_surrounding_whitespace(self):
        assert StrFunc_StripSymbols("hello").get_result() == "hello"

    def test_preserves_inner_spaces(self):
        assert StrFunc_StripSymbols("  hello world  ").get_result() == "hello world"


class TestStrFunc_AscendDictionaryOrder:
    def test_basic_sort(self):
        assert StrFunc_AscendDictionaryOrder("banana apple cherry").get_result() == "apple banana cherry"

    def test_already_sorted(self):
        assert StrFunc_AscendDictionaryOrder("alpha beta gamma").get_result() == "alpha beta gamma"

    def test_single_word(self):
        assert StrFunc_AscendDictionaryOrder("word").get_result() == "word"

    def test_case_sensitive_sort(self):
        # uppercase letters sort before lowercase in default Python sort
        result = StrFunc_AscendDictionaryOrder("b A c").get_result()
        assert result.split()[0] == "A"


class TestStrFunc_DescendDictionaryOrder:
    def test_basic_sort(self):
        assert StrFunc_DescendDictionaryOrder("apple banana cherry").get_result() == "cherry banana apple"

    def test_single_word(self):
        assert StrFunc_DescendDictionaryOrder("word").get_result() == "word"

    def test_reverse_of_ascend(self):
        text = "dog cat bird"
        asc = StrFunc_AscendDictionaryOrder(text).get_result()
        desc = StrFunc_DescendDictionaryOrder(text).get_result()
        assert asc.split() == list(reversed(desc.split()))


class TestStrFunc_RemoveHtmlTags:
    def test_removes_bold_tags(self):
        assert StrFunc_RemoveHtmlTags("<b>hello</b>").get_result() == "hello"

    def test_removes_self_closing_tag(self):
        assert StrFunc_RemoveHtmlTags("line1<br>line2").get_result() == "line1line2"

    def test_nested_tags(self):
        result = StrFunc_RemoveHtmlTags("<div><p>text</p></div>").get_result()
        assert result == "text"

    def test_no_html(self):
        assert StrFunc_RemoveHtmlTags("plain text").get_result() == "plain text"

    def test_empty_string(self):
        assert StrFunc_RemoveHtmlTags("").get_result() == ""


class TestStrFunc_CleanEscapedSymbols:
    def test_removes_escaped_double_quote(self):
        assert StrFunc_CleanEscapedSymbols('\\"hello\\"').get_result() == "hello"

    def test_removes_single_quote(self):
        assert StrFunc_CleanEscapedSymbols("it's").get_result() == "its"

    def test_restores_escaped_single_quote(self):
        result = StrFunc_CleanEscapedSymbols("\\'hello\\'").get_result()
        assert "'" not in result  # stripped by the final `replace("'", "")`


# StrFunc_NormalizeParentheses is decorated with @old_method which triggers
# a NameError in isd_py_framework_sdk <= 0.3.2 (OldWarning not defined).
# Mark these as xfail until the dependency is fixed.
class TestStrFunc_NormalizeParentheses:
    @pytest.mark.xfail(reason="@old_method decorator bug in isd_py_framework_sdk: OldWarning not defined", strict=True)
    def test_full_width_parentheses(self):
        result = StrFunc_NormalizeParentheses("（hello）").get_result()
        assert result == "(hello)"

    @pytest.mark.xfail(reason="@old_method decorator bug in isd_py_framework_sdk: OldWarning not defined", strict=True)
    def test_square_brackets(self):
        result = StrFunc_NormalizeParentheses("[hello]").get_result()
        assert result == "(hello)"

    @pytest.mark.xfail(reason="@old_method decorator bug in isd_py_framework_sdk: OldWarning not defined", strict=True)
    def test_curly_braces(self):
        result = StrFunc_NormalizeParentheses("{hello}").get_result()
        assert result == "(hello)"

    @pytest.mark.xfail(reason="@old_method decorator bug in isd_py_framework_sdk: OldWarning not defined", strict=True)
    def test_half_width_unchanged(self):
        result = StrFunc_NormalizeParentheses("(hello)").get_result()
        assert result == "(hello)"


class TestStrFunc_NormalizeWhitespace:
    def test_strips_and_collapses(self):
        assert StrFunc_NormalizeWhitespace("  hello   world  ").get_result() == "hello world"

    def test_full_width_space(self):
        result = StrFunc_NormalizeWhitespace("hello\u3000world").get_result()
        assert result == "hello world"

    def test_tab_and_newline(self):
        assert StrFunc_NormalizeWhitespace("hello\t\nworld").get_result() == "hello world"

    def test_empty_string(self):
        assert StrFunc_NormalizeWhitespace("").get_result() == ""


class TestStrFunc_KeepEnglishParenthesesAndSpaces:
    def test_keeps_letters_parens_spaces(self):
        assert StrFunc_KeepEnglishParenthesesAndSpaces("hello (world) 123!").get_result() == "hello (world) "

    def test_removes_digits_and_symbols(self):
        result = StrFunc_KeepEnglishParenthesesAndSpaces("abc123@# (test)").get_result()
        assert result == "abc (test)"

    def test_empty_string(self):
        assert StrFunc_KeepEnglishParenthesesAndSpaces("").get_result() == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Param processors — StrProcessorWithParamBase 子類
#    用法：ClassName(input_str).get_result(param)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrFuncWithPars_CaseConvert:
    def test_upper_mode(self):
        assert StrFuncWithPars_CaseConvert("hello").get_result("upper") == "HELLO"

    def test_lower_mode(self):
        assert StrFuncWithPars_CaseConvert("HELLO").get_result("lower") == "hello"

    def test_chinese_alias_upper(self):
        assert StrFuncWithPars_CaseConvert("hello").get_result("大寫") == "HELLO"

    def test_chinese_alias_lower(self):
        assert StrFuncWithPars_CaseConvert("HELLO").get_result("小寫") == "hello"

    def test_invalid_mode_raises(self):
        with pytest.raises(Exception):
            StrFuncWithPars_CaseConvert("hello").get_result("invalid_mode")


class TestStrFunc_Capitalize:
    def test_sentence_mode(self):
        assert StrFunc_Capitalize("hello world").get_result("sentence") == "Hello world"

    def test_words_mode(self):
        assert StrFunc_Capitalize("hello world foo").get_result("words") == "Hello World Foo"

    def test_chinese_alias_sentence(self):
        assert StrFunc_Capitalize("hello world").get_result("句子") == "Hello world"

    def test_chinese_alias_words(self):
        assert StrFunc_Capitalize("hello world").get_result("每個字詞片段") == "Hello World"

    def test_invalid_mode_raises(self):
        with pytest.raises(Exception):
            StrFunc_Capitalize("hello").get_result("unknown")


class TestStrFuncWithPars_RemoveSpecificSymbol:
    def test_removes_single_symbol(self):
        assert StrFuncWithPars_RemoveSpecificSymbol("hello!").get_result(["!"]) == "hello"

    def test_removes_multiple_symbols(self):
        assert StrFuncWithPars_RemoveSpecificSymbol("h@e#l$l%o").get_result(["@", "#", "$", "%"]) == "hello"

    def test_empty_list_unchanged(self):
        assert StrFuncWithPars_RemoveSpecificSymbol("hello!").get_result([]) == "hello!"

    def test_type_error_on_non_list(self):
        with pytest.raises(TypeError):
            StrFuncWithPars_RemoveSpecificSymbol("hello!").get_result("!")


class TestStrFunc_SortWordsWithDictionaryOrder:
    def test_ascend(self):
        assert StrFunc_SortWordsWithDictionaryOrder("banana apple cherry").get_result("ascend") == "apple banana cherry"

    def test_descend(self):
        assert StrFunc_SortWordsWithDictionaryOrder("apple banana cherry").get_result("descend") == "cherry banana apple"

    def test_chinese_alias_ascend(self):
        assert StrFunc_SortWordsWithDictionaryOrder("banana apple").get_result("升序") == "apple banana"

    def test_chinese_alias_descend(self):
        assert StrFunc_SortWordsWithDictionaryOrder("apple banana").get_result("降序") == "banana apple"

    def test_invalid_mode_raises(self):
        with pytest.raises(Exception):
            StrFunc_SortWordsWithDictionaryOrder("hello world").get_result("sideways")


class TestStrFunc_ReplaceInputToNothing:
    def test_single_removal(self):
        assert StrFunc_ReplaceInputToNothing("hello world").get_result(["world"]) == "hello "

    def test_multiple_removals(self):
        result = StrFunc_ReplaceInputToNothing("the quick brown fox").get_result(["quick ", "brown "])
        assert result == "the fox"

    def test_no_match(self):
        assert StrFunc_ReplaceInputToNothing("hello").get_result(["xyz"]) == "hello"

    def test_empty_list(self):
        assert StrFunc_ReplaceInputToNothing("hello").get_result([]) == "hello"

    def test_type_error_on_non_list(self):
        with pytest.raises(TypeError):
            StrFunc_ReplaceInputToNothing("hello").get_result("world")


class TestStrFunc_ReplaceInputToSomething:
    def test_single_replacement(self, capsys):
        result = StrFunc_ReplaceInputToSomething("hello world").get_result([("world", "python")])
        assert result == "hello python"

    def test_multiple_replacements(self, capsys):
        result = StrFunc_ReplaceInputToSomething("foo bar baz").get_result([("foo", "one"), ("bar", "two")])
        assert result == "one two baz"

    def test_no_match(self, capsys):
        result = StrFunc_ReplaceInputToSomething("hello").get_result([("xyz", "abc")])
        assert result == "hello"

    def test_empty_list(self, capsys):
        result = StrFunc_ReplaceInputToSomething("hello").get_result([])
        assert result == "hello"

    def test_type_error_on_non_list(self):
        with pytest.raises(TypeError):
            StrFunc_ReplaceInputToSomething("hello").get_result("world")


class TestStrFunc_MultipleKeepLogic:
    def test_keep_english_only(self):
        result = StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文"])
        assert result == "hello"

    def test_keep_digits_only(self):
        result = StrFunc_MultipleKeepLogic("hello 123!").get_result(["數字"])
        assert result == "123"

    def test_keep_english_and_digits(self):
        result = StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文", "數字"])
        assert result == "hello123"

    def test_keep_with_space(self):
        result = StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文", "字間空白"])
        assert result == "hello"

    def test_empty_options_raises(self):
        # Empty keep_options → empty char-class pattern "[]" → re.error
        import re
        with pytest.raises(re.error):
            StrFunc_MultipleKeepLogic("hello 123!").get_result([])

    def test_type_error_on_non_list(self):
        with pytest.raises(TypeError):
            StrFunc_MultipleKeepLogic("hello").get_result("英文")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Contexted processor — StrFunc_RemoveUpperCaseStopwords
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrFunc_RemoveUpperCaseStopwords:
    def test_removes_article(self):
        result = StrFunc_RemoveUpperCaseStopwords("THE University OF Taiwan").get_result()
        assert "THE" not in result
        assert "OF" not in result
        assert "University" in result
        assert "Taiwan" in result

    def test_removes_conjunction(self):
        result = StrFunc_RemoveUpperCaseStopwords("Apple AND Banana OR Cherry").get_result()
        assert "AND" not in result
        assert "OR" not in result

    def test_keeps_lowercase_words(self):
        result = StrFunc_RemoveUpperCaseStopwords("the quick brown fox").get_result()
        # lowercase stopwords are NOT removed by this strategy
        assert "the" in result

    def test_preserves_mixed_case_words(self):
        result = StrFunc_RemoveUpperCaseStopwords("MIT THE Best").get_result()
        assert "MIT" in result
        assert "Best" in result
        assert "THE" not in result

    def test_empty_string(self):
        assert StrFunc_RemoveUpperCaseStopwords("").get_result() == ""

    def test_no_stopwords(self):
        result = StrFunc_RemoveUpperCaseStopwords("MIT NTU Stanford").get_result()
        assert result == "MIT NTU Stanford"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. StrProcessorChain / StrProcessorsChain
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrProcessorChain:
    def test_single_processor(self):
        chain = StrProcessorChain([StrFunc_Lowercase])
        assert chain.run("HELLO") == "hello"

    def test_two_processors(self):
        chain = StrProcessorChain([StrFunc_Lowercase, StrFunc_StripSymbols])
        assert chain.run("  HELLO  ") == "hello"

    def test_chain_order_matters(self):
        # strip first, then uppercase
        chain = StrProcessorChain([StrFunc_StripSymbols, StrFunc_Uppercase])
        assert chain.run("  hello  ") == "HELLO"

    def test_long_chain(self):
        chain = StrProcessorChain([
            StrFunc_NormalizeWhitespace,
            StrFunc_Lowercase,
            StrFunc_KeepEnglishWordsAndSpaces,
        ])
        result = chain.run("  Hello 123 World!  ")
        assert result == "hello  world"

    def test_empty_string_passthrough(self):
        chain = StrProcessorChain([StrFunc_Lowercase, StrFunc_StripSymbols])
        assert chain.run("") == ""


class TestStrProcessorsChain:
    def test_aliases_same_behaviour(self):
        chain = StrProcessorsChain([StrFunc_Uppercase, StrFunc_StripSymbols])
        assert chain.run("  hello  ") == "HELLO"

    def test_add_method(self):
        chain = StrProcessorsChain([StrFunc_Lowercase])
        chain.add_method(StrFunc_StripSymbols)
        assert chain.run("  HELLO  ") == "hello"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CleaningStrategyAdapter
# ═══════════════════════════════════════════════════════════════════════════════

class TestCleaningStrategyAdapter:
    def test_lowercase_via_adapter(self):
        adapter = CleaningStrategyAdapter("StrFunc_Lowercase")
        assert adapter.run("HELLO WORLD") == "hello world"

    def test_uppercase_via_adapter(self):
        adapter = CleaningStrategyAdapter("StrFunc_Uppercase")
        assert adapter.run("hello") == "HELLO"

    def test_normalize_whitespace_via_adapter(self):
        adapter = CleaningStrategyAdapter("StrFunc_NormalizeWhitespace")
        assert adapter.run("  hello   world  ") == "hello world"

    def test_noop_via_adapter(self):
        adapter = CleaningStrategyAdapter("StrFuncNoop")
        assert adapter.run("unchanged") == "unchanged"

    def test_unknown_strategy_raises(self):
        with pytest.raises(KeyError):
            CleaningStrategyAdapter("NonExistentStrategy")

    def test_type_error_on_non_str_input(self):
        adapter = CleaningStrategyAdapter("StrFunc_Lowercase")
        with pytest.raises((AssertionError, TypeError)):
            adapter.run(123)
