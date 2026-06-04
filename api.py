# -*- coding: utf-8 -*-
"""
FastAPI backend for PharmRAG.

The Streamlit UI remains the default demo surface. This API exposes the same
agent flow for engineering demos and integration tests.
"""

from __future__ import annotations

import re
import time
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from agents.medical_agent import create_agent
from config import (
    APP_CONFIG,
    DEFAULT_PROVIDER,
    EMBEDDING_PROVIDER,
    MEDICAL_KNOWLEDGE_DIR,
    PERSONAL_KNOWLEDGE_DIR,
    get_api_key_for_provider,
)
from rag.attachments import (
    AttachmentContext,
    build_personal_knowledge_attachment_summary,
    parse_attachment_bytes,
)
from rag.knowledge_manager import write_text_knowledge, write_uploaded_knowledge, write_url_knowledge


app = FastAPI(title="PharmRAG API", version="0.2.0")

_AGENT_CACHE: dict[tuple[str, str, str, str], Any] = {}


def _knowledge_dir(store: str) -> str:
    if store == "personal":
        return PERSONAL_KNOWLEDGE_DIR
    if store == "medical":
        return MEDICAL_KNOWLEDGE_DIR
    raise HTTPException(status_code=400, detail="store must be 'medical' or 'personal'")


def _get_agent(
    provider: str,
    api_key: str,
    embedding_provider: str,
    embedding_api_key: str,
) -> Any:
    resolved_api_key = api_key or get_api_key_for_provider(provider)
    if not resolved_api_key:
        raise HTTPException(status_code=400, detail=f"Missing API key for provider: {provider}")

    resolved_embedding_key = embedding_api_key
    if embedding_provider != "none" and not resolved_embedding_key:
        if embedding_provider == provider:
            resolved_embedding_key = resolved_api_key
        else:
            resolved_embedding_key = get_api_key_for_provider(embedding_provider, for_embedding=True)

    cache_key = (provider, resolved_api_key, embedding_provider, resolved_embedding_key)
    if cache_key not in _AGENT_CACHE:
        _AGENT_CACHE[cache_key] = create_agent(
            provider,
            resolved_api_key,
            embedding_provider,
            resolved_embedding_key,
        )
    return _AGENT_CACHE[cache_key]


def _extract_sources(answer: str) -> list[str]:
    match = re.search(r"(?ms)^参考来源[:：]\s*(.*)$", answer)
    if not match:
        return []
    lines = [line.strip("- ").strip() for line in match.group(1).splitlines()]
    return [line for line in lines if line]


async def _parse_uploads(
    files: list[UploadFile],
    *,
    question: str,
    agent: Any,
) -> list[AttachmentContext]:
    contexts: list[AttachmentContext] = []
    for file in files:
        data = await file.read()
        contexts.append(
            parse_attachment_bytes(
                file.filename or "attachment",
                data,
                content_type=file.content_type or "",
                question=question,
                vision_summarizer=agent.summarize_image_attachment if APP_CONFIG["vision_enabled"] else None,
            )
        )
    return contexts


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "default_provider": DEFAULT_PROVIDER,
        "default_embedding_provider": EMBEDDING_PROVIDER,
        "vision_enabled": APP_CONFIG["vision_enabled"],
        "vision_model": APP_CONFIG["vision_model"],
    }


@app.post("/chat")
async def chat(
    message: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    medical_knowledge_enabled: bool = Form(True),
    personal_knowledge_enabled: bool = Form(False),
    save_to_personal_knowledge: bool = Form(False),
    provider: str = Form(DEFAULT_PROVIDER),
    api_key: str = Form(""),
    embedding_provider: str = Form(EMBEDDING_PROVIDER),
    embedding_api_key: str = Form(""),
) -> dict[str, object]:
    started_at = time.perf_counter()
    agent = _get_agent(provider, api_key, embedding_provider, embedding_api_key)
    agent.set_knowledge_enabled(medical_knowledge_enabled, personal_knowledge_enabled)
    attachments = await _parse_uploads(files, question=message, agent=agent)

    if save_to_personal_knowledge:
        write_text_knowledge(
            "单次提问个人资料",
            build_personal_knowledge_attachment_summary(message, attachments),
            knowledge_dir=PERSONAL_KNOWLEDGE_DIR,
        )
        agent.init_retriever()
        agent.set_knowledge_enabled(medical_knowledge_enabled, personal_knowledge_enabled)

    answer = agent.chat(message, attachments=attachments)
    return {
        "answer": answer,
        "sources": _extract_sources(answer),
        "attachment_reports": [item.public_report() for item in attachments],
        "risk_flags": agent._assess_medical_risk(message, attachments)["flags"],
        "provider": agent.provider,
        "model": agent.provider_config["model"],
        "metrics": {
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "medical_knowledge_enabled": medical_knowledge_enabled,
            "personal_knowledge_enabled": personal_knowledge_enabled,
        },
    }


@app.post("/knowledge/upload")
async def upload_knowledge(
    store: str = Form("medical"),
    files: list[UploadFile] = File(...),
) -> dict[str, object]:
    knowledge_dir = _knowledge_dir(store)
    saved: list[str] = []
    errors: list[str] = []
    for file in files:
        try:
            path = write_uploaded_knowledge(
                file.filename or "upload",
                await file.read(),
                knowledge_dir=knowledge_dir,
            )
            saved.append(str(path))
        except Exception as exc:
            errors.append(f"{file.filename}: {exc}")
    return {"saved": saved, "errors": errors}


@app.post("/knowledge/url")
def import_url_knowledge(
    urls: str = Form(...),
    title: str = Form(""),
    store: str = Form("medical"),
) -> dict[str, object]:
    saved, errors = write_url_knowledge(urls, title, knowledge_dir=_knowledge_dir(store))
    return {"saved": [str(path) for path in saved], "errors": errors}


@app.post("/eval/retrieval")
def eval_retrieval(
    query: str = Form(...),
    provider: str = Form(DEFAULT_PROVIDER),
    api_key: str = Form(""),
    embedding_provider: str = Form(EMBEDDING_PROVIDER),
    embedding_api_key: str = Form(""),
    medical_knowledge_enabled: bool = Form(True),
    personal_knowledge_enabled: bool = Form(False),
) -> dict[str, object]:
    agent = _get_agent(provider, api_key, embedding_provider, embedding_api_key)
    agent.set_knowledge_enabled(medical_knowledge_enabled, personal_knowledge_enabled)
    context, docs = agent._retrieve_context(query)
    return {
        "query": query,
        "context_preview": context[:1200],
        "documents": [
            {
                "source": str(doc.metadata.get("source", "")),
                "knowledge_base": str(doc.metadata.get("knowledge_base", "")),
                "excerpt": str(doc.metadata.get("excerpt", "")),
            }
            for doc in docs
        ],
    }
