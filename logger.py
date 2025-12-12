from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import threading
from typing import Any, Callable, Optional

from config import LOG_DIR, APP_NAME, APP_VERSION

LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class LogPaths:
    text: Path
    jsonl: Path


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


class Logger:
    def __init__(self) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.paths = LogPaths(
            text=LOG_DIR / f"maintenance_{stamp}.log",
            jsonl=LOG_DIR / f"maintenance_{stamp}.jsonl",
        )
        self._lock = threading.Lock()
        self._ui_sink: Optional[Callable[[str], None]] = None

        # Header
        self.info(f"{APP_NAME} v{APP_VERSION} started")
        self.info(f"Text log: {self.paths.text}")
        self.info(f"JSON log: {self.paths.jsonl}")

    def attach_ui_sink(self, sink: Callable[[str], None]) -> None:
        self._ui_sink = sink

    def _write(self, line: str) -> None:
        with self._lock:
            try:
                self.paths.text.parent.mkdir(parents=True, exist_ok=True)
                with open(self.paths.text, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    def _write_json(self, obj: dict[str, Any]) -> None:
        with self._lock:
            try:
                with open(self.paths.jsonl, "a", encoding="utf-8") as f:
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def _emit(self, level: str, message: str, **data: Any) -> None:
        line = message
        if self._ui_sink:
            try:
                self._ui_sink(line)
            except Exception:
                pass

        self._write(line)
        self._write_json({
            "ts": _utc_ts(),
            "level": level,
            "message": message,
            "data": data or {},
        })

    def info(self, message: str, **data: Any) -> None:
        self._emit("INFO", message, **data)

    def warn(self, message: str, **data: Any) -> None:
        self._emit("WARN", message, **data)

    def error(self, message: str, **data: Any) -> None:
        self._emit("ERROR", message, **data)
