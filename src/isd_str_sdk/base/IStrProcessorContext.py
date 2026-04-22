from abc import ABC, abstractmethod


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

class UnACWordContext(IStrProcessorContext):
    """ TESTING YET !@! """
    def _data_init(self) -> None:
        pass

