from functools import wraps
from abc import ABC, abstractmethod
from typing import List, Type, Union, Generic, TypeVar

from src.hyper_framework.unitest_structure.assertions.type_checking.assertions import assert__is_list_of_str, assert__is_list_of_list_of_str, assert__is_str, assert__is_list_of_tuple_of_str


def enforce_types(input_type, output_type):
    """ Please Don't Touch The Logic Here !! """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 1. 檢查 self.input_str
            val = getattr(self, 'input_str', None)
            if not isinstance(val, input_type):
                raise TypeError(
                f"[{self.__class__.__name__}] Invalid self.input_str type before {func.__name__}(): "
                f"{repr(val)} (type: {type(val).__name__}) — expected {input_type.__name__}"
            )
            # 2. 執行 _handle(self)
            result = func(self, *args, **kwargs)
            # 3. 檢查回傳型態
            if not isinstance(result, output_type):
                raise TypeError(
                f"[{self.__class__.__name__}] Invalid return type from {func.__name__}(): "
                f"{repr(result)} (type: {type(result).__name__}) — expected {output_type.__name__}"
            )
            return result

        # 保留抽象方法屬性
        wrapper.__isabstractmethod__ = getattr(func, '__isabstractmethod__', False)
        return wrapper

    return decorator

def enforce_types_with_pars_check(input_type, output_type, param_type):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 1. 檢查 self.input_str
            val = getattr(self, 'input_str', None)
            if not isinstance(val, input_type):
                raise TypeError(
                    f"[{self.__class__.__name__}] Invalid self.input_str type before {func.__name__}(): "
                    f"{repr(val)} (type: {type(val).__name__}) — expected {input_type.__name__}"
                )

            # 2. 檢查 _handle 第一個參數（args[0]）是否存在且型態符合 param_type
            if len(args) > 0:
                if not isinstance(args[0], param_type):
                    raise TypeError(
                        f"[{self.__class__.__name__}] Invalid parameter type for {func.__name__}(): "
                        f"{repr(args[0])} (type: {type(args[0]).__name__}) — expected {param_type.__name__}"
                    )
            else:
                # 如果沒有參數，但你預期有，這邊可以選擇拋錯或跳過
                raise TypeError(
                    f"[{self.__class__.__name__}] Missing required parameter for {func.__name__}()"
                )

            # 3. 執行 _handle(self, *args, **kwargs)
            result = func(self, *args, **kwargs)

            # 4. 檢查回傳型態
            if not isinstance(result, output_type):
                raise TypeError(
                    f"[{self.__class__.__name__}] Invalid return type from {func.__name__}(): "
                    f"{repr(result)} (type: {type(result).__name__}) — expected {output_type.__name__}"
                )
            return result

        wrapper.__isabstractmethod__ = getattr(func, '__isabstractmethod__', False)
        return wrapper

    return decorator

def type_guard_for_pars_advanced(input_type, output_type, param_type_check_fn):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            val = getattr(self, 'input_str', None)
            if not isinstance(val, input_type):
                raise TypeError(
                    f"[{self.__class__.__name__}] Invalid self.input_str type before {func.__name__}(): "
                    f"{repr(val)} (type: {type(val).__name__}) — expected {input_type.__name__}"
                )

            if len(args) > 0:
                if not param_type_check_fn(args[0]):
                    raise TypeError(
                        f"[{self.__class__.__name__}] Invalid parameter type for {func.__name__}(): "
                        f"{repr(args[0])} — failed custom param_type_check_fn"
                    )
            else:
                raise TypeError(
                    f"[{self.__class__.__name__}] Missing required parameter for {func.__name__}()"
                )

            result = func(self, *args, **kwargs)

            if not isinstance(result, output_type):
                raise TypeError(
                    f"[{self.__class__.__name__}] Invalid return type from {func.__name__}(): "
                    f"{repr(result)} (type: {type(result).__name__}) — expected {output_type.__name__}"
                )
            return result

        wrapper.__isabstractmethod__ = getattr(func, '__isabstractmethod__', False)
        return wrapper

    return decorator



class IStrProcessor(ABC):
    def __init__(self, input_str: str):
        """ Please Don't Override The Logic Here !! """
        if not isinstance(input_str, str):
            raise TypeError(
                f"[{self.__class__.__name__}] Invalid input_str type: "
                f"{repr(input_str)} (type: {type(input_str).__name__}) — expected str"
            )
        self.input_str = input_str
    @abstractmethod
    def get_result(self, *args, **kwargs) -> str:
        pass

class IStrProcessorContext(ABC):
    """
        A Context-Object For A New Class Inherited StrProcessorBase Named StrProcessorWithContextBase,
        This Object Can Contain And Load Data Needed
    """
    def __init__(self, *args, **kwargs):
        self._data_init()
    @abstractmethod
    def _data_init(self) -> None:
        pass

class StrProcessorBase(IStrProcessor, ABC):
    def get_result(self) -> str:
        return self._handle()
    @abstractmethod
    def _handle(self) -> str:
        pass

class StrProcessorWithParamBase(IStrProcessor, ABC):
    def get_result(self, *args, **kwargs) -> str:
        return self._handle(*args, **kwargs)
    @abstractmethod
    def _handle(self, *args, **kwargs) -> str:
        pass

# ### REFACTOR: not sure if this structrue is good enough ###
TStrProcessorContextFamily = TypeVar("TStrProcessorContextFamily", bound=IStrProcessorContext)
class StrProcessorWithContextBase(StrProcessorBase, Generic[TStrProcessorContextFamily], ABC):
    """ TESTING YET !@! """
    def __init__(self, input_str: str):
        super().__init__(input_str)
        self._inner_context: IStrProcessorContext = None
    @abstractmethod
    def require_context(self, require_key: Union[type[TStrProcessorContextFamily], str]) -> TStrProcessorContextFamily:
        pass

class UnACWordContext(IStrProcessorContext):
    """ TESTING YET !@! """
    def _data_init(self) -> None:
        pass
class SomeProcessor(StrProcessorWithContextBase[UnACWordContext]):
    """ TESTING YET !@! """
    def require_context(self) -> UnACWordContext:
        return UnACWordContext
# ### REFACTOR: not sure if this structrue is good enough ###

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

class StrProcessorChain:
    def __init__(self, processors: List[Type[StrProcessorBase]]):
        self.processors = [p("") for p in processors]

    def add_method(self, clean_method: Type[StrProcessorBase]):
        self.processors.append(clean_method(""))

    def run(self, text: str) -> str:
        for p in self.processors:
            p.input_str = text
            text = p._handle()
        return text
