"""Application-owned resources and writable data, independent of the launch cwd."""

from pathlib import Path
import sys

from PySide6.QtCore import QStandardPaths


def is_bundled() -> bool:
    return bool(getattr(sys, "frozen", False))


def application_directory() -> Path:
    # The onedir spec keeps normal resource folders beside the executable.
    if is_bundled():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_path(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Resource paths must be relative to the application directory.")
    return application_directory() / path


def user_data_directory() -> Path:
    directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)
    if not directory:
        raise OSError("Cannot find the writable application data directory.")
    return Path(directory) / "ClockIn"


def stylesheet(name: str) -> str:
    return resource_path(f"styles/{name}.qss").read_text(encoding="utf-8")
