# Agent Skills — collaborating with AI on this matcher

Purpose: document concise practices to use AI as a productive partner while implementing the IN-variant matcher and maintaining TDD.

- **Task framing**: give the AI one focused goal (e.g., implement one matching algorithm inside `test` folder). Include examples and edge cases.
- **TDD loop**: add a failing test, ask AI to implement minimal code to satisfy it, run tests, iterate. Keep tests small and focused.
- **Prompt engineering**: provide expected input/output pairs, scoring priorities (coverage vs similarity vs extra-token penalty), and negative prompts.
- **Review cycles**: inspect code diffs the AI proposes, run static type checks, and run the test suite before merging.
- **Agent skills to rely on**:
  - Write small, testable functions.
  - Suggest heuristics (subsequence vs edit distance) and tune thresholds.
  - Generate unit tests for edge cases and ranking decisions.
  - Produce plain-language explanations of scoring formulas.

How to work with this repo right now:
- Ask AI to add or modify a single test in `test/` then implement the minimal change.
- Ask AI to produce an explanation for any non-trivial heuristic used (e.g., subsequence floor = 0.85).
