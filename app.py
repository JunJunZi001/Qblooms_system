from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.globals import set_debug, set_verbose

from edugenie import OpenList, QA_STRUCT, SYSTEM_TEMPLATE, HUMAN_TEMPLATE, Q_TYPE, LEARNING_OBJECTIVE
from edugenie import REFINE_TEMPLATE, RATING_MEANING, REFINE_NEXT_STEP, REFINE_TEMPLATE_EXISTING
from edugenie import INITIAL_OBJECTIVE
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
import gradio as gr
import base64
from io import BytesIO
from datetime import datetime, timezone
import hmac
import json
import os
from pathlib import Path
import pandas as pd
import hashlib
import re
import time
import chromadb
import openai
from pypdf import PdfReader
import uvicorn

set_debug(False)
set_verbose(False)


def safe_log(text):
    """Optional debug logging. Disabled by default to avoid storing user content."""
    if os.getenv("EDUGENIE_DEBUG_LOGS", "").lower() not in {"1", "true", "yes"}:
        return
    try:
        print(text)
    except UnicodeEncodeError:
        fallback = str(text).encode("ascii", errors="backslashreplace").decode("ascii")
        print(fallback)


def friendly_api_error(exc):
    """Return user-friendly error text for API/runtime failures."""
    message = str(exc).lower()
    if "exceeded your current quota" in message or "ratelimit" in message or "429" in message:
        return "API quota exceeded (HTTP 429). Please check OpenAI billing/usage and ensure this API key has available balance."
    return f"Request failed: {type(exc).__name__}. Please check terminal logs for details."


def timing_card(operation, started_at, succeeded=True):
    """Build a compact timing summary for the user interface."""
    elapsed = time.perf_counter() - started_at
    state_class = "timing-success" if succeeded else "timing-error"
    state_label = "Completed" if succeeded else "Stopped"
    return (
        f'<div class="timing-card {state_class}" role="status">'
        '<div class="timing-icon">⏱</div>'
        '<div><div class="timing-label">'
        f'{operation} time</div><div class="timing-value">{elapsed:.2f} seconds</div></div>'
        f'<div class="timing-state">{state_label}</div>'
        '</div>'
    )


# Load `.env` from the project root (same directory as this file).
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

openai.api_key = OPENAI_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parent
EXAMPLE_ROOT = PROJECT_ROOT / "QuestionsText"
CHROMA_DIR = PROJECT_ROOT / "ChromaStore"
CHROMA_COLLECTION = "edugenie_fewshot_examples"
RAG_EXAMPLE_COUNT = 3
EMBEDDING_MODEL = "text-embedding-3-small"
TEXTBOOK_CHUNK_SIZE = 2500
TEXTBOOK_CHUNK_OVERLAP = 300
TEXTBOOK_DIRECT_CHAR_LIMIT = 12000
MAX_TEXTBOOK_PROMPT_CHUNKS = 4
MAX_TEXTBOOK_RETRIEVAL_CHUNKS = 24
DEFAULT_MODEL = os.getenv("EDUGENIE_DEFAULT_MODEL", "gpt-4o")
MODEL_CANDIDATES = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
]
ACTIVITY_LOG_PATH = PROJECT_ROOT / "activity.log"
LOG_SALT = os.getenv("EDUGENIE_LOG_SALT") or OPENAI_API_KEY or "edugenie-activity-log"
CUSTOM_CSS = """
footer,
.footer {
    display: none !important;
}

.timing-card {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-top: 0.25rem;
    padding: 0.85rem 1rem;
    border: 1px solid #dbe4f0;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
    box-shadow: 0 4px 14px rgba(30, 64, 175, 0.08);
}

.timing-icon {
    display: grid;
    width: 2.25rem;
    height: 2.25rem;
    place-items: center;
    border-radius: 50%;
    background: #dbeafe;
    font-size: 1.15rem;
}

.timing-label {
    color: #475569;
    font-size: 0.82rem;
    font-weight: 600;
}

.timing-value {
    color: #0f172a;
    font-size: 1.05rem;
    font-weight: 700;
}

.timing-state {
    margin-left: auto;
    color: #047857;
    font-size: 0.82rem;
    font-weight: 700;
}

.timing-error .timing-state {
    color: #b91c1c;
}

.edugenie-legal {
    margin-top: 1.5rem;
    padding: 1rem 1.15rem;
    border-top: 1px solid #dbe4f0;
    border-radius: 10px;
    background: #f8fafc;
    color: #475569;
    font-size: 0.88rem;
    line-height: 1.55;
    text-align: center;
}

.edugenie-legal p {
    margin: 0.2rem 0;
}

.edugenie-legal a {
    color: #2563eb;
    font-weight: 600;
    text-decoration: none;
}

.edugenie-legal a:hover,
.edugenie-legal a:focus {
    text-decoration: underline;
}
"""
LEGAL_FOOTER_HTML = """
<div class="edugenie-legal" role="contentinfo" aria-label="Privacy and accessibility information">
    <p>
        This website does not collect any personal information. Log information contains only a
        pseudonymous user ID, timestamp, and action name.
    </p>
    <p>
        For further details, please see the
        <a href="https://uoe.sharepoint.com/sites/inf-computing/SitePages/Privavcy.aspx"
           target="_blank" rel="noopener noreferrer">Privacy Statement</a>
        and the
        <a href="/accessibility.html">Accessibility Statement</a>.
    </p>
</div>
"""
CUSTOM_JS = """
() => {
    const replacements = new Map([
        ["将文件拖放到此处", "Drop file here"],
        ["点击上传", "Click to upload"],
        ["- 或 -", "- or -"],
        ["或", "or"],
        ["通过 API 使用", ""],
        ["使用 Gradio 构建", ""],
    ]);

    const replaceText = () => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const textNodes = [];
        while (walker.nextNode()) {
            textNodes.push(walker.currentNode);
        }
        for (const node of textNodes) {
            let text = node.nodeValue;
            for (const [source, target] of replacements.entries()) {
                text = text.replaceAll(source, target);
            }
            if (text !== node.nodeValue) {
                node.nodeValue = text;
            }
        }
        document.querySelectorAll("footer, .footer").forEach((element) => {
            element.style.display = "none";
        });
    };

    replaceText();
    let pending = false;
    const scheduleReplace = () => {
        if (pending) {
            return;
        }
        pending = true;
        window.requestAnimationFrame(() => {
            pending = false;
            replaceText();
        });
    };
    new MutationObserver(scheduleReplace).observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
    });
}
"""


def get_available_model_choices():
    """Return available chat models from the API key, limited to safe text-generation choices."""
    if os.getenv("EDUGENIE_SKIP_MODEL_DISCOVERY") == "1":
        return MODEL_CANDIDATES
    try:
        model_ids = {model["id"] for model in openai.Model.list()["data"]}
        choices = [model for model in MODEL_CANDIDATES if model in model_ids]
        if DEFAULT_MODEL in model_ids and DEFAULT_MODEL not in choices:
            choices.insert(0, DEFAULT_MODEL)
        return choices or [DEFAULT_MODEL]
    except Exception as exc:
        safe_log(f"model discovery failed: {type(exc).__name__}")
        return [DEFAULT_MODEL]


MODEL_CHOICES = get_available_model_choices()
DEFAULT_MODEL_CHOICE = DEFAULT_MODEL if DEFAULT_MODEL in MODEL_CHOICES else MODEL_CHOICES[0]


def create_conversation(model_name):
    chat_model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.7, model_name=model_name)
    return ConversationChain(
        llm=chat_model,
        memory=ConversationBufferMemory(),
        verbose=False,
    )


def ensure_model_state(state, model_name, reset_memory=False):
    if state is None:
        state = {}
    selected_model = model_name or DEFAULT_MODEL
    if state.get("model_name") != selected_model or "conversation" not in state:
        state["conversation"] = create_conversation(selected_model)
        state["model_name"] = selected_model
    elif reset_memory:
        state["conversation"].memory = ConversationBufferMemory()
    state.setdefault("question_list", [])
    state.setdefault("saved_to_export", False)
    return state


def get_request_value(request, header_name):
    headers = getattr(request, "headers", {}) or {}
    try:
        return headers.get(header_name, "")
    except AttributeError:
        return ""


def get_anonymous_user_id(request):
    """Return a stable pseudonymous ID without storing raw IP or user agent."""
    if request is None:
        return "unknown"

    forwarded_for = get_request_value(request, "x-forwarded-for")
    real_ip = get_request_value(request, "x-real-ip")
    client = getattr(request, "client", None)
    client_host = getattr(client, "host", "") if client else ""
    user_agent = get_request_value(request, "user-agent")
    source = (forwarded_for.split(",")[0].strip() or real_ip or client_host or "unknown")
    digest_source = f"{source}|{user_agent}".encode("utf-8", errors="ignore")
    digest = hmac.new(LOG_SALT.encode("utf-8"), digest_source, hashlib.sha256).hexdigest()
    return digest[:16]


def log_activity(event, request=None, metadata=None):
    """Write privacy-preserving activity logs without user prompts or generated content."""
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": get_anonymous_user_id(request),
        "metadata": metadata or {},
    }
    try:
        with ACTIVITY_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        ACTIVITY_LOG_PATH.chmod(0o600)
    except Exception as exc:
        safe_log(f"activity logging failed: {type(exc).__name__}")


def log_page_load(request: gr.Request):
    log_activity("page_load", request)


def infer_question_type(text):
    """Infer whether an example question is multiple choice or open."""
    option_pattern = r"(?im)^\s*(?:[A-Da-d])[\.\)]\s+"
    if "correct answer" in text.lower() and re.search(option_pattern, text):
        return "Multiple"
    return "Open"


def split_text(text, chunk_size=2000, chunk_overlap=250):
    """Split text into overlapping chunks, preferring paragraph or sentence boundaries."""
    cleaned = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks = []
    start = 0
    while start < len(cleaned):
        hard_end = min(start + chunk_size, len(cleaned))
        end = hard_end
        if hard_end < len(cleaned):
            window = cleaned[start:hard_end]
            boundary_candidates = [
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind("? "),
                window.rfind("! "),
            ]
            boundary = max(boundary_candidates)
            if boundary > chunk_size * 0.55:
                end = start + boundary + 1

        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(end - chunk_overlap, start + 1)

    return chunks


def get_embedding(text):
    response = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    return response["data"][0]["embedding"]


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def get_uploaded_file_path(uploaded_file):
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, str):
        return uploaded_file
    return getattr(uploaded_file, "name", None) or getattr(uploaded_file, "path", None)


def extract_pdf_text(uploaded_file):
    """Extract text from a user-uploaded PDF without logging or persisting its content."""
    file_path = get_uploaded_file_path(uploaded_file)
    if not file_path:
        return "", {"pdf_pages": 0, "pdf_chars": 0}

    reader = PdfReader(file_path)
    page_texts = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            page_texts.append(f"[Page {page_index}]\n{text}")

    pdf_text = "\n\n".join(page_texts).strip()
    return pdf_text, {"pdf_pages": len(reader.pages), "pdf_chars": len(pdf_text)}


def inspect_pdf_upload(uploaded_file, request: gr.Request):
    """Show privacy-safe PDF upload/extraction status without storing extracted content."""
    if uploaded_file is None:
        return ""
    try:
        _, metadata = extract_pdf_text(uploaded_file)
    except Exception as exc:
        log_activity("pdf_upload_failed", request, {"error_type": type(exc).__name__})
        return f"PDF upload detected, but text extraction failed: {type(exc).__name__}. Please use a text-based PDF."

    pages = metadata.get("pdf_pages", 0)
    chars = metadata.get("pdf_chars", 0)
    estimated_chunks = len(split_text("x" * chars, TEXTBOOK_CHUNK_SIZE, TEXTBOOK_CHUNK_OVERLAP)) if chars else 0
    log_activity(
        "pdf_uploaded",
        request,
        {
            "pdf_pages": pages,
            "pdf_chars": chars,
            "estimated_chunks": estimated_chunks,
        },
    )
    if chars == 0:
        return f"PDF uploaded: {pages} page(s), but no extractable text was found. Scanned/image-only PDFs may need OCR."
    return f"PDF uploaded: {pages} page(s), about {chars:,} extractable characters."


def build_textbook_context(textbook_section, uploaded_pdf, retrieval_query):
    """Combine typed/PDF textbook inputs and select prompt-safe chunks for long content."""
    typed_text = (textbook_section or "").strip()
    pdf_text, pdf_metadata = extract_pdf_text(uploaded_pdf)
    sources = []
    combined_parts = []
    if typed_text:
        sources.append("typed_text")
        combined_parts.append(typed_text)
    if pdf_text:
        sources.append("pdf_upload")
        combined_parts.append(pdf_text)

    full_text = "\n\n".join(combined_parts).strip()
    if not full_text:
        return "", {
            "source_types": [],
            "total_chars": 0,
            "chunks_total": 0,
            "chunks_used": 0,
            **pdf_metadata,
        }

    chunks = split_text(full_text, TEXTBOOK_CHUNK_SIZE, TEXTBOOK_CHUNK_OVERLAP)
    metadata = {
        "source_types": sources,
        "total_chars": len(full_text),
        "chunks_total": len(chunks),
        "chunks_used": len(chunks),
        "chunk_strategy": "full_text",
        **pdf_metadata,
    }
    if len(full_text) <= TEXTBOOK_DIRECT_CHAR_LIMIT:
        return full_text, metadata

    candidate_chunks = chunks[:MAX_TEXTBOOK_RETRIEVAL_CHUNKS]
    query = (retrieval_query or "").strip() or full_text[:2000]
    try:
        query_embedding = get_embedding(query[:8000])
        scored_chunks = []
        for index, chunk in enumerate(candidate_chunks):
            score = cosine_similarity(query_embedding, get_embedding(chunk))
            scored_chunks.append((score, index, chunk))
        selected = sorted(scored_chunks, reverse=True)[:MAX_TEXTBOOK_PROMPT_CHUNKS]
        selected = sorted(selected, key=lambda item: item[1])
        selected_chunks = [chunk for _, _, chunk in selected]
        metadata["chunk_strategy"] = "embedding_top_chunks"
    except Exception as exc:
        safe_log(f"textbook chunk selection failed: {type(exc).__name__}")
        selected_chunks = candidate_chunks[:MAX_TEXTBOOK_PROMPT_CHUNKS]
        metadata["chunk_strategy"] = "first_chunks_fallback"

    metadata["chunks_used"] = len(selected_chunks)
    prompt_text = "\n\n".join(
        f"[Selected textbook excerpt {index}]\n{chunk}"
        for index, chunk in enumerate(selected_chunks, start=1)
    )
    return prompt_text, metadata


def load_fewshot_documents():
    """Load local example questions and attach metadata used for retrieval filters."""
    records = []
    if not EXAMPLE_ROOT.exists():
        return records, []

    for file_path in sorted(EXAMPLE_ROOT.glob("*/*.txt")):
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        learning_objective = file_path.parent.name
        question_type = infer_question_type(content)
        for idx, chunk in enumerate(split_text(content)):
            records.append(
                {
                    "document": chunk,
                    "metadata": {
                        "LearningObjective": learning_objective,
                        "question_type": question_type,
                        "source": str(file_path.relative_to(PROJECT_ROOT)),
                        "chunk_index": idx,
                    },
                }
            )

    ids = []
    for record in records:
        source = record["metadata"].get("source", "unknown")
        chunk_index = record["metadata"].get("chunk_index", 0)
        digest = hashlib.sha1(record["document"].encode("utf-8")).hexdigest()[:12]
        ids.append(f"{source}:{chunk_index}:{digest}")

    return records, ids


def initialize_fewshot_vector_store():
    """Create or refresh the local Chroma store for few-shot examples."""
    records, ids = load_fewshot_documents()
    if not records:
        safe_log("No few-shot documents found. RAG examples disabled.")
        return None

    try:
        CHROMA_DIR.mkdir(exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(CHROMA_COLLECTION)
        manifest = "\n".join(ids)
        manifest_path = CHROMA_DIR / "manifest.txt"
        existing_manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        existing_count = collection.count()

        if existing_manifest != manifest or existing_count != len(records):
            safe_log("Refreshing Chroma few-shot example store.")
            try:
                client.delete_collection(CHROMA_COLLECTION)
            except Exception:
                pass
            collection = client.get_or_create_collection(CHROMA_COLLECTION)
            collection.add(
                ids=ids,
                documents=[record["document"] for record in records],
                metadatas=[record["metadata"] for record in records],
                embeddings=[get_embedding(record["document"]) for record in records],
            )
            manifest_path.write_text(manifest, encoding="utf-8")
        else:
            safe_log(f"Loaded Chroma few-shot example store with {existing_count} chunks.")

        return collection
    except Exception as exc:
        safe_log(f"RAG vector store initialization failed: {exc}")
        return None


FEWSHOT_VECTOR_STORE = initialize_fewshot_vector_store()


def retrieve_fewshot_examples(textbook_section, q_type):
    """Retrieve up to three question examples matching the selected question type."""
    query = (textbook_section or "").strip()
    if FEWSHOT_VECTOR_STORE is None or not query:
        return ""

    try:
        results = FEWSHOT_VECTOR_STORE.query(
            query_embeddings=[get_embedding(query)],
            n_results=RAG_EXAMPLE_COUNT,
            where={"question_type": q_type},
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        safe_log(f"RAG retrieval failed: {exc}")
        return ""

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        safe_log(f"No RAG examples found for question_type={q_type}.")
        return ""

    formatted_examples = []
    for idx, (document, metadata, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        source = metadata.get("source", "unknown source")
        formatted_examples.append(
            f"Example {idx} (source: {source}, distance: {distance:.2f}):\n{document}"
        )

    safe_log(f"Retrieved {len(formatted_examples)} RAG examples for question_type={q_type}.")
    return (
        "The following examples were retrieved from the local question bank because they are similar "
        "to the textbook section and match the selected question type. Use them as few-shot guidance "
        "for style, difficulty, and structure, but do not copy them.\n"
        + "\n\n".join(formatted_examples)
    )


def clear_questions(state, request: gr.Request):
    log_activity(
        "clear_questions",
        request,
        {"rows_before_clear": len(state.get("question_list") or [])},
    )
    state['question_list'] = []
    state['saved_to_export'] = False
    return state, "", "", "Cleared in-memory and displayed Q&As.", ""


def build_question_record(qa_item, objective, q_type, learning_goal, text_name, model_name):
    """Convert a parsed QA object into a row that can be saved/exported."""
    return {
        "objective": objective,
        "question_type": q_type,
        "learning_goal": learning_goal,
        "strategy": getattr(qa_item, 'strategy', None),
        "key_elements": getattr(qa_item, 'key_elements', None),
        "key_concepts": getattr(qa_item, 'key_concepts', None),
        "scenario": getattr(qa_item, 'scenario', None),
        "analysis": getattr(qa_item, 'analysis', None),
        "evaluation_target": getattr(qa_item, 'evaluation_target', None),
        "criteria": getattr(qa_item, 'criteria', None),
        "constraints": getattr(qa_item, 'constraints', None),
        "question": qa_item.question.replace(',', ' '),
        "options": getattr(qa_item, 'options', ''),
        "correct_answer": qa_item.correct_answer,
        "explanation": qa_item.explanation.replace(',', ' '),
        "textbook_section": text_name,
        "model": model_name,
    }


def generate_qa(objective, learning_goal, qa_purpose, question_examples, q_type, textbook_section, textbook_pdf, num, state, text_name, model_name, request: gr.Request):
    """
    Generates a question,  an answer and an explanation based on the given arguments.

    This function uses the OpenAI GPT-4 model to generate a question and answer pair. 
    The type of question, learning objective, and textbook section are used to guide the generation process.

    Parameters:
    objective (str): The learning objective to base the question on.
    q_type (str): The type of question to generate. Can be 'Open' or 'Multipl' for multiple choice.
    textbook_section (str): The section of the textbook to base the question on.
    state (dict): A dictionary containing the current state of the conversation. 
                  The 'conversation' key should contain an instance of ConversationChain.
    num (int): The number of questions to generate.

    Returns:
    qa (str): A string containing the generated question and answer.
    state (dict): A dictionary containing the updated state of the conversation.
    """
    started_at = time.perf_counter()
    log_activity(
        "generate_qa_started",
        request,
        {
            "objective": objective,
            "question_type": q_type,
            "requested_count": int(num or 0),
            "text_name": text_name,
            "model": model_name or DEFAULT_MODEL,
            "has_learning_goal": bool((learning_goal or "").strip()),
            "has_qa_purpose": bool((qa_purpose or "").strip()),
            "has_user_examples": bool((question_examples or "").strip()),
            "has_textbook_section": bool((textbook_section or "").strip()),
            "has_pdf_upload": textbook_pdf is not None,
        },
    )
    state = ensure_model_state(state, model_name, reset_memory=True)
    parser = PydanticOutputParser(pydantic_object=QA_STRUCT[objective])
    context_parts = []
    if learning_goal != "":
        context_parts.append(
            f"The question should assess whether the student has mastered the specified learning goal.\nLearning Goal: {learning_goal}"
        )
    if qa_purpose != "":
        context_parts.append(f"Purpose of these generated questions: {qa_purpose}")
    educational_context = "\n".join(context_parts)

    retrieval_query = "\n".join(
        str(part)
        for part in [objective, q_type, text_name, learning_goal, qa_purpose]
        if part
    )
    try:
        textbook_prompt_text, textbook_metadata = build_textbook_context(textbook_section, textbook_pdf, retrieval_query)
    except Exception as exc:
        err = f"Could not read the uploaded PDF: {type(exc).__name__}. Please check that it is a text-based PDF."
        safe_log(f"PDF/textbook preparation failed: {type(exc).__name__}")
        duration = time.perf_counter() - started_at
        log_activity("generate_qa_failed", request, {"error_type": type(exc).__name__, "stage": "textbook_preparation", "duration_seconds": round(duration, 3)})
        return "", state, err, timing_card("Generation", started_at, succeeded=False)
    if not textbook_prompt_text:
        duration = time.perf_counter() - started_at
        log_activity("generate_qa_failed", request, {"reason": "empty_textbook_input", "stage": "textbook_preparation", "duration_seconds": round(duration, 3)})
        return "", state, "Please enter a textbook section or upload a readable PDF before generating Q&As.", timing_card("Generation", started_at, succeeded=False)


    example_parts = []
    if question_examples != "":
        safe_log("User-provided few-shot examples supplied.")
        example_parts.append(
            "The following are user-provided questions optimized for student learning. "
            "The generated examples should be of a similar level of difficulty and have a similar, "
            f"but not identical style to the example questions.\nExamples: {question_examples}"
        )
    else:
        safe_log("User-provided few-shot examples: none")

    rag_examples = retrieve_fewshot_examples(textbook_prompt_text, q_type)
    if rag_examples != "":
        safe_log("RAG few-shot examples retrieved.")
        example_parts.append(rag_examples)
    else:
        safe_log("Retrieved RAG few-shot examples: none")

    examples = "\n\n".join(example_parts)
    safe_log(f"Final few-shot examples prepared (length={len(examples)}).")
    #     "The educational context for the assessment: " + edu_context
    safe_log(f"Number of questions is {num}")
    message = "System: " + SYSTEM_TEMPLATE + "\nHuman: " + \
            HUMAN_TEMPLATE.format(N=num,
                                    q_type=Q_TYPE[q_type],
                                    learning_objective=LEARNING_OBJECTIVE[objective],
                                    examples=examples,
                                    educational_context=educational_context,
                                    textbook_section=textbook_prompt_text,
                                    format_instructions=parser.get_format_instructions(),
                                    )
    safe_log(f"Prompt prepared (length={len(message)}).")
    try:
        completion = state["conversation"].predict(input=message)
        model_name = state["model_name"]
        safe_log(f"Model completion received (length={len(completion)}).")
        try:
            qa_list = parser.parse(completion)
            qa = qa_list.get_response()
        except Exception:
            fix_parser = OutputFixingParser.from_llm(
                parser=parser,
                llm=ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.7, model_name=model_name),
            )
            qa_list = fix_parser.parse(completion)
            qa = qa_list.get_response()
    except Exception as exc:
        err = friendly_api_error(exc)
        safe_log(f"generate_qa failed: {exc}")
        duration = time.perf_counter() - started_at
        log_activity(
            "generate_qa_failed",
            request,
            {
                "objective": objective,
                "question_type": q_type,
                "model": model_name or DEFAULT_MODEL,
                "error_type": type(exc).__name__,
                "duration_seconds": round(duration, 3),
            },
        )
        return "", state, err, timing_card("Generation", started_at, succeeded=False)

    ## Successfully generated question. 
    # Create a list of question dictionaries
    

    question_list = state['question_list']
    if question_list is None:
        question_list = []
    for i in range(0, len(qa_list.QAs)):
        question_list.append(
            build_question_record(qa_list.QAs[i], objective, q_type, learning_goal, text_name, model_name)
        )
    safe_log(f"Question list updated (rows={len(question_list)}).")
    state['question_list'] = question_list
    state['saved_to_export'] = False
    duration = time.perf_counter() - started_at
    log_activity(
        "generate_qa_completed",
        request,
        {
            "objective": objective,
            "question_type": q_type,
            "model": model_name,
            "textbook_source_types": textbook_metadata.get("source_types", []),
            "textbook_chunks_total": textbook_metadata.get("chunks_total", 0),
            "textbook_chunks_used": textbook_metadata.get("chunks_used", 0),
            "textbook_chunk_strategy": textbook_metadata.get("chunk_strategy"),
            "generated_count": len(getattr(qa_list, "QAs", []) or []),
            "total_rows_in_memory": len(question_list),
            "duration_seconds": round(duration, 3),
        },
    )
    
    # Next I need to find a way to parse options
    return qa, state, "Generated Q&A successfully.", timing_card("Generation", started_at)


def save_question_list(state, request: gr.Request):
    # Marks the in-memory generated questions as ready for browser-side export.
    question_list = state.get('question_list') or []
    safe_log(f"Question list ready check (rows={len(question_list)}).")
    if not question_list:
        state['saved_to_export'] = False
        log_activity("save_for_export_failed", request, {"reason": "empty_memory"})
        return state, "No Q&As in memory. Generate questions first."

    state['saved_to_export'] = True
    log_activity("save_for_export_completed", request, {"rows": len(question_list)})
    return state, f"Saved {len(question_list)} Q&A rows for export."


def export_question_list(state, request: gr.Request):
    if not state.get('saved_to_export'):
        log_activity("export_failed", request, {"reason": "not_saved"})
        return "", "No current export is ready. Click 'Save Q&As to export later' first."

    question_list = state.get('question_list') or []
    if not question_list:
        state['saved_to_export'] = False
        log_activity("export_failed", request, {"reason": "empty_memory"})
        return "", "No Q&As in memory. Generate questions first."

    try:
        output = BytesIO()
        pd.DataFrame(question_list).to_excel(output, index=False)
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
    except Exception as exc:
        safe_log(f"export_question_list failed: {exc}")
        log_activity("export_failed", request, {"error_type": type(exc).__name__})
        return "", f"Export failed: {type(exc).__name__}. Please check terminal logs for details."

    download_link = (
        '<a download="questionbank.xlsx" '
        'href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,'
        f'{encoded}" '
        'style="display:inline-block;padding:0.6em 1em;border:1px solid #ccc;'
        'border-radius:6px;text-decoration:none;">Download questionbank.xlsx</a>'
    )
    log_activity("export_prepared_for_download", request, {"rows": len(question_list)})
    return download_link, "Export ready: click the download link."

    
  
def refine_qa(objective, q_type, rating, liked, to_improve, next, state, text_name, textbook_section, textbook_pdf, question, learning_goal1, options, correct_answer, explanation, model_name, request: gr.Request):
    """
    Refines a question and answer pair based on user feedback.

    This function uses the OpenAI GPT-4 model to refine a previously generated question and answer pair. 
    The type of question, learning objective, user rating, aspects the user liked, aspects to improve, 
    and the next step are used to guide the refinement process.

    Parameters:
    objective (str): The learning objective to base the question on.
    q_type (str): The type of question to refine. Can be 'Open' or other types defined in Q_TYPE.
    rating (int): The user's rating of the original question and answer (1 to 5).
    liked (str): Aspects of the original question and answer that the user liked.
    to_improve (str): Aspects of the original question and answer that need to be improved.
    next (str): The next step in the refinement process.
    state (dict): A dictionary containing the current state of the conversation. 
                  The 'conversation' key should contain an instance of ConversationChain.

    Returns:
    tuple: A tuple containing the refined question and answer (as a string), and the updated state (as a dict).
    """
    started_at = time.perf_counter()
    log_activity(
        "refine_qa_started",
        request,
        {
            "objective": objective,
            "question_type": q_type,
            "rating": rating,
            "next_step": next,
            "text_name": text_name,
            "model": model_name or DEFAULT_MODEL,
            "has_existing_question": bool((question or "").strip()),
            "has_learning_goal": bool((learning_goal1 or "").strip()),
            "has_liked_feedback": bool((liked or "").strip()),
            "has_improvement_feedback": bool((to_improve or "").strip()),
            "has_textbook_section": bool((textbook_section or "").strip()),
            "has_pdf_upload": textbook_pdf is not None,
        },
    )
    state = ensure_model_state(state, model_name)
    
    parser = PydanticOutputParser(pydantic_object=QA_STRUCT[objective])
    safe_log(f"parser: {objective} / {q_type}")
    retrieval_query = "\n".join(
        str(part)
        for part in [objective, q_type, text_name, learning_goal1, next]
        if part
    )
    try:
        textbook_prompt_text, textbook_metadata = build_textbook_context(textbook_section, textbook_pdf, retrieval_query)
    except Exception as exc:
        err = f"Could not read the uploaded PDF: {type(exc).__name__}. Please check that it is a text-based PDF."
        safe_log(f"PDF/textbook preparation failed: {type(exc).__name__}")
        duration = time.perf_counter() - started_at
        log_activity("refine_qa_failed", request, {"error_type": type(exc).__name__, "stage": "textbook_preparation", "duration_seconds": round(duration, 3)})
        return "", state, err, timing_card("Refinement", started_at, succeeded=False)
    if not textbook_prompt_text:
        duration = time.perf_counter() - started_at
        log_activity("refine_qa_failed", request, {"reason": "empty_textbook_input", "stage": "textbook_preparation", "duration_seconds": round(duration, 3)})
        return "", state, "Please enter a textbook section or upload a readable PDF before refining Q&As.", timing_card("Refinement", started_at, succeeded=False)

    ## Check if there is anything in the question. If not, proceed. If so use a new template
    if question == "":
        safe_log("No question provided. Using a new template")
        message = "System: " + SYSTEM_TEMPLATE + "\nHuman: " + \
          REFINE_TEMPLATE.format(learning_goal=learning_goal1,
                                      learning_objective=LEARNING_OBJECTIVE[objective],
                                      q_type=Q_TYPE[q_type],
                                      textbook_section=textbook_prompt_text,
                                      rating=str(rating),
                                      liked=liked,
                                      rating_meaning=RATING_MEANING[rating],
                                      to_improve=to_improve,
                                      next_step=REFINE_NEXT_STEP[next],
                                      format_instructions=parser.get_format_instructions())
    else:
        message = "System: " + SYSTEM_TEMPLATE + "\nHuman: " + \
          REFINE_TEMPLATE_EXISTING.format(learning_goal=learning_goal1,
                                                  learning_objective=LEARNING_OBJECTIVE[objective], 
                                                  q_type = Q_TYPE[q_type],
                                                  textbook_section=textbook_prompt_text,
                                                  question=question,
                                                  options=options,
                                                  correct_answer=correct_answer,
                                                  explanation=explanation,
                                                  next_step=REFINE_NEXT_STEP[next],
                                                  liked=liked,
                                                  to_improve=to_improve,
                                                  rating=rating,
                                                  rating_meaning=RATING_MEANING[rating],
                                                  format_instructions=parser.get_format_instructions(),)
        
        
        
    try:
        completion = state["conversation"].predict(input=message)
        safe_log(f"Model completion received (length={len(completion)}).")
        model_name = state["model_name"]
        try:
            qa_list = parser.parse(completion)
            qa = qa_list.get_response()
        except Exception:
            fix_parser = OutputFixingParser.from_llm(
                parser=parser,
                llm=ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.7, model_name=model_name),
            )
            qa_list = fix_parser.parse(completion)
            qa = qa_list.get_response()
    except Exception as exc:
        err = friendly_api_error(exc)
        safe_log(f"refine_qa failed: {exc}")
        duration = time.perf_counter() - started_at
        log_activity(
            "refine_qa_failed",
            request,
            {
                "objective": objective,
                "question_type": q_type,
                "model": model_name or DEFAULT_MODEL,
                "error_type": type(exc).__name__,
                "duration_seconds": round(duration, 3),
            },
        )
        return "", state, err, timing_card("Refinement", started_at, succeeded=False)
    question_list = state['question_list']
    if question_list is None:
        question_list = []
    for i in range(0, len(qa_list.QAs)):
        question_list.append(
            build_question_record(qa_list.QAs[i], objective, q_type, learning_goal1, text_name, model_name)
        )
    safe_log(f"Question list updated (rows={len(question_list)}).")
    state['question_list'] = question_list
    state['saved_to_export'] = False
    safe_log(f"Refined Q&A prepared (length={len(qa)}).")
    duration = time.perf_counter() - started_at
    log_activity(
        "refine_qa_completed",
        request,
        {
            "objective": objective,
            "question_type": q_type,
            "model": model_name,
            "textbook_source_types": textbook_metadata.get("source_types", []),
            "textbook_chunks_total": textbook_metadata.get("chunks_total", 0),
            "textbook_chunks_used": textbook_metadata.get("chunks_used", 0),
            "textbook_chunk_strategy": textbook_metadata.get("chunk_strategy"),
            "generated_count": len(getattr(qa_list, "QAs", []) or []),
            "total_rows_in_memory": len(question_list),
            "duration_seconds": round(duration, 3),
        },
    )
    
    return qa, state, "Refined Q&A successfully.", timing_card("Refinement", started_at)

# Define the app's interface
with gr.Blocks(theme=gr.themes.Base(text_size="lg"), css=CUSTOM_CSS, js=CUSTOM_JS) as demo:
    state = gr.State(
        {
            "conversation": create_conversation(DEFAULT_MODEL_CHOICE),
            "model_name": DEFAULT_MODEL_CHOICE,
            "question_list": [],
            "saved_to_export": False,
        }
    )
    demo.load(fn=log_page_load, inputs=None, outputs=None)
    gr.Markdown("""# EduGenie: Smart Content Generation for Educators   ✍🏽 🧞‍♂️🧐 
                EduGenie generates a question, an answer, and an explanation based on your specifications, for various learning objectives: 

                **Remembering** - Recall facts and basic concepts; **Understanding** - Comprehend and explain the meaning of ideas or concepts; **Applying** - Use information in \
                new situations and contexts; **Analyzing** - Draw connections and identify patterns among ideas; **Evaluating** - Make and justify judgments using criteria; \
                **Creating** - Generate new ideas, plans, solutions, or products by synthesizing concepts.
                """)
    with gr.Row():
        objective = gr.Radio(["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"], 
                         label="Learning Objective to assess", value=INITIAL_OBJECTIVE, scale=4)
        q_type = gr.Radio([("Multiple Choice", "Multiple"), ("Open", "Open")], label="What type of question?", value="Multiple", scale=2)
        num = gr.Slider(1, 5, value=1, label="How many questions?", step=1, scale=2, interactive=True)
    with gr.Row():
        model_name = gr.Dropdown(
            choices=MODEL_CHOICES,
            value=DEFAULT_MODEL_CHOICE,
            label="OpenAI model",
            info="Used for both initial generation and refinement.",
            interactive=True,
            scale=3,
        )
    with gr.Tab("Enter Textbook Section"):
        with gr.Row():
            textbook_section = gr.Textbox(label="Textbook Section", lines=7)
            # demo_text = gr.Dropdown([1, 2, 3])
            text_name = gr.Dropdown(["Section 1 - Redox", "Section 2- Reduction Potential", "Section 3 - ATP", "Section 4 - Glycolysis", "Section 5 - pKa", "Data Science"], label = "Topic (e.g. Data Science)")
        textbook_pdf = gr.File(
            label="Upload textbook PDF (optional)",
            file_types=[".pdf"],
            type="filepath",
        )
        pdf_status = gr.Markdown()
        btn_generate_text = gr.Button("Generate Q&A based on the textbook section", variant="primary")
    with gr.Tab("Educational Context (optional)"):
        # gr.Markdown("The optional fields below provide EduGenie useful context for generating the questions.")
        with gr.Row():
            
            learning_goal = gr.Textbox(label="The overall goal of the learning")
            qa_purpose = gr.Textbox(label="The purpose of the generated questions")
            #example_questions = gr.Textbox(label="Labeled examples of the questions to be generated")
    
        with gr.Row():
            question_examples = gr.Textbox(label="Examples of the questions to be generated", lines=10)
        btn_generate_context = gr.Button("Generate Q&A based on the textbook section", variant="primary", interactive=True)
        # with gr.Row():
        #     audience = gr.Textbox(label="The audience for the questions")
        #     audience_knowledge = gr.Textbox(label="What should be assumed about the audiences' knowledge?")
        #     other = gr.Textbox(label="What else should be considered?")
    with gr.Tab("Refine Q&A"):
        with gr.Row():
            rating = gr.Slider(1, 5, value=3, label="Overall Rating (1-5, 5 means 'awesome')", step=1, scale=1)
            liked = gr.Textbox(label="What do you like about the question and answer?", lines=2, scale=1)
            to_improve = gr.Textbox(label="How can the Q&A be improved?", lines=2, scale=1)
        
        with gr.Row():
            question = gr.Textbox(label="Question", lines=3)
            learning_goal1 = gr.Textbox(label="Learning Goal", lines=3)
            options = gr.Textbox(label="Options", lines=3)
        with gr.Row():
            correct_answer = gr.Textbox(label="Correct Answer", lines=3)
            explanation = gr.Textbox(label="Explanation", lines=3)
            
        next = gr.Radio(["Revise the Q&A", "Create new Q&A"], 
                            label="What should I do next?", value="Revise the Q&A")
        btn_refine = gr.Button("Process feedback", variant="primary")
        

   
    qa = gr.Textbox(label="Generated Q&A", lines=6, interactive=True)
    status_message = gr.Textbox(label="Status", interactive=False)
    timing_summary = gr.HTML()
    export_file = gr.HTML(label="Exported question bank")
    #qa_list =gr.Textbox(label=" Q&A List", lines=6, interactive=True)
    # rating, feedback_improve, objective1, q_type1, text_name1, question, learning_goal1, options, correct_answer, explanation,textbook
   
    # btn_generate.click(fn=generate_qa, inputs=[objective, learning_goal,question_examples,q_type, textbook_section, num, state, text_name], outputs=[qa, state, qa_list])
    btn_generate_context.click(
        fn=generate_qa,
        inputs=[objective, learning_goal, qa_purpose, question_examples, q_type, textbook_section, textbook_pdf, num, state, text_name, model_name],
        outputs=[qa, state, status_message, timing_summary]
    )
    btn_generate_text.click(
        fn=generate_qa,
        inputs=[objective, learning_goal, qa_purpose, question_examples, q_type, textbook_section, textbook_pdf, num, state, text_name, model_name],
        outputs=[qa, state, status_message, timing_summary]
    )
    #btn_refine.click(fn=refine_qa, inputs=[objective, q_type, rating, to_improve, next, state, text_name, textbook_section, question, learning_goal1, options, correct_answer, explanation], outputs=[qa, state, qa_list])
    btn_refine.click(
        fn=refine_qa,
        inputs=[objective, q_type, rating, liked, to_improve, next, state, text_name, textbook_section, textbook_pdf, question, learning_goal1, options, correct_answer, explanation, model_name],
        outputs=[qa, state, status_message, timing_summary]
    )
    textbook_pdf.upload(fn=inspect_pdf_upload, inputs=[textbook_pdf], outputs=[pdf_status])
    textbook_pdf.clear(fn=lambda: "", inputs=None, outputs=[pdf_status])
    with gr.Row():
        btn_save = gr.Button("Save Q&As to export later", variant="secondary", size="sm", scale=1)
        btn_export = gr.Button("Export Q&As", variant="secondary", size="sm", scale=2)
        # gr.Button("Export Q&As as CSV", variant="secondary")
        btn_clear = gr.Button("Clear Q&As", variant="secondary", size="sm", scale=1)


    btn_save.click(fn=save_question_list, inputs=[state], outputs=[state, status_message])
    btn_export.click(fn=export_question_list, inputs=[state], outputs=[export_file, status_message])
    btn_clear.click(fn=clear_questions, inputs=[state], outputs=[state, qa, export_file, status_message, timing_summary])

    gr.HTML(LEGAL_FOOTER_HTML)

gr.close_all()

web_app = FastAPI()


@web_app.get("/accessibility.html", include_in_schema=False)
@web_app.get("/accessibility", include_in_schema=False)
def accessibility_statement():
    return FileResponse(PROJECT_ROOT / "accessibility.html", media_type="text/html")


web_app = gr.mount_gradio_app(web_app, demo, path="/")


if __name__ == "__main__":
    uvicorn.run(web_app, host="127.0.0.1", port=7860)
