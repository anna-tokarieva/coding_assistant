---
name: pytest-tests
description: Help the user write pytest-style unit tests.
---

Use this skill when the user asks about testing Python code.

Guidelines:
- Use `pytest` style tests (plain functions, no classes).
- One clear assertion per test when possible.
- Name tests like `test_<what_it_does>`.

Always:
- Show how to import the function under test.
- Include at least one passing and one failing example case when it makes sense.
- Mention how to run the tests: `pytest -q`.