from legacy.EntireCompareTree.test.in_variant_matcher import tokenize, score_candidate, normalize_token
q = "chang gang univ"
c = "chang gang univ departmental"
print('tokens:', tokenize(c))
print('normalize neg:', normalize_token('dept'))
res = score_candidate(q, c, negative_tokens=['-dept'], negative_mode='boundary')
print('result rejected:', res.rejected_by_negative_prompt)
print(res)
from legacy.EntireCompareTree.test.in_variant_matcher import normalize_token
nrm = normalize_token('dept')
print('check starts/ends per token:', [ (t, t.startswith(nrm), t.endswith(nrm)) for t in tokenize(c)])
print('any starts/ends:', any(t.startswith(nrm) or t.endswith(nrm) for t in tokenize(c)))
for t in tokenize(c):
	print('token repr:', repr(t), [hex(ord(ch)) for ch in t[:6]])
print('nrm repr:', repr(nrm), [hex(ord(ch)) for ch in nrm])
print("direct test:", 'departmental'.startswith('dept'))
