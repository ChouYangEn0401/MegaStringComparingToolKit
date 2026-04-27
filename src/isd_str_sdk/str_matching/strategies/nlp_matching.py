import numpy as np
from sentence_transformers import SentenceTransformer

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
    

# --- 基於 AI 模型的語義比對 ---
class EmbeddingSimilarityStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, model_name: str = 'all-MiniLM-L6-v2', **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

        # 使用一個預訓練的輕量級模型
        self.model = SentenceTransformer(model_name)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col))
        val2 = str(context.row2.get(self.df2_col))

        if not val1 or not val2:
            return StrategyResult(success=False, score=-1.0)

        # 將字串轉換為 embeddings (向量)
        embeddings = self.model.encode([val1, val2])

        # 計算餘弦相似度
        similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))

        return StrategyResult(success=similarity >= self.standard, score=similarity)
    
