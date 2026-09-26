# Verification record

Verified locally in the build environment before packaging:

- Python compilation: passed
- Automated tests: 33 passed
- Coverage: 84.55%
- Coverage gate: 80% passed
- Python lines over Ruff's configured 120-character limit: 0

Ruff itself was not executable in the build environment used to package this project, so the final repository's first local command should be:

```powershell
python -m ruff check .
```

The repository includes GitHub Actions CI that runs Ruff and the same test/coverage gate on pushes and pull requests.
