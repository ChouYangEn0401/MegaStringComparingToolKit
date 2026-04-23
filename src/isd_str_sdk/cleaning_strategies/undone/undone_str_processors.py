from enum import auto, Enum
import re
import regex
from typing import List
import string
from isd_py_framework_sdk.exceptions import WrongOptionException
from isd_py_framework_sdk.decorators import old_method

from isd_str_sdk.cleaning_strategies.StrProcessorWiths import StrProcessorWithListStrParam, StrProcessorWithListTupleStrParam
from src.isd_str_sdk.base.IStrProcessor import StrProcessorBase, StrProcessorWithParamBase
from src.isd_str_sdk.utils.decorators import enforce_types, enforce_types_with_pars_check
from isd_str_sdk.cleaning_strategies.pre_contexted._actable_str_processor import UnionLetterExcelACTableContext


# ### UNDONE
class callable_func_spellcheck(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_pinyin_check(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_pinyin_check_2(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_spellcheck_2(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_org_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_company_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_school_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_location_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_foreign_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_special_word_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_encoding_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_other_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
# ### UNDONE


