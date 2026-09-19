"""Customer configuration loader. One codebase, many configurations."""
from pathlib import Path
from typing import Any, Dict
from app.core.config import ROOT

CONFIG_PATH = ROOT / "config" / "customers.yaml"
_cache: Dict[str, Any] = {}


def _parse_yaml(path: Path) -> dict:
    """Minimal YAML subset parser so PyYAML is not a hard dependency.
    Falls back to PyYAML when installed."""
    try:
        import yaml
        return yaml.safe_load(path.read_text())
    except ImportError:
        pass
    import ast, re
    out, stack = {}, [(-1, out)]
    for raw in path.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key, _, val = raw.strip().partition(":")
        val = val.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if val == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            if val.startswith(("[", "{")):
                try:
                    val = ast.literal_eval(re.sub(r"(\w[\w\-/ ]*)", r"'\1'", val)
                                           if "'" not in val and '"' not in val else val)
                except Exception:
                    pass
            parent[key] = val
    return out


def load_all() -> dict:
    global _cache
    if not _cache:
        _cache = _parse_yaml(CONFIG_PATH)
    return _cache


def get_customer(customer_key: str = "customer_a") -> dict:
    cfg = load_all()
    if customer_key not in cfg:
        raise KeyError(f"Unknown customer '{customer_key}'. "
                       f"Available: {sorted(cfg)}")
    return cfg[customer_key]


def tool_allowed(customer_key: str, tool: str) -> bool:
    allowed = get_customer(customer_key).get("allowed_tools", [])
    return tool in allowed


def requires_approval(customer_key: str, action: str) -> bool:
    rules = get_customer(customer_key).get("approval_rules", {})
    return action in (rules.get("require_approval_for") or [])
