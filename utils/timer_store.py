"""Local JSON storage for timer definitions, independent of widgets and clocks."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from models import MAX_DURATION_SECONDS


DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "timers.json"


class TimerStoreError(Exception):
    """A database could not be read, validated, or safely saved."""


@dataclass(frozen=True)
class TimerRecord:
    timer_id: str
    duration_seconds: int


class TimerStore:
    def __init__(self, path: Path = DEFAULT_DATABASE) -> None:
        self.path = Path(path)

    def load(self) -> list[TimerRecord]:
        try:
            contents = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.save([])
            return []
        except (OSError, UnicodeError) as exc:
            raise TimerStoreError(f"Cannot read {self.path}: {exc}") from exc
        try:
            return self._validate(json.loads(contents))
        except ValueError as exc:
            raise TimerStoreError(f"Invalid timer database {self.path}: {exc}. The file was not changed.") from exc

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
