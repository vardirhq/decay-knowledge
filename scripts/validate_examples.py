#!/usr/bin/env python3
"""Compile explicitly annotated Decay examples with the upstream checker."""

import argparse, re, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(
    r"```decay\s+(compile|fail)(?:\s+diagnostic=([\w-]+))?\n(.*?)```", re.S
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-dir", type=Path, required=True)
    args = ap.parse_args()
    examples = []
    for path in sorted((ROOT / "content").rglob("*.md")):
        text = path.read_text()
        for number, match in enumerate(FENCE.finditer(text), 1):
            examples.append((path, number, *match.groups()))
        unmarked = re.findall(r"```decay(?:\n|\s+(?!compile|fail))", text)
        if unmarked:
            raise SystemExit(f"{path}: Decay fence missing compile/fail expectation")
    if not examples:
        raise SystemExit("no Decay examples found")
    with tempfile.TemporaryDirectory() as tmp:
        for path, number, expect, diagnostic, source in examples:
            sample = Path(tmp) / f"example-{number}.decay"
            sample.write_text(source)
            result = subprocess.run(
                [
                    "cargo",
                    "run",
                    "--quiet",
                    "--package",
                    "decay-lsp",
                    "--",
                    "--check",
                    str(sample),
                ],
                cwd=args.engine_dir,
                text=True,
                capture_output=True,
            )
            failed = result.returncode != 0
            if (expect == "compile" and failed) or (expect == "fail" and not failed):
                print(result.stdout, result.stderr)
                raise SystemExit(f"{path} example {number}: expected {expect}")
            if diagnostic and diagnostic not in result.stdout + result.stderr:
                raise SystemExit(
                    f"{path} example {number}: missing diagnostic {diagnostic}"
                )
            print(f"ok {path.relative_to(ROOT)}:{number} ({expect})")


if __name__ == "__main__":
    main()
