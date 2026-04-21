from typing import Literal
import numpy as np
from rapidfuzz import fuzz  # fuzzywuzzy 替代品，更快
from sentence_transformers import SentenceTransformer
from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity

# #########################
# Global Temp API
# #########################

def callable_function1(): print("功能1 執行")
def callable_function2(param): print(f"功能2 執行，參數是: {param}")
def callable_function3(param): print(f"功能3 執行，參數是: {param}")

# #########################
# tool Functions
# #########################

def _lcs_length(a: str, b: str) -> int:
    # 計算LCS長度
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                dp[i+1][j+1] = dp[i][j] + 1
            else:
                dp[i+1][j+1] = max(dp[i][j+1], dp[i+1][j])
    return dp[m][n]

def lcs_similarity(a: str, b: str) -> float:
    # LCS similarity normalized by max length
    lcs_len = _lcs_length(a, b)
    return lcs_len / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0

def jaccard_similarity(a: str, b: str) -> float:
    set_a = set(a.split())
    set_b = set(b.split())
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0

def exact_match(a: str, b: str) -> bool:
    return a == b

def fuzzy_ratio(a: str, b: str) -> float:
    return fuzz.ratio(a, b) / 100

def fuzzy_partial_ratio(a: str, b: str) -> float:
    return fuzz.partial_ratio(a, b) / 100

# #########################
# tool Functions
# #########################

class EmbeddingSimilarity:
    def __init__(self, model: Literal['all-MiniLM-L6-v2', 'paraphrase-multilingual-MiniLM-L12-v2', 'all-mpnet-base-v2']='all-MiniLM-L6-v2'):
        """
        模型說明：
            - all-MiniLM-L6-v2
                單語（英文為主）Sentence Transformer，
                速度快、資源消耗低，適合大量比對或 baseline 使用。

            - paraphrase-multilingual-MiniLM-L12-v2
                多語 / 跨語言 Sentence Transformer，
                能處理中英文、跨語言語義對齊，
                適合機構名稱、翻譯差異等情境。

            - all-mpnet-base-v2
                高精度英文 Sentence Transformer，
                語義表現最佳但模型較大、速度較慢，
                適合當作上限參考或高品質比對。
        """
        # Load sentence-transformer model
        self.sbert_model = SentenceTransformer(model)
        # Load pretrained Word2Vec GoogleNews vectors (需自行下載)
        # self.w2v_model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
        # 這裡先不載入，改用 dummy
        self.w2v_model = None

    def sentence_embedding_similarity(self, a: str, b: str) -> float:
        emb_a = self.sbert_model.encode([a])[0].reshape(1, -1)
        emb_b = self.sbert_model.encode([b])[0].reshape(1, -1)
        sim = cosine_similarity(emb_a, emb_b)[0][0]
        return float(sim)

    def word2vec_avg_embedding(self, sentence: str) -> np.ndarray:
        if self.w2v_model is None:
            # 回傳隨機向量示範
            return np.random.rand(300).reshape(1, -1)
        words = sentence.split()
        vectors = [self.w2v_model[w] for w in words if w in self.w2v_model]
        if not vectors:
            return np.zeros((1, 300))
        avg_vec = np.mean(vectors, axis=0).reshape(1, -1)
        return avg_vec

    def word2vec_similarity(self, a: str, b: str) -> float:
        emb_a = self.word2vec_avg_embedding(a)
        emb_b = self.word2vec_avg_embedding(b)
        sim = cosine_similarity(emb_a, emb_b)[0][0]
        return float(sim)

def compare_sentences(a: str, b: str):
    embed_sim = EmbeddingSimilarity()

    print(f"LCS similarity: {lcs_similarity(a, b):.4f}")
    print(f"Jaccard similarity: {jaccard_similarity(a, b):.4f}")
    print(f"Exact match: {exact_match(a, b)}")
    print(f"Fuzzy ratio: {fuzzy_ratio(a, b):.4f}")
    print(f"Fuzzy partial ratio: {fuzzy_partial_ratio(a, b):.4f}")
    print(f"Sentence-BERT embedding similarity: {embed_sim.sentence_embedding_similarity(a, b):.4f}")
    print(f"Word2Vec avg embedding similarity: {embed_sim.word2vec_similarity(a, b):.4f}")


"""
    Sample Showcase, Convert To Strategy Pattern In Future
"""
if __name__ == "__main__":
    sent1 = "今天天氣真好，我想去散步"
    sent2 = "今天天氣不錯，想出去走走"
    compare_sentences(sent1, sent2)
