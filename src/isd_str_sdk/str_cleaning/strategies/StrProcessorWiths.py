from functools import wraps
from abc import ABC, abstractmethod
from typing import Union, Generic, TypeVar

from src.isd_str_sdk.base.IStrProcessor import IStrProcessor, StrProcessorBase, StrProcessorWithContextBase
from src.isd_str_sdk.base.IStrProcessorContext import IStrProcessorContext, UnACWordContext
from isd_str_sdk.utils.decorators import type_guard_for_pars_advanced
from isd_py_framework_sdk.assertions import assert__is_list_of_str, assert__is_list_of_list_of_str, assert__is_str, assert__is_list_of_tuple_of_str


class StrProcessorWithStrParam(IStrProcessor, ABC):
    def get_result(self, *args, **kwargs) -> str:
        return self._handle(*args, **kwargs)
    @abstractmethod
    def _handle_runner(self, *args, **kwargs) -> str:
        pass
    @type_guard_for_pars_advanced(str, str, assert__is_str)
    def _handle(self, *args, **kwargs) -> str:
        return self._handle_runner(*args, **kwargs)

class StrProcessorWithListStrParam(IStrProcessor, ABC):
    def get_result(self, *args, **kwargs) -> str:
        return self._handle(*args, **kwargs)
    @abstractmethod
    def _handle_runner(self, *args, **kwargs) -> str:
        pass
    @type_guard_for_pars_advanced(str, str, assert__is_list_of_str)
    def _handle(self, *args, **kwargs) -> str:
        return self._handle_runner(*args, **kwargs)

class StrProcessorWithListListStrParam(IStrProcessor, ABC):
    def get_result(self, *args, **kwargs) -> str:
        return self._handle(*args, **kwargs)
    @abstractmethod
    def _handle_runner(self, *args, **kwargs) -> str:
        pass
    @type_guard_for_pars_advanced(str, str, assert__is_list_of_list_of_str)
    def _handle(self, *args, **kwargs) -> str:
        return self._handle_runner(*args, **kwargs)

class StrProcessorWithListTupleStrParam(IStrProcessor, ABC):
    def get_result(self, *args, **kwargs) -> str:
        return self._handle(*args, **kwargs)
    @abstractmethod
    def _handle_runner(self, *args, **kwargs) -> str:
        pass
    @type_guard_for_pars_advanced(str, str, assert__is_list_of_tuple_of_str)
    def _handle(self, *args, **kwargs) -> str:
        return self._handle_runner(*args, **kwargs)

TStrProcessorContextFamily = TypeVar("TStrProcessorContextFamily", bound=IStrProcessorContext)
class StrProcessorWithContextBase(StrProcessorBase, Generic[TStrProcessorContextFamily], ABC):
    """ TESTING YET !@! """
    def __init__(self, input_str: str):
        super().__init__(input_str)
        self._inner_context: IStrProcessorContext = None
    @abstractmethod
    def require_context(self, require_key: Union[type[TStrProcessorContextFamily], str]) -> TStrProcessorContextFamily:
        pass

# ### REFACTOR: not sure if this structrue is good enough ###
class SomeProcessor(StrProcessorWithContextBase[UnACWordContext]):
    """ TESTING YET !@! """
    def require_context(self) -> UnACWordContext:
        return UnACWordContext
# ### REFACTOR: not sure if this structrue is good enough ###