"""Structured JSON logging with workflow/trace correlation."""
import json, logging, sys, time, uuid
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
workflow_id_var: ContextVar[str] = ContextVar("workflow_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "trace_id": trace_id_var.get(),
            "workflow_id": workflow_id_var.get(),
        }
        for k in ("node", "tool", "status", "latency_ms", "error"):
            if hasattr(record, k):
                payload[k] = getattr(record, k)
        return json.dumps(payload)


def setup_logging(level=logging.INFO):
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [h]
    root.setLevel(level)


def new_trace_id() -> str:
    tid = uuid.uuid4().hex[:12]
    trace_id_var.set(tid)
    return tid
