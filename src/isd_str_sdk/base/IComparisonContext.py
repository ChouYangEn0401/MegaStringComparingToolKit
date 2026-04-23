"""
### NOTE: 這裡的設計靈感來自於 Strategy Pattern 中的 Context 注入，讓 Strategy 的執行完全依賴於外部提供的 Context，而不是自己去獲取資料。
    這樣做的好處是：
    1. **分離關注點**： Strategy 專注於算法邏輯，而 Context 負責提供數據，兩者職責分明。
    2. **提高靈活性**： 不同的 Context 可以用來支持不同的使用場景，Strategy 不需要修改就可以適應新的需求。
    3. **便於測試**： 在測試 Strategy 時，可以輕鬆地創建不同的 Context 來模擬各種情況，從而全面測試算法的行為。
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Generic, TypeVar, Dict, Any, Optional

# 定義 Context 的型別
class IComparisonContext(ABC):
    """
    用來在遍歷樹時傳遞所有外部資料。
    """
    __slots__ = ()  # 讓子類 @dataclass(slots=True) 能真正消除 __dict__
    pass
IComparisonContextFamily = TypeVar("ContextType", bound=IComparisonContext)

