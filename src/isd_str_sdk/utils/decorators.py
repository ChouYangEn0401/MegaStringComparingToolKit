from functools import wraps

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



