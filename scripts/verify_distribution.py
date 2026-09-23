"""Run the bundle from an unrelated cwd with no Python/source search paths."""

import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "dist/ClockIn")
    parser.add_argument("--native", action="store_true", help="Use the real desktop instead of offscreen Qt")
    args = parser.parse_args()
    executable_name = "ClockIn.exe" if sys.platform == "win32" else "ClockIn"
    if not (args.bundle / executable_name).is_file():
        raise SystemExit(f"Build first: missing {args.bundle / executable_name}")
    with TemporaryDirectory(prefix="clockin-relocated-") as temporary:
        # Windows may provide an 8.3 TEMP path (RUNNER~1); normalize it just
        # like the application does before comparing resource locations.
        directory = Path(temporary).resolve()
        bundle = directory / "ClockIn"
        shutil.copytree(args.bundle, bundle, symlinks=True)
        executable = bundle / executable_name
        if sys.platform == "win32":
            with executable.open("rb") as stream:
                stream.seek(0x3C)
                pe_offset = struct.unpack("<I", stream.read(4))[0]
                stream.seek(pe_offset + 24 + 68)
                subsystem = struct.unpack("<H", stream.read(2))[0]
            if subsystem != 2:
                raise SystemExit("Windows executable is not a GUI subsystem application")
        environment = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
            environment.pop(key, None)
        if not args.native:
            environment["QT_QPA_PLATFORM"] = "offscreen"
        report = directory / "report.json"
        command = [str(executable), "--smoke-test", str(report)]
        # On Linux also make the source tree physically unavailable and the
        # relocated installation read-only. No writes to the original checkout.
        if sys.platform == "linux" and shutil.which("bwrap"):
            command = ["bwrap", "--die-with-parent", "--bind", "/", "/",
                       "--ro-bind", str(bundle), str(bundle),
                       "--tmpfs", str(ROOT), "--chdir", str(directory), "--", *command]
        run = subprocess.run(command, cwd=directory, env=environment,
                             capture_output=True, text=True, timeout=45)
        if run.returncode or not report.is_file():
            raise SystemExit(f"Bundle smoke test failed ({run.returncode}):\n{run.stdout}\n{run.stderr}")
        evidence = json.loads(report.read_text(encoding="utf-8"))
        if not evidence["passed"] or Path(evidence["resource_root"]) != bundle:
            raise SystemExit(json.dumps(evidence, indent=2))
        output = ROOT / "build/verification"
        output.mkdir(parents=True, exist_ok=True)
        evidence["source_hidden"] = command[0] == "bwrap"
        evidence["native"] = args.native
        evidence["stderr"] = run.stderr
        (output / "bundle-smoke.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"Relocated bundle passed {len(evidence['checks'])} checks; source hidden: {evidence['source_hidden']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
