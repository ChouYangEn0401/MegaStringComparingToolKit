from __future__ import annotations
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple, Optional


@dataclass
class MatchResult:
    score: float
    matched_pairs: List[Tuple[str, str, float]]
    rejected_by_negative_prompt: bool = False
    coverage: float = 0.0
    avg_similarity: float = 0.0
    extra_token_frac: float = 0.0


def normalize_token(t: str) -> str:
    t = t.lower().strip()
    t = re.sub(r"[^a-z0-9]+", "", t)
    return t


def tokenize(text: str) -> List[str]:
    raw = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [normalize_token(t) for t in raw if normalize_token(t)]


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, 1):
            cur = dp[j]
            if ca == cb:
                dp[j] = prev
            else:
                dp[j] = min(prev + 1, dp[j] + 1, dp[j - 1] + 1)
            prev = cur
    return dp[-1]


def is_subsequence(short: str, long: str) -> bool:
    # return True if all chars in short appear in order inside long
    it = iter(long)
    return all(c in it for c in short)


def token_sim(a: str, b: str) -> float:
    # similarity in [0,1] combining edit distance and subsequence heuristic
    if not a or not b:
        return 0.0
    a_, b_ = a, b
    d = levenshtein(a_, b_)
    base = max(0.0, 1.0 - d / max(len(a_), len(b_)))

    # subsequence bonus: if one token is subsequence of the other, treat as strong match
    short, long = (a_, b_) if len(a_) <= len(b_) else (b_, a_)
    if is_subsequence(short, long):
        # give a high floor; but don't exceed 0.95
        base = max(base, 0.85)
    return base


def _best_assignment(query_tokens: List[str], cand_tokens: List[str]) -> Tuple[float, List[Tuple[int, int, float]]]:
    # one-to-one assignment maximizing total similarity (order ignored)
    n, m = len(query_tokens), len(cand_tokens)
    sims = [[token_sim(query_tokens[i], cand_tokens[j]) for j in range(m)] for i in range(n)]

    @lru_cache(None)
    def dp(i: int, mask: int) -> Tuple[float, Tuple[Tuple[int, int, float], ...]]:
        if i == n:
            return 0.0, ()
        best_score, best_path = -1.0, ()
        # option: skip matching this query token
        skip_score, skip_path = dp(i + 1, mask)
        best_score, best_path = skip_score, skip_path

        for j in range(m):
            if mask & (1 << j):
                continue
            s2, p2 = dp(i + 1, mask | (1 << j))
            total = sims[i][j] + s2
            if total > best_score:
                best_score = total
                best_path = ((i, j, sims[i][j]),) + p2
        return best_score, best_path

    s, p = dp(0, 0)
    return s, list(p)


def score_candidate(
    query: str,
    candidate: str,
    negative_tokens: Optional[List[str]] = None,
    min_token_sim: float = 0.6,
    extra_token_penalty: float = 0.15,
    # out-of-order penalty: disabled by default to preserve previous behaviour
    penalize_out_of_order: bool = False,
    out_of_order_penalty: float = 0.10,
    # negative prompt handling: 'exact'|'boundary'|'in'|'fuzzy'
    negative_mode: str = "exact",
    negative_fuzzy_threshold: float = 0.85,
) -> MatchResult:
    q = tokenize(query)
    c = tokenize(candidate)

    if negative_tokens:
        neg_raw = [x.lstrip("-") for x in negative_tokens]
        mode = (negative_mode or "exact").lower()
        for raw in neg_raw:
            nrm = normalize_token(raw)
            if not nrm:
                continue
            if mode == "exact":
                if any(t == nrm for t in c):
                    return MatchResult(score=0.0, matched_pairs=[], rejected_by_negative_prompt=True)
            elif mode == "boundary":
                # match if appears at token start or end
                if any(t.startswith(nrm) or t.endswith(nrm) for t in c):
                    return MatchResult(score=0.0, matched_pairs=[], rejected_by_negative_prompt=True)
            elif mode == "in":
                # substring anywhere in token
                if any(nrm in t for t in c):
                    return MatchResult(score=0.0, matched_pairs=[], rejected_by_negative_prompt=True)
            elif mode == "fuzzy":
                # token similarity above threshold
                if any(token_sim(nrm, t) >= negative_fuzzy_threshold for t in c):
                    return MatchResult(score=0.0, matched_pairs=[], rejected_by_negative_prompt=True)
            else:
                # unknown mode: fall back to exact
                if any(t == nrm for t in c):
                    return MatchResult(score=0.0, matched_pairs=[], rejected_by_negative_prompt=True)

    if not q or not c:
        return MatchResult(score=0.0, matched_pairs=[])

    best_sum, idx_pairs = _best_assignment(q, c)

    # keep only pairs above threshold
    pairs = [(q[i], c[j], s) for i, j, s in idx_pairs if s >= min_token_sim]

    matched_count = len(pairs)
    avg_q_match = (sum(s for _, _, s in pairs) / len(q)) if q else 0.0
    coverage = matched_count / len(q) if q else 0.0
    extra = max(0, len(c) - matched_count) / len(c) if c else 0.0

    # order penalty: measure inversions in candidate-token indices among matched pairs
    order_penalty_val = 0.0
    if penalize_out_of_order and matched_count > 1:
        j_indices = [j for _, j, _ in [(i, j, s) for i, j, s in idx_pairs if s >= min_token_sim]]
        inv = 0
        for a in range(len(j_indices)):
            for b in range(a + 1, len(j_indices)):
                if j_indices[a] > j_indices[b]:
                    inv += 1
        max_inv = len(j_indices) * (len(j_indices) - 1) / 2
        if max_inv > 0:
            order_penalty_val = out_of_order_penalty * (inv / max_inv)

    score = 0.75 * avg_q_match + 0.20 * coverage - extra_token_penalty * extra - order_penalty_val
    score = max(0.0, min(1.0, score))
    return MatchResult(
        score=score,
        matched_pairs=pairs,
        coverage=coverage,
        avg_similarity=avg_q_match,
        extra_token_frac=extra,
    )


def rank_candidates(
    query: str,
    candidates: List[str],
    negative_tokens: Optional[List[str]] = None,
    # pass-through options (kept default to preserve current behaviour)
    **score_kwargs,
) :
    out = []
    for idx, c in enumerate(candidates):
        r = score_candidate(query, c, negative_tokens=negative_tokens, **score_kwargs)
        out.append((c, r.score, r, idx))

    # sort primary by score, then tie-break by coverage, fewer extra tokens, avg similarity, shorter candidate, lexicographic
    def sort_key(item):
        cand, sc, res, idx = item
        # higher is better for first fields; negative for fields where smaller is better
        return (
            sc,
            res.coverage,
            -res.extra_token_frac,
            res.avg_similarity,
            -len(tokenize(cand)),
            -idx,
        )
    out.sort(key=sort_key, reverse=True)
    # strip idx before returning
    return [(c, sc, r) for (c, sc, r, idx) in out]


def normalize_nospace(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def string_similarity(a: str, b: str) -> float:
    # simple whole-string similarity after removing spaces/punctuation
    a2 = normalize_nospace(a)
    b2 = normalize_nospace(b)
    if not a2 or not b2:
        return 0.0
    d = levenshtein(a2, b2)
    base = max(0.0, 1.0 - d / max(len(a2), len(b2)))
    # subsequence bonus
    short, long = (a2, b2) if len(a2) <= len(b2) else (b2, a2)
    if is_subsequence(short, long):
        base = max(base, 0.8)
    return base


def rank_typo_candidates(
    query: str,
    candidates: List[str],
    negative_tokens: Optional[List[str]] = None,
    weight_string: float = 0.30,
    **score_kwargs,
):
    """Combine token-based IN-variant score with whole-string similarity to
    better handle merged/space-separated/garbled tokens (e.g. NATLTAIWAN, NATL TAI WAN).
    """
    out = []
    for c in candidates:
        token_res = score_candidate(query, c, negative_tokens=negative_tokens, **score_kwargs)
        s_token = token_res.score
        s_string = string_similarity(query, c)
        combined = (1 - weight_string) * s_token + weight_string * s_string
        # keep combined in [0,1]
        combined = max(0.0, min(1.0, combined))
        out.append((c, combined, token_res))

    out.sort(key=lambda x: x[1], reverse=True)
    return out
