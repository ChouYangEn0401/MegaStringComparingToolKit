from __future__ import annotations
from typing import Generic, Any, List, Union, Iterator, Callable, Protocol, TypeVar, Dict
import pandas as pd
from dataclasses import dataclass
from collections import deque


# 定義一個協議（Protocol），這就是我們說的「介面」。
# 任何符合這個介面行為的類別都可以作為迭代資料來源。
class IterableSource(Protocol):
    def __iter__(self) -> Iterator[dict | Any]: ...
    def __len__(self) -> int: ...

# 泛型定義
T = TypeVar("T")
K = TypeVar("K", int, str, float)

# 數據包裝器：將原始數據和索引包裝在一起
@dataclass(frozen=True)  # 使用 frozen=True 讓物件不可變，提高安全性
class IterationItem(Generic[K, T]):
    index: K
    data: T

# 通用迭代器：將任何符合 IterableSource 協議的數據來源，包裝成我們需要的 IterationItem
class UniversalIterator:
    """
    通用迭代器，負責將不同的資料來源（如 DataFrame, list）轉換成統一的格式。
    """

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> List[IterationItem[K, pd.Series]]:
        return [IterationItem(index=idx, data=row) for idx, row in df.iterrows()]

    @staticmethod
    def from_list(data_list: List[Any]) -> List[IterationItem[int, Any]]:
        return [IterationItem(index=i, data=item) for i, item in enumerate(data_list)]

    @staticmethod
    def from_dict(data_list: Dict[K, Any]) -> List[IterationItem[K, Any]]:
        return [IterationItem(index=i, data=item) for i, item in enumerate(data_list)]

    @staticmethod
    def from_series(series: pd.Series) -> List[IterationItem[K, Any]]:
        return [IterationItem(index=i, data=item) for i, item in series.items()]

# 核心：迴圈協調者（LoopCoordinator）
class LoopCoordinator:
    """
    負責協調和執行多層嵌套迴圈，支援在不同層級注入回呼函數。
    """

    def __init__(self, iterables: List[List[IterationItem]]):
        self._iterables = iterables
        self._on_item_callbacks: Dict[int, Callable[..., None]] = {}
        self._on_exit_callbacks: Dict[int, Callable[..., None]] = {}  # 新增：用於儲存 on_exit 的回呼

    def on_item(self, level: int, callback: Callable[..., None]) -> LoopCoordinator:
        """為指定的迴圈層級綁定一個在進入時執行的回呼函數。"""
        if level < 0 or level >= len(self._iterables):
            raise IndexError("Callback level is out of bounds.")
        self._on_item_callbacks[level] = callback
        return self

    def on_exit(self, level: int, callback: Callable[..., None]) -> LoopCoordinator:
        """新增：為指定的迴圈層級綁定一個在退出時執行的回呼函數。"""
        if level < 0 or level >= len(self._iterables):
            raise IndexError("Callback level is out of bounds.")
        self._on_exit_callbacks[level] = callback
        return self

    def run(self):
        """
        使用非遞迴的堆疊來執行嵌套迴圈。
        這個版本修復了 on_exit 的觸發時機，使其在外層迴圈的每個項目結束時觸發。
        """
        if not self._iterables:
            return

        # 堆疊元素：(層級, 迭代器, 當前迭代項目列表)
        stack = deque([(0, iter(self._iterables[0]), [])])

        while stack:
            level, current_iterator, current_items = stack[-1]

            try:
                item = next(current_iterator)

                # 處理 on_item 回呼
                current_items.append(item)
                on_item_callback = self._on_item_callbacks.get(level)
                if on_item_callback:
                    on_item_callback(*current_items)

                # 如果有下一層迴圈，則將其推入堆疊
                if level + 1 < len(self._iterables):
                    next_level_iterator = iter(self._iterables[level + 1])
                    stack.append((level + 1, next_level_iterator, current_items[:]))
                else:
                    # 如果沒有下一層迴圈（即達到最內層），則執行 on_exit 回呼
                    # 這是為了確保最內層的每次迭代都執行回呼
                    on_exit_callback = self._on_exit_callbacks.get(level)
                    if on_exit_callback:
                        on_exit_callback(*current_items)

                    current_items.pop()

            except StopIteration:
                # 當前層級的迭代器已耗盡，從堆疊中移除
                stack.pop()

                # 如果堆疊不為空，說明我們從一個內層迴圈返回到外層
                if stack:
                    # 在返回外層時，執行該層的回呼，並彈出項目
                    on_exit_callback = self._on_exit_callbacks.get(level - 1)
                    if on_exit_callback:
                        on_exit_callback(*stack[-1][2])  # 使用上一層的 items

                    # 彈出項目
                    stack[-1][2].pop()


# --- 範例1：使用具名函式 ---
def on_level_0_callback(item1: IterationItem):
    """處理第一層迴圈的回呼邏輯。"""
    print(f"> df1[{item1.index}] = {item1.data.to_dict()}")

def on_level_1_callback(item1: IterationItem, item2: IterationItem):
    """處理第二層迴圈的回呼邏輯。"""
    print(f"  - df2[{item2.index}] = {item2.data.to_dict()}")

def test_callback_function():
    print("\n--- 測試具名函式回呼 ---")
    df1 = pd.DataFrame({"a": ["apple", "banana"]})
    df2 = pd.DataFrame({"b": [10, 20, 30]})

    iter1 = UniversalIterator.from_dataframe(df1)
    iter2 = UniversalIterator.from_dataframe(df2)

    LoopCoordinator([iter1, iter2]) \
        .on_item(0, on_level_0_callback) \
        .on_item(1, on_level_1_callback) \
        .run()

# --- 範例2：使用封裝的類別 ---
class CustomCallbackProcessor:
    def __init__(self, some_state: Any):
        self._some_state = some_state
        print(f"CallbackProcessor initialized with state: {self._some_state}")

    def on_first_level(self, item1: IterationItem):
        print(f"> Processing item at level 0: {item1.index} with state {self._some_state}")

    def on_second_level(self, item1: IterationItem, item2: IterationItem):
        print(f"  - Processing item at level 1: {item2.index} with state {self._some_state}")

def test_callback_class():
    print("\n--- 測試回呼類別 ---")
    df1 = pd.DataFrame({"a": ["apple", "banana"]})
    df2 = pd.DataFrame({"b": [10, 20, 30]})

    iter1 = UniversalIterator.from_dataframe(df1)
    iter2 = UniversalIterator.from_dataframe(df2)

    processor = CustomCallbackProcessor("MyCustomState")

    LoopCoordinator([iter1, iter2]) \
        .on_item(0, processor.on_first_level) \
        .on_item(1, processor.on_second_level) \
        .run()


# --- 測試案例 ---
def test_double_dataframe_pair():
    """測試兩個 DataFrame 的雙層迴圈。"""
    print("\n--- 測試案例 1：兩個 DataFrame ---")
    df1 = pd.DataFrame({"a": ["apple", "banana"]})
    df2 = pd.DataFrame({"b": [10, 20, 30]})

    iter1 = UniversalIterator.from_dataframe(df1)
    iter2 = UniversalIterator.from_dataframe(df2)

    LoopCoordinator([iter1, iter2]) \
        .on_item(1, lambda item1, item2: print(f"Comparing df1[{item1.index}] with df2[{item2.index}]")) \
        .run()

def test_list_and_dataframe_pair():
    """測試 list 和 DataFrame 的雙層迴圈。"""
    print("\n--- 測試案例 2：List 和 DataFrame ---")
    array1 = ["apple", "banana", "cat"]
    df2 = pd.DataFrame({"b": [10, 20, 30]})

    iter1 = UniversalIterator.from_list(array1)
    iter2 = UniversalIterator.from_dataframe(df2)

    LoopCoordinator([iter1, iter2]) \
        .on_item(1, lambda item1, item2: print(f"Comparing list[{item1.index}] with df2[{item2.index}]")) \
        .run()

def test_triple_nested_loop():
    """測試三層迴圈，使用不同資料來源。"""
    print("\n--- 測試案例 3：三層迴圈 ---")
    list1 = ["A", "B"]
    df2 = pd.DataFrame({"col": [1, 2]})
    dict3 = {"key1": "val1", "key2": "val2"}

    iter1 = UniversalIterator.from_list(list1)
    iter2 = UniversalIterator.from_dataframe(df2)
    iter3 = UniversalIterator.from_dict(dict3)

    LoopCoordinator([iter1, iter2, iter3]) \
        .on_item(0, lambda item1: print(f"Level 0: {item1.data}")) \
        .on_item(1, lambda item1, item2: print(f"  Level 1: {item2.index}")) \
        .on_item(2, lambda item1, item2, item3: print(f"    Level 2: {item3.index} -> {item3.data}")) \
        .run()

def test_dict_and_series_pair():
    """測試 Dict 和 Series 的雙層迴圈。"""
    print("\n--- 測試案例 4：Dict 和 Series ---")
    my_dict = {"id1": "dataA", "id2": "dataB"}
    my_series = pd.Series([100, 200], index=["item1", "item2"])

    iter1 = UniversalIterator.from_dict(my_dict)
    iter2 = UniversalIterator.from_series(my_series)

    LoopCoordinator([iter1, iter2]) \
        .on_item(1, lambda item1, item2: print(f"Comparing dict key[{item1.index}] with series key[{item2.index}]")) \
        .run()


if __name__ == "__main__":
    test_double_dataframe_pair()
    test_list_and_dataframe_pair()
    test_triple_nested_loop()
    test_dict_and_series_pair()
    test_callback_function()
    test_callback_class()


