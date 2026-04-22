from abc import ABC, abstractmethod

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

