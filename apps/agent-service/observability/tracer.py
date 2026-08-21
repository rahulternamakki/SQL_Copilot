"""
Observability and Telemetry Engine for Governed AI Database Copilot.
Tracks per-node execution latencies, token consumption, and cost calculations across agent workflows.
Supports LangSmith and OpenTelemetry export tags.
"""

import time
import os
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agent-tracer")


class NodeSpan(BaseModel):
    node_name: str
    duration_ms: float
    status: str = "completed"
    details: Optional[str] = None


class TelemetryPayload(BaseModel):
    total_latency_ms: float
    estimated_prompt_tokens: int
    estimated_completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model_name: str
    spans: List[NodeSpan]


class AgentTracer:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model_name = model_name
        # Groq LLaMA 3.3 70B pricing: ~$0.59 per 1M tokens ($0.00000059 / token)
        self.cost_per_token = 0.00000059

    def create_trace(self, node_timings: Dict[str, float], prompt_text: str, output_text: str) -> TelemetryPayload:
        """
        Synthesize execution spans, calculate token counts, and estimate run costs.
        """
        spans: List[NodeSpan] = []
        total_time = 0.0

        for node, duration in node_timings.items():
            spans.append(
                NodeSpan(
                    node_name=node,
                    duration_ms=round(duration, 2),
                    status="completed",
                    details=f"Executed node '{node}'",
                )
            )
            total_time += duration

        # Estimate tokens: ~1 token per 4 characters
        prompt_tokens = max(1, len(prompt_text) // 4)
        completion_tokens = max(1, len(output_text) // 4)
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = round(total_tokens * self.cost_per_token, 6)

        return TelemetryPayload(
            total_latency_ms=round(total_time, 2),
            estimated_prompt_tokens=prompt_tokens,
            estimated_completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost_usd,
            model_name=self.model_name,
            spans=spans,
        )


tracer = AgentTracer()
