# ### NOTE: not sure if we will need it or not ###

from typing import Union

from src.hyper_framework.CuriouslyRecurringTemplatePattern.Singleton import SingletonMetaclass
from src.lib.processors_strategies.base.processor_base import IStrProcessorContext


class ContextManager(SingletonMetaclass):

    def _initialize_manager(self):
        _str_cleaning_processors_context_map: dict[Union[type[IStrProcessorContext], str], IStrProcessorContext] = {}

    @classmethod
    def get(cls, search_key: Union[type[IStrProcessorContext], str], context: IStrProcessorContext = None) -> IStrProcessorContext:
        if search_key not in cls._str_cleaning_processors_context_map:
            instance = context or search_key()
            cls._str_cleaning_processors_context_map[search_key] = instance
        return cls._str_cleaning_processors_context_map[search_key]

# ### NOTE: not sure if we will need it or not ###
