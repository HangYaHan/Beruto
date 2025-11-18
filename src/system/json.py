from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .log import get_logger

logger = get_logger(__name__)


def read_json(path: str | Path, default: Optional[Any] = None) -> Any:
	"""Read JSON file from `path` and return the parsed object.

	On failure (file missing or parse error) this function logs the problem and
	returns `default`.
	"""
	p = Path(path)
	if not p.exists():
		logger.debug("read_json: file does not exist: %s", p)
		return default
	try:
		with p.open('r', encoding='utf-8') as f:
			return json.load(f)
	except Exception as e:
		logger.exception("Failed to read/parse JSON from %s: %s", p, e)
		return default


def write_json(path: str | Path, data: Any, *, indent: int = 2, ensure_ascii: bool = False) -> None:
	"""Write `data` as JSON to `path`.

	Creates parent directories as needed. On error this function logs the
	exception and re-raises it so callers can decide how to proceed.
	"""
	p = Path(path)
	p.parent.mkdir(parents=True, exist_ok=True)
	try:
		with p.open('w', encoding='utf-8') as f:
			json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
		logger.info("Wrote JSON to %s", p)
	except Exception as e:
		logger.exception("Failed to write JSON to %s: %s", p, e)
		raise


def safe_loads(s: str, default: Optional[Any] = None) -> Any:
	"""Safely parse a JSON string and return the object or `default` on error."""
	try:
		return json.loads(s)
	except Exception as e:
		logger.debug("safe_loads parse error: %s", e)
		return default


def safe_dumps(obj: Any, *, indent: int = 2, ensure_ascii: bool = False) -> str:
	"""Return a JSON string for `obj`. Raises on serialization errors."""
	return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)

