"""OpenTelemetry Distributed Tracing & W3C Span Context Propagation (SEC-0006, Q7)."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.repositories.filestore_repository import FileStoreRepository


class Span:
    """Represents a single OpenTelemetry distributed trace span."""

    # Gemini 3.7 Flash pricing
    INPUT_TOKEN_PRICE_PER_M = 0.10
    OUTPUT_TOKEN_PRICE_PER_M = 0.40

    def __init__(self, tracer: "OpenTelemetryTracer", name: str, trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
        self.tracer = tracer
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.start_time = time.perf_counter()
        self.start_iso = datetime.now(timezone.utc).isoformat()
        self.tags: Dict[str, Any] = {}

    def get_w3c_traceparent(self) -> str:
        """Generate standard W3C traceparent header: 00-{trace_id}-{span_id}-01."""
        return f"00-{self.trace_id}-{self.span_id}-01"

    def set_tag(self, key: str, value: Any) -> "Span":
        """Attach domain-level metadata or attribute tag."""
        self.tags[key] = value
        return self

    def record_tokens(self, input_tokens: int, output_tokens: int) -> "Span":
        """Record token usage and compute FinOps cost attribution."""
        self.tags["gemini.tokens.input"] = input_tokens
        self.tags["gemini.tokens.output"] = output_tokens
        cost = (input_tokens * (self.INPUT_TOKEN_PRICE_PER_M / 1_000_000.0)) + (output_tokens * (self.OUTPUT_TOKEN_PRICE_PER_M / 1_000_000.0))
        self.tags["gemini.cost_usd"] = cost
        return self

    def end(self) -> Dict[str, Any]:
        """Complete span, calculate duration, and persist to Cloud Trace repository."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        span_data = {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_iso,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "tags": self.tags
        }
        self.tracer._record_span(span_data)
        return span_data


class OpenTelemetryTracer:
    """Manages distributed trace contexts and spans."""

    TRACES_FILE = "traces/spans.json"

    def __init__(self, repository: Optional[FileStoreRepository] = None):
        self.repo = repository or FileStoreRepository()

    def start_span(self, name: str, trace_id: Optional[str] = None, parent_span_id: Optional[str] = None) -> Span:
        """Create and start a new distributed trace span."""
        t_id = trace_id or uuid.uuid4().hex
        s_id = uuid.uuid4().hex[:16]
        return Span(tracer=self, name=name, trace_id=t_id, span_id=s_id, parent_span_id=parent_span_id)

    def _record_span(self, span_data: Dict[str, Any]) -> None:
        """Persist trace span to atomic FileStore."""
        self.repo.save_record(self.TRACES_FILE, span_data["span_id"], span_data)
