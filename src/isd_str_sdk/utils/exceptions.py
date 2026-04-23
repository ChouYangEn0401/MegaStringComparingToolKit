from typing import List
import inspect

class MissingParameters(Exception):
    def __init__(self, options: List[str], message=None):
        if message is None:
            str_ = ', '.join([f"`{option}`" for option in options])
            message = f"Missing Important Parameters {str_} !!"
        super().__init__(message)

    def __str__(self):
        """
        提供更詳細的例外訊息，包含發生錯誤的類別。
        """
        # 嘗試找出呼叫此例外的類別
        frame = inspect.currentframe().f_back
        while frame:
            if 'self' in frame.f_locals:
                calling_class = frame.f_locals['self'].__class__.__name__
                return f"錯誤：在類別 '{calling_class}' 中發生 MissingParameters。\n{super().__str__()}"
            frame = frame.f_back
        return super().__str__()

