from functools import wraps
from abc import ABC, abstractmethod
from typing import List, Type, Union, Generic

from isd_py_framework_sdk.assertions import assert__is_list_of_str, assert__is_list_of_list_of_str, assert__is_str, assert__is_list_of_tuple_of_str

from isd_str_sdk.base.IStrProcessor import IStrProcessor, StrProcessorBase

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
