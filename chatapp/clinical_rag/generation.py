"""Groq generation. The prompts and settings are the ones from query.py; answers are streamed."""

import json
import logging
import os

import requests

from . import config

logger = logging.getLogger(__name__)

CONDENSE_PROMPT = """Given the conversation below and a follow-up question, rewrite the follow-up as a single standalone question that can be understood without the conversation. Keep all medical terms. If the follow-up is already standalone, return it unchanged. Only replace references such as "that" or "the second group" with what they refer to. Do not add facts or conclusions from the Assistant's earlier answers, which may be wrong. Return only the question, nothing else.

Conversation:
{history}

Follow-up question: {question}

Standalone question:"""


class GenerationError(RuntimeError):
    """Something went wrong talking to Groq. The message is safe to show to users."""


def _api_key():
    key = os.getenv("GROQ_API_KEY")
    if not key or key == "YOUR_GROQ_API_KEY_HERE":
        raise GenerationError("GROQ_API_KEY is missing. Add it to the .env file next to manage.py.")
    return key


def _post(payload, stream=False):
    try:
        response = requests.post(
            config.GROQ_URL,
            headers={
                "Authorization": f"Bearer {_api_key()}",
                "Content-Type": "application/json",
            },
            json=payload,
            stream=stream,
            timeout=(10, 120),
        )
    except requests.exceptions.RequestException as exc:
        logger.exception("Could not reach Groq")
        raise GenerationError("Could not reach the language model service. Please try again.") from exc

    if response.status_code >= 400:
        logger.error("Groq returned %s: %s", response.status_code, response.text[:500])
        raise GenerationError(
            f"The language model service returned an error ({response.status_code}). Please try again."
        )
    return response


def build_context(hits):
    return "\n\n".join(f"Document {i + 1}:\n{hit['content']}" for i, hit in enumerate(hits))


def build_messages(question, hits):
    user_prompt = (
        "Context information is below.\n"
        "---------------------\n"
        f"{build_context(hits)}\n"
        "---------------------\n\n"
        f"Question: {question}\nAnswer:"
    )
    return [
        {"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def stream_answer(question, hits):
    """Yield the answer text piece by piece."""
    payload = {
        "model": config.GROQ_MODEL,
        "messages": build_messages(question, hits),
        "temperature": config.TEMPERATURE,
        "stream": True,
    }

    with _post(payload, stream=True) as response:
        response.encoding = "utf-8"
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except ValueError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            text = (choices[0].get("delta") or {}).get("content")
            if text:
                yield text


def _format_history(history, max_chars=500):
    lines = []
    for message in history:
        role = "User" if message["role"] == "user" else "Assistant"
        lines.append(f"{role}: {message['content'][:max_chars]}")
    return "\n".join(lines)


def condense_question(question, history):
    """Rewrite a follow-up as a standalone question. With no history this makes no model call."""
    if not history or not config.CONDENSE_FOLLOW_UPS:
        return question

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [{
            "role": "user",
            "content": CONDENSE_PROMPT.format(history=_format_history(history), question=question),
        }],
        "temperature": config.TEMPERATURE,
    }
    data = _post(payload).json()
    rewritten = (data["choices"][0]["message"].get("content") or "").strip()
    return rewritten or question
