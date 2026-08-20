# FDS Question-Bank Utilities

This directory contains internal utilities used to prepare the final
multiple-choice question bank for the Foundations of Data Science (FDS) case
study. These utilities are separate from the Qblooms web application and are
not required to run the website.

## Final question-bank workflow

The final corpus contains 230 multiple-choice questions from 23 teaching
chapters:

- five Understanding questions per chapter;
- five Analyzing questions per chapter; and
- ten questions per chapter in total.

Chapter 24 of the source PDF is a dataset index and is not included.

### `batch_generate_fds_mcqs.py`

This is the main generation script. It:

1. extracts the 24 bookmarked sections from
   `FDS-lecture-notes-2026-01-19.pdf` and keeps the first 23 teaching chapters;
2. calls the same `generate_qa` pipeline used by `app.py`;
3. generates one five-question Understanding set and one five-question
   Analyzing set for each chapter;
4. validates the structure of each set;
5. rebalances correct-answer positions across A--D;
6. saves progress to `.fds_mcq_question_bank_checkpoint.json`; and
7. writes `basic_concept_questions.docx` and
   `higher_concept_quesitons.docx` in the project root.

The structural checks reject a set when it has the wrong number of questions,
an incorrect Bloom label, a non-multiple-choice record, incomplete A--D
options, an invalid answer label, a short stem or explanation, a reference to
source material unavailable to students, a missing Analyzing strategy, or two
stems with a `SequenceMatcher` similarity of at least 0.78.

These checks verify machine-readable structure and selected surface
constraints. They do not establish factual correctness, pedagogical quality,
or genuine Bloom-level alignment.

Run from the project root with an `OPENAI_API_KEY` in `.env`:

```bash
.venv/bin/python tools/batch_generate_fds_mcqs.py
```

Useful options include `--model`, `--workers`, `--max-attempts`, `--pdf`,
`--checkpoint`, and `--fresh`.

### `fds_mcq_common.py`

This is a shared support module. It provides:

- PDF bookmark traversal and chapter extraction;
- model selection;
- question-record normalisation;
- prohibited source-reference phrases; and
- basic record validation.

It is imported by the generation script and is not intended to be run
directly.

## Validation scope

The included workflow performs generation-time structural validation only.
Invalid sets are rejected and retried within `batch_generate_fds_mcqs.py`.
There is no separate content-audit or repair workflow in this directory.

Factual correctness, pedagogical suitability, and substantive Bloom alignment
must be assessed separately by a qualified reviewer.

## Generated and private files

The following files are generated intermediates and should not be committed:

```text
.fds_*.json
__pycache__/
*.pyc
activity.log
```

Question-bank DOCX files, source PDFs, API keys, and other private study
materials should also remain outside the public repository unless their
release has been explicitly approved.
