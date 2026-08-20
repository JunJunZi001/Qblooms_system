#!/usr/bin/env python3
"""Generate Understanding and Analyzing MCQ banks from the FDS lecture notes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

from dotenv import load_dotenv
import pypandoc

import fds_mcq_common as common


TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parent
DEFAULT_PDF = PROJECT_ROOT / "FDS-lecture-notes-2026-01-19.pdf"
DEFAULT_CHECKPOINT = TOOLS_ROOT / ".fds_mcq_question_bank_checkpoint.json"
OUTPUTS = {
    "Understanding": PROJECT_ROOT / "basic_concept_questions.docx",
    "Analyzing": PROJECT_ROOT / "higher_concept_quesitons.docx",
}
QUESTIONS_PER_CHAPTER = 5
OBJECTIVES = ("Understanding", "Analyzing")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--model", default="auto")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--fresh", action="store_true")
    return parser.parse_args()


def load_checkpoint(path: Path, fresh: bool) -> dict[str, Any]:
    if fresh or not path.exists():
        return {"model": None, "sets": {}, "failures": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def set_key(chapter_number: int, objective: str) -> str:
    return f"{chapter_number}:{objective}"


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def format_options_markdown(options: Any) -> str:
    option_pattern = re.compile(
        r"(?:^|\n)\s*([A-D])[\).:]\s*(.*?)(?=(?:\n\s*[A-D][\).:])|\Z)",
        re.DOTALL,
    )
    parsed = option_pattern.findall(str(options or ""))
    if len(parsed) != 4:
        return str(options or "").strip()
    return "\n\n".join(
        f"{letter}. {normalize_text(text)}"
        for letter, text in parsed
    )


def rebalance_answer_position(
    question: dict[str, Any],
    target_letter: str,
) -> None:
    option_pattern = re.compile(
        r"(?:^|\n)\s*([A-D])[\).:]\s*(.*?)(?=(?:\n\s*[A-D][\).:])|\Z)",
        re.DOTALL,
    )
    parsed_options = [
        (letter, text.strip())
        for letter, text in option_pattern.findall(str(question.get("options") or ""))
    ]
    answer_match = re.search(r"\b([A-D])\b", str(question.get("answer") or ""))
    if len(parsed_options) != 4 or not answer_match:
        return

    correct_letter = answer_match.group(1)
    correct_text = next(
        text for letter, text in parsed_options if letter == correct_letter
    )
    distractors = [
        (letter, text)
        for letter, text in parsed_options
        if letter != correct_letter
    ]
    target_index = ord(target_letter) - ord("A")
    reordered = list(distractors)
    reordered.insert(target_index, (correct_letter, correct_text))
    letter_mapping = {
        old_letter: new_letter
        for new_letter, (old_letter, _text) in zip("ABCD", reordered)
    }
    question["options"] = "\n".join(
        f"{letter}. {text}"
        for letter, (_old_letter, text) in zip("ABCD", reordered)
    )
    question["answer"] = target_letter
    explanation = str(question.get("explanation") or "")
    question["explanation"] = re.sub(
        r"\b([Oo]ption)\s+([A-D])\b",
        lambda match: f"{match.group(1)} {letter_mapping[match.group(2)]}",
        explanation,
    )


def rebalance_question_set(
    questions: list[dict[str, Any]],
    chapter_number: int,
    objective: str,
) -> None:
    objective_offset = 0 if objective == "Understanding" else 2
    for index, question in enumerate(questions):
        target_index = (
            (chapter_number - 1) * QUESTIONS_PER_CHAPTER
            + index
            + objective_offset
        ) % 4
        rebalance_answer_position(question, "ABCD"[target_index])


def validate_set(
    questions: list[dict[str, Any]],
    objective: str,
) -> list[str]:
    errors: list[str] = []
    if len(questions) != QUESTIONS_PER_CHAPTER:
        errors.append(
            f"received {len(questions)} questions; expected {QUESTIONS_PER_CHAPTER}"
        )

    stems: list[str] = []
    for index, question in enumerate(questions, start=1):
        prefix = f"Q{index}"
        if question.get("bloom_level") != objective:
            errors.append(f"{prefix}: wrong Bloom level")
        if question.get("question_type") != "Multiple Choice":
            errors.append(f"{prefix}: not multiple choice")
        stem = normalize_text(question.get("question"))
        if len(stem) < 25:
            errors.append(f"{prefix}: question is missing or too short")
        stems.append(stem)

        options = str(question.get("options") or "").strip()
        markers = re.findall(r"(?:^|\n)\s*([A-D])[\).:]", options)
        if sorted(set(markers)) != ["A", "B", "C", "D"]:
            errors.append(f"{prefix}: options do not contain exactly A-D")
        answer_match = re.search(r"\b([A-D])\b", str(question.get("answer") or ""))
        if not answer_match:
            errors.append(f"{prefix}: answer does not identify A-D")
        if len(normalize_text(question.get("explanation"))) < 25:
            errors.append(f"{prefix}: explanation is missing or too short")
        lower_stem = stem.lower()
        for phrase in common.PROHIBITED_REFERENCES:
            if phrase in lower_stem:
                errors.append(f"{prefix}: contains context-dependent phrase {phrase!r}")
        if objective == "Analyzing" and not question.get("strategy"):
            errors.append(f"{prefix}: missing analysis strategy")

    for left_index, left in enumerate(stems):
        for right_index, right in enumerate(stems[left_index + 1 :], left_index + 2):
            similarity = SequenceMatcher(
                None,
                re.sub(r"\W+", " ", left.lower()),
                re.sub(r"\W+", " ", right.lower()),
            ).ratio()
            if similarity >= 0.78:
                errors.append(
                    f"Q{left_index + 1} and Q{right_index} are too similar "
                    f"({similarity:.0%})"
                )
    return errors


def generation_purpose(objective: str) -> str:
    common = (
        "Generate exactly five distinct, self-contained multiple-choice questions for a "
        "university user study. Each question must have exactly four separately labelled "
        "options A-D and exactly one unambiguously correct answer. Use only facts and "
        "concepts supported by the supplied chapter. Make distractors plausible, similar "
        "in style and length, and based on realistic misconceptions. Cover different "
        "important ideas across the chapter; do not create near-duplicate questions. "
        "Students will not see the source text, so do not refer to a textbook, chapter, "
        "lecture, passage, supplied text, or unprovided figure/table."
    )
    if objective == "Understanding":
        return (
            common
            + " Target Bloom's Understanding level through varied restatement, "
            "classification, inference, exemplification, and summarisation tasks. Do not "
            "reduce all five questions to simple factual recall."
        )
    return (
        common
        + " Target Bloom's Analyzing level. Require students to compare relationships, "
        "distinguish assumptions, classify a concrete case, predict consequences, or "
        "identify the structure of a problem. Include all scenario information needed to "
        "reason to the answer, and avoid mere definition or recall questions."
    )


def generate_set(
    app_module,
    chapter: dict[str, Any],
    objective: str,
    model: str,
    max_attempts: int,
) -> list[dict[str, Any]]:
    last_error = "unknown generation failure"
    for attempt in range(1, max_attempts + 1):
        try:
            result = app_module.generate_qa(
                objective,
                f"Assess mastery of Chapter {chapter['number']}: {chapter['title']}.",
                generation_purpose(objective),
                "",
                "Multiple",
                chapter["text"],
                None,
                QUESTIONS_PER_CHAPTER,
                None,
                f"Chapter {chapter['number']}: {chapter['title']}",
                model,
                None,
            )
            _display, state, status, _timing = result
            if not status.startswith("Generated Q&A successfully"):
                raise RuntimeError(status)
            records = (state or {}).get("question_list") or []
            questions = [
                common.normalise_question(
                    record,
                    chapter,
                    (
                        "Basic concept / comprehension"
                        if objective == "Understanding"
                        else "Higher concept"
                    ),
                )
                for record in records[-QUESTIONS_PER_CHAPTER:]
            ]
            rebalance_question_set(questions, chapter["number"], objective)
            errors = validate_set(questions, objective)
            if errors:
                raise ValueError("; ".join(errors))
            for index, question in enumerate(questions, start=1):
                question["id"] = (
                    f"C{chapter['number']:02d}-"
                    f"{'B' if objective == 'Understanding' else 'H'}Q{index}"
                )
                question["generation_attempt"] = attempt
            return questions
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < max_attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(
        f"Chapter {chapter['number']} {objective} failed after "
        f"{max_attempts} attempts: {last_error}"
    )


def render_markdown(
    objective: str,
    chapters: list[dict[str, Any]],
    sets: dict[str, list[dict[str, Any]]],
) -> str:
    title = (
        "Basic Concept Questions"
        if objective == "Understanding"
        else "Higher Concept Questions"
    )
    subtitle = (
        "Bloom’s Taxonomy level: Understanding"
        if objective == "Understanding"
        else "Bloom’s Taxonomy level: Analyzing"
    )
    lines = [
        f"# {title}",
        "",
        subtitle,
        "",
        f"{QUESTIONS_PER_CHAPTER} multiple-choice questions per chapter.",
        "",
    ]
    for chapter in chapters:
        questions = sets.get(set_key(chapter["number"], objective), [])
        lines.extend(
            [
                f"# Chapter {chapter['number']}: {chapter['title']}",
                "",
            ]
        )
        for index, question in enumerate(questions, start=1):
            lines.extend(
                [
                    f"## Question {index}",
                    "",
                    normalize_text(question["question"]),
                    "",
                    format_options_markdown(question["options"]),
                    "",
                    f"**Answer:** {question['answer']}",
                    "",
                    f"**Explanation:** {normalize_text(question['explanation'])}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def write_docx_outputs(
    chapters: list[dict[str, Any]],
    sets: dict[str, list[dict[str, Any]]],
) -> None:
    for objective, output_path in OUTPUTS.items():
        markdown = render_markdown(objective, chapters, sets)
        pypandoc.convert_text(
            markdown,
            "docx",
            format="md",
            outputfile=str(output_path),
            extra_args=["--standalone"],
        )


def main() -> int:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from .env.")
    if not args.pdf.exists():
        raise FileNotFoundError(args.pdf)
    if args.workers < 1:
        raise ValueError("--workers must be at least 1.")

    os.environ["EDUGENIE_SKIP_MODEL_DISCOVERY"] = "1"
    import app as app_module

    app_module.log_activity = lambda *args, **kwargs: None
    original_build_question_record = app_module.build_question_record

    def build_question_record_without_punctuation_loss(*record_args, **record_kwargs):
        record = original_build_question_record(*record_args, **record_kwargs)
        qa_item = record_args[0]
        record["question"] = qa_item.question
        record["explanation"] = qa_item.explanation
        return record

    app_module.build_question_record = build_question_record_without_punctuation_loss

    chapters = common.extract_chapters(args.pdf)[: common.STUDY_CHAPTER_COUNT]
    checkpoint = load_checkpoint(args.checkpoint, args.fresh)
    model = checkpoint.get("model") or common.select_model(args.model)
    if args.model != "auto" and checkpoint.get("model") not in (None, args.model):
        raise RuntimeError(
            f"Checkpoint uses {checkpoint['model']}; use --fresh to change models."
        )
    checkpoint["model"] = model
    checkpoint.setdefault("sets", {})
    checkpoint.setdefault("failures", {})
    for chapter in chapters:
        for objective in OBJECTIVES:
            questions = checkpoint["sets"].get(
                set_key(chapter["number"], objective)
            )
            if questions:
                rebalance_question_set(
                    questions,
                    chapter["number"],
                    objective,
                )

    print(f"MODEL_SELECTED {model}", flush=True)
    print(f"STUDY_CHAPTERS {len(chapters)}", flush=True)

    for chapter in chapters:
        pending = [
            objective
            for objective in OBJECTIVES
            if set_key(chapter["number"], objective) not in checkpoint["sets"]
        ]
        if not pending:
            print(
                f"CHAPTER_SKIPPED {chapter['number']}/{len(chapters)}",
                flush=True,
            )
            continue

        with ThreadPoolExecutor(max_workers=min(args.workers, len(pending))) as executor:
            futures = {
                executor.submit(
                    generate_set,
                    app_module,
                    chapter,
                    objective,
                    model,
                    args.max_attempts,
                ): objective
                for objective in pending
            }
            for future in as_completed(futures):
                objective = futures[future]
                key = set_key(chapter["number"], objective)
                try:
                    checkpoint["sets"][key] = future.result()
                    checkpoint["failures"].pop(key, None)
                    print(
                        f"SET_DONE chapter={chapter['number']} "
                        f"objective={objective} count={QUESTIONS_PER_CHAPTER}",
                        flush=True,
                    )
                except Exception as exc:
                    checkpoint["failures"][key] = str(exc)
                    print(
                        f"SET_FAILED chapter={chapter['number']} "
                        f"objective={objective} error={type(exc).__name__}",
                        flush=True,
                    )
        save_checkpoint(args.checkpoint, checkpoint)
        write_docx_outputs(chapters, checkpoint["sets"])
        print(
            f"CHAPTER_DONE {chapter['number']}/{len(chapters)}",
            flush=True,
        )

    save_checkpoint(args.checkpoint, checkpoint)
    write_docx_outputs(chapters, checkpoint["sets"])

    expected_sets = len(chapters) * len(OBJECTIVES)
    completed_sets = sum(
        1
        for chapter in chapters
        for objective in OBJECTIVES
        if set_key(chapter["number"], objective) in checkpoint["sets"]
    )
    total_questions = sum(
        len(checkpoint["sets"].get(set_key(chapter["number"], objective), []))
        for chapter in chapters
        for objective in OBJECTIVES
    )
    print(f"COMPLETED_SETS {completed_sets}/{expected_sets}", flush=True)
    print(f"TOTAL_QUESTIONS {total_questions}", flush=True)
    print(f"TOTAL_FAILURES {len(checkpoint['failures'])}", flush=True)
    for output_path in OUTPUTS.values():
        print(f"OUTPUT_READY {output_path}", flush=True)
    return 0 if completed_sets == expected_sets and not checkpoint["failures"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            "Generation interrupted; progress is preserved in the checkpoint.",
            file=sys.stderr,
        )
        raise SystemExit(130)
