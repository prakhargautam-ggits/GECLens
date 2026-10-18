# Contributing to GECLens

Bug reports, questions and pull requests are welcome.

- **Report a problem:** open an issue at https://github.com/prakhargautam-ggits/GECLens/issues with the command you ran,
  the full error message, and your Python, spaCy and ERRANT versions (`geclens --version`, `pip show spacy errant`).
- **Propose a change:** fork the repository, create a branch, and open a pull request. Please add or update tests.
- **Run the tests:**

  ```bash
  pip install -e ".[dev]"
  python -m spacy download en_core_web_sm
  pytest
  ```

  The suite also checks that GECLens matches `errant_compare` on the bundled data, so any change to scoring must keep
  these tests passing.
- **Check against ERRANT on your own data:**
  `python scripts/check_against_errant.py src.txt ref.m2 sys1.txt [sys2.txt ...]`

For other questions, write to prakhargautam@jecjabalpur.ac.in.
