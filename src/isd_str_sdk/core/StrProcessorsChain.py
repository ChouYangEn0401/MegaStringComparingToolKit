from typing import List, Type

from isd_str_sdk.base.IStrProcessor import StrProcessorBase


class StrProcessorsChain:
    def __init__(self, processors: List[Type[StrProcessorBase]]):
        self.processors = [p("") for p in processors]

    def add_method(self, clean_method: Type[StrProcessorBase]):
        self.processors.append(clean_method(""))

    def run(self, text: str) -> str:
        for p in self.processors:
            p.input_str = text
            text = p._handle()
        return text
