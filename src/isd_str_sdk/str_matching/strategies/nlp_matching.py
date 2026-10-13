import numpy as np
from sentence_transformers import SentenceTransformer

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.str_matching.null_policy import NullPolicy


# --- 基於 AI 模型的語義比對 ---
class EmbeddingSimilarityStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, model_name: str = 'all-MiniLM-L6-v2', **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

        # 使用一個預訓練的輕量級模型
        self.model = SentenceTransformer(model_name)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = NullPolicy.to_text(raw1)
        val2 = NullPolicy.to_text(raw2)

        if not val1 or not val2:
            return StrategyResult(success=False, score=-1.0)

        # 將字串轉換為 embeddings (向量)
        embeddings = self.model.encode([val1, val2])

        # 計算餘弦相似度
        similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))

        return StrategyResult(success=similarity >= self.standard, score=similarity)
    
