"""Local JSON storage for timer definitions, independent of widgets and clocks."""

from dataclasses import asdict, dataclass
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from models import MAX_DURATION_SECONDS
from utils.paths import is_bundled, resource_path, user_data_directory


DEFAULT_DATABASE = resource_path("timers.json")


class TimerStoreError(Exception):
    """A database could not be read, validated, or safely saved."""


@dataclass(frozen=True)
class TimerRecord:
    timer_id: str
    duration_seconds: int


class TimerStore:
    def __init__(self, path: Path | None = None) -> None:
        self._legacy_path: Path | None = None
        if path is None and (sys.platform == "win32" or is_bundled()):
            # Both Program Files and /opt may be read-only to the current user.
            try:
                self.path = user_data_directory() / "timers.json"
            except OSError as exc:
                raise TimerStoreError(str(exc)) from exc
            self._legacy_path = DEFAULT_DATABASE
        else:
            self.path = Path(path) if path is not None else DEFAULT_DATABASE

    def load(self) -> list[TimerRecord]:
        source = self.path
        try:
            if not source.exists() and self._legacy_path is not None and self._legacy_path.is_file():
                source = self._legacy_path
            contents = source.read_text(encoding="utf-8")
        except FileNotFoundError:
            try:
                defaults = json.loads(resource_path("defaults/timers.json").read_text(encoding="utf-8"))
                records = self._validate(defaults)
            except (OSError, UnicodeError, ValueError) as exc:
                raise TimerStoreError(f"Cannot load default timers: {exc}") from exc
            self.save(records)
            return records
        except (OSError, UnicodeError) as exc:
            raise TimerStoreError(f"Cannot read {source}: {exc}") from exc
        try:
            records = self._validate(json.loads(contents))
        except ValueError as exc:
            raise TimerStoreError(f"Invalid timer database {source}: {exc}. The file was not changed.") from exc
        if source != self.path:
            # Import once, leaving the original database intact.
            self.save(records)
        return records

    def save(self, timers: list[TimerRecord]) -> None:
        payload = {"version": 1, "timers": [asdict(timer) for timer in timers]}
        try:
            self._validate(payload)
        except ValueError as exc:
            raise TimerStoreError(f"Cannot save {self.path}: {exc}") from exc
        temporary: Path | None = None
        try:
            # Same-directory replacement keeps a failed write from truncating
            # the previous database. Never write to the live file in place.
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=f".{self.path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(payload, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise TimerStoreError(f"Cannot save {self.path}: {exc}. Your change was not applied.") from exc
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    @staticmethod
    def _validate(payload: object) -> list[TimerRecord]:
        if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
            raise ValueError("expected a JSON object with version 1")
        entries = payload.get("timers")
        if not isinstance(entries, list):
            raise ValueError("'timers' must be a list")
        result = []
        identities: set[str] = set()
        for index, entry in enumerate(entries, 1):
            if not isinstance(entry, dict):
                raise ValueError(f"timer {index} must be an object")
            timer_id = entry.get("timer_id")
            duration = entry.get("duration_seconds")
            if not isinstance(timer_id, str) or not timer_id.strip() or timer_id in identities:
                raise ValueError(f"timer {index} needs a unique, non-empty timer_id")
            if type(duration) is not int or not 1 <= duration <= MAX_DURATION_SECONDS:
                raise ValueError(f"timer {index} duration_seconds must be an integer from 1 to {MAX_DURATION_SECONDS}")
            identities.add(timer_id)
            result.append(TimerRecord(timer_id, duration))
        return result
