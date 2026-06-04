# -*- coding: utf-8 -*-
"""
Named PharmRAG workflow steps.

LangGraph is optional at runtime. The application keeps a lightweight step list
for logs/tests and can build a no-op graph when langgraph is installed.
"""

from __future__ import annotations

from typing import Any, TypedDict


WORKFLOW_STEPS = [
    "risk_check",
    "attachment_extract",
    "retrieve",
    "answer",
    "citation_verify",
    "safety_postprocess",
    "log_metrics",
]


class WorkflowState(TypedDict, total=False):
    question: str
    attachments: list[dict[str, Any]]
    answer: str
    risk_flags: list[str]
    sources: list[str]


def build_langgraph_workflow() -> Any:
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    graph = StateGraph(WorkflowState)

    def passthrough(state: WorkflowState) -> WorkflowState:
        return state

    for step in WORKFLOW_STEPS:
        graph.add_node(step, passthrough)

    for current, next_step in zip(WORKFLOW_STEPS, WORKFLOW_STEPS[1:]):
        graph.add_edge(current, next_step)
    graph.add_edge(WORKFLOW_STEPS[-1], END)
    graph.set_entry_point(WORKFLOW_STEPS[0])
    return graph.compile()
