"""Shared helpers for the final FDS multiple-choice question workflow."""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

from pypdf import PdfReader


TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STUDY_CHAPTER_COUNT = 23
MODEL_PRIORITY = [
    "gpt-4.1",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "gpt-4.1-nano",
]
PROHIBITED_REFERENCES = (
    "according to the textbook",
    "according to the text",
    "according to the lecture",
    "in the lecture notes",
    "in this chapter",
    "in the provided section",
    "the passage states",
)


def iter_outline(items: list[Any], reader: PdfReader, depth: int = 0):
    for item in items:
        if isinstance(item, list):
            yield from iter_outline(item, reader, depth + 1)
            continue
        try:
            page_index = reader.get_destination_page_number(item)
        except Exception:
            continue
        yield depth, item.title.strip(), page_index


def extract_chapters(pdf_path: Path) -> list[dict[str, Any]]:
    reader = PdfReader(pdf_path)
    destinations = [
        (title, page_index)
        for depth, title, page_index in iter_outline(reader.outline or [], reader)
        if depth == 1
    ]
    if len(destinations) != 24:
        raise RuntimeError(
            "Expected 24 numbered FDS chapters from PDF bookmarks, "
            f"found {len(destinations)}."
        )

    chapters = []
    for index, (title, start_page) in enumerate(destinations):
        end_page = (
            destinations[index + 1][1] - 1
            if index + 1 < len(destinations)
            else len(reader.pages) - 1
        )
        page_text = [
            reader.pages[page_index].extract_text() or ""
            for page_index in range(start_page, end_page + 1)
        ]
        text = "\n\n".join(page_text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        chapters.append(
            {
                "number": index + 1,
                "title": title,
                "pdf_page_start": start_page + 1,
                "pdf_page_end": end_page + 1,
                "text": text,
                "character_count": len(text),
            }
        )
    return chapters


def select_model(requested_model: str) -> str:
    import openai

    if requested_model != "auto":
        return requested_model
    models = {
        model["id"]
        for model in openai.Model.list(request_timeout=30)["data"]
    }
    for candidate in MODEL_PRIORITY:
        if candidate in models:
            return candidate
    raise RuntimeError(
        "None of the EduGenie model candidates is available to this API key."
    )


def normalise_question(
    record: dict[str, Any],
    chapter: dict[str, Any],
    category: str,
) -> dict[str, Any]:
    question_parts = []
    scenario = record.get("scenario")
    if scenario:
        question_parts.append(str(scenario).strip())
    question_parts.append(str(record.get("question") or "").strip())
    full_question = "\n\n".join(part for part in question_parts if part)

    return {
        "id": "",
        "chapter_number": chapter["number"],
        "chapter_title": chapter["title"],
        "category": category,
        "bloom_level": record.get("objective"),
        "question_type": (
            "Multiple Choice"
            if record.get("question_type") == "Multiple"
            else "Open"
        ),
        "strategy": record.get("strategy"),
        "key_elements": record.get("key_elements"),
        "key_concepts": record.get("key_concepts"),
        "analysis": record.get("analysis"),
        "evaluation_target": record.get("evaluation_target"),
        "criteria": record.get("criteria"),
        "constraints": record.get("constraints"),
        "question": full_question,
        "options": record.get("options") or "",
        "answer": str(record.get("correct_answer") or "").strip(),
        "explanation": str(record.get("explanation") or "").strip(),
        "model": record.get("model"),
        "automated_checks": [],
    }


def validate_question(
    question: dict[str, Any],
    expected_level: str,
) -> list[str]:
    errors = []
    if question.get("bloom_level") != expected_level:
        errors.append(
            f"Bloom level was {question.get('bloom_level')!r}, "
            f"expected {expected_level!r}."
        )
    for field in ("question", "explanation"):
        if len(str(question.get(field) or "").strip()) < 20:
            errors.append(f"{field} is missing or too short.")
    lower_question = question.get("question", "").lower()
    for phrase in PROHIBITED_REFERENCES:
        if phrase in lower_question:
            errors.append(
                f"Question contains context-dependent phrase: {phrase!r}."
            )
    if question.get("question_type") == "Multiple Choice":
        options = str(question.get("options") or "")
        option_markers = re.findall(r"(?:^|\n)\s*[A-D][\).:]", options)
        if len(option_markers) < 4:
            errors.append(
                "Multiple-choice question does not contain four clearly "
                "labelled options."
            )
        if not re.search(r"\b[A-D]\b", question.get("answer", "")):
            errors.append(
                "Multiple-choice answer does not identify an option A-D."
            )
    return errors
