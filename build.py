"""Build a native onedir distribution, archive, and (on Arch x64) PKGBUILD."""

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent


def main() -> int:
    if sys.platform not in ("win32", "linux"):
        raise SystemExit("Build ClockIn on Windows or Linux, for that same platform.")
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit("Build dependencies missing. Run: uv sync --locked --group build")
    resources = json.loads((ROOT / "packaging/resources.json").read_text(encoding="utf-8"))
    missing = [name for name in resources if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Missing required resources:\n" + "\n".join(missing))
    # Only delete this application's generated output, never the source folders.
    for folder in (ROOT / "build/pyinstaller", ROOT / "dist/ClockIn"):
        if folder.exists():
            shutil.rmtree(folder)
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--workpath", str(ROOT / "build/pyinstaller"),
        "--distpath", str(ROOT / "dist"), str(ROOT / "ClockIn.spec"),
    ], cwd=ROOT, check=True)
    output = ROOT / "dist/ClockIn"
    for name in resources:
        if not (output / name).is_file():
            raise SystemExit(f"Build did not include required resource: {name}")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    target = "windows" if sys.platform == "win32" else "linux"
    machine = platform.machine().lower()
    architecture = {"amd64": "x86_64", "arm64": "aarch64"}.get(machine, machine)
    if sys.platform == "linux":
        shutil.copy2(ROOT / "packaging/arch/clockin.desktop", output)
    archive_name = f"ClockIn-{version}-{target}-{architecture}"
    archive = Path(shutil.make_archive(
        str(ROOT / "dist" / archive_name), "zip" if sys.platform == "win32" else "gztar",
        root_dir=ROOT / "dist", base_dir="ClockIn",
    ))
    if sys.platform == "linux" and architecture == "x86_64":
        package_dir = ROOT / "dist/arch"
        package_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive, package_dir / archive.name)
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        recipe = (ROOT / "packaging/arch/PKGBUILD.in").read_text(encoding="utf-8")
        for key, value in {"VERSION": version, "ARCHIVE": archive.name, "SHA256": digest}.items():
            recipe = recipe.replace(f"@{key}@", value)
        (package_dir / "PKGBUILD").write_text(recipe, encoding="utf-8")
    print(f"Ready to ship: {output}\nArchive: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
