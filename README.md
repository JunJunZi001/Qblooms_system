# Qblooms

Qblooms is a web application for instructors and students to generate and
refine educational questions, reference answers, and explanations from
textbook text or PDF files. Generation is conditioned on one of the six
cognitive objectives in the revised Bloom taxonomy:

- Remembering
- Understanding
- Applying
- Analyzing
- Evaluating
- Creating

The system treats generated questions as reviewable drafts. It combines
objective-specific prompts, typed Pydantic output schemas, parser repair,
long-document retrieval, local few-shot retrieval, and a human-in-the-loop
refinement workflow.

A deployed version is available at
[https://chatty.inf.ed.ac.uk/](https://chatty.inf.ed.ac.uk/).

## Features

- Generate multiple-choice or open-ended questions from text and PDF input.
- Select a Bloom-level cognitive objective and an available OpenAI model.
- Add an educational purpose, learning goal, and optional user examples.
- Retrieve relevant chunks when source material is too long for one prompt.
- Retrieve curated few-shot examples from a local Chroma vector store.
- Parse model responses into typed question, answer, explanation, option, and
  planning fields.
- Repair malformed structured responses through the LangChain parser.
- Rate generated questions and request revisions or replacements.
- Save, clear, and export the in-memory question bank as an Excel file.
- Show user-facing status messages for generation and API failures.
- Record privacy-conscious operational events without logging prompts,
  uploaded text, or generated educational content.

## Project Structure

```text
app.py                  Main Gradio/FastAPI application and workflow
edugenie.py             Bloom-specific prompts and Pydantic schemas
QuestionsText/          Curated few-shot examples
accessibility.html      Accessibility statement served by the application
docs/diagrams/          Architecture and user-flow diagrams
tools/requirements.txt  Python dependencies
tools/.env.example      Environment-variable template
tools/README.md         Optional FDS case-study utility documentation
tools/batch_generate_fds_mcqs.py  Optional FDS MCQ generation script
tools/fds_mcq_common.py           Shared support for the FDS generator
```

`ChromaStore/`, `questionbank.xlsx`, activity logs, checkpoints, and exported
study files are generated local data and are not required in the repository.

## Installation

Python 3.11 is recommended.

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r tools/requirements.txt
   ```

3. Create the local environment file:

   ```bash
   cp tools/.env.example .env
   ```

4. Set your OpenAI API key in `.env`:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Start the application:

   ```bash
   python app.py
   ```

The local Chroma vector store is created automatically from the examples in
`QuestionsText/` when the application starts.

## FDS Case Study

The dissertation case study used lecture notes from 23 teaching chapters of a
Foundations of Data Science course. The batch workflow generated five
Understanding and five Analyzing multiple-choice questions per chapter, for a
total of 230 questions. The case-study scripts are documented separately in
[`tools/README.md`](tools/README.md); they are not required to run the website.
They perform generation-time structural validation but do not include a
separate content-audit or repair workflow.

The source lecture notes and generated study materials are not included in the
public repository unless their release has been separately authorised.

## Limitations

Structural parsing and validation do not guarantee factual correctness,
pedagogical quality, or genuine Bloom-level alignment. Generated questions
should be reviewed by an instructor before they are used for formal teaching
or assessment.
