"""Exercise the actual compiler and initialized template, without network access.

Usage: python tests/validate.py /path/to/typst
Requires Poppler's pdfinfo and pdftotext on PATH.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
COMPILER = str(Path(sys.argv[1]).resolve())
RESULTS = []


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def record(name, ok, detail):
    RESULTS.append({"name": name, "passed": bool(ok), "detail": detail})
    if not ok:
        raise AssertionError(f"{name}: {detail}")


def pages(pdf):
    output = run(["pdfinfo", str(pdf)])
    output.check_returncode()
    return int(re.search(r"^Pages:\s+(\d+)", output.stdout, re.M)[1])


with tempfile.TemporaryDirectory(prefix="idraaak-step-cards-") as tmp:
    tmp = Path(tmp)
    package_path = tmp / "packages"
    target = package_path / "preview/idraaak-step-cards/0.1.0"
    target.parent.mkdir(parents=True)
    target.symlink_to(ROOT, target_is_directory=True)
    manifest = tomllib.loads((ROOT / "typst.toml").read_text())
    record("manifest author URL", manifest["package"]["authors"] == ["Idraaak <https://idraaak.com/>"], "clean publisher homepage")
    record("package license", manifest["package"]["license"] == "MIT-0" and (ROOT / "LICENSE").exists(), "MIT-0")

    initialized = tmp / "initialized"
    result = run([COMPILER, "init", "--package-path", str(package_path), "@preview/idraaak-step-cards:0.1.0", str(initialized)])
    record("initialize template", result.returncode == 0, result.stderr.strip())

    def compile_file(name, expected_pages):
        pdf = tmp / (name + ".pdf")
        result = run([COMPILER, "compile", "--package-path", str(package_path), str(initialized / (name + ".typ")), str(pdf)])
        record(name + " compilation", result.returncode == 0 and not result.stderr, result.stderr.strip() or "no diagnostics")
        record(name + " pagination", pages(pdf) == expected_pages, f"expected {expected_pages}, got {pages(pdf)}")
        return pdf

    english = compile_file("main", 1)
    arabic = compile_file("arabic", 1)
    text = run(["pdftotext", str(arabic), "-"]).stdout
    record("Arabic text is selectable", len(re.findall(r"[\u0600-\u06ff]", text)) > 100, "Arabic Unicode text in PDF")

    prelude = '#import "@preview/idraaak-step-cards:0.1.0": step-cards\n'
    cases = [
        ("five-steps", 'steps: range(5).map(i => (title: [Task], instruction: [Keep this text concise.]))', 3),
        ("one-per-page", 'per-page: 1, steps: range(3).map(i => (title: [Task], instruction: [A longer explanation can go here.]))', 3),
        ("arabic-twelve", 'lang: "ar", per-page: 1, steps: range(12).map(i => (title: [خطوة], instruction: [نص تجريبي]))', 12),
        ("letter", 'paper: "us-letter", steps: ((title: [Task], instruction: [A short instruction.]),)', 1),
        ("optional-fields", 'steps: ((title: [Task], instruction: [No image or check is required.]),)', 1),
    ]
    for name, opts, count in cases:
        (initialized / (name + ".typ")).write_text(prelude + '#show: step-cards.with(title: "Validation", ' + opts + ')\n')
        compile_file(name, count)

    failures = [
        ("empty-steps", "steps: ()", "provide at least one step"),
        ("invalid-language", 'lang: "fr", steps: ((title: [T], instruction: [I]),)', "lang must be en or ar"),
        ("invalid-pagination", 'per-page: 3, steps: ((title: [T], instruction: [I]),)', "per-page must be 1 or 2"),
        ("missing-instruction", 'steps: ((title: [T],),)', "each step needs an instruction"),
        ("invalid-step", 'steps: ("bad",)', "each step must be a dictionary"),
    ]
    for name, opts, expected in failures:
        source = initialized / (name + ".typ")
        source.write_text(prelude + '#show: step-cards.with(title: "Validation", ' + opts + ')\n')
        result = run([COMPILER, "compile", "--package-path", str(package_path), str(source), str(tmp / "invalid.pdf")])
        record(name, result.returncode != 0 and expected in result.stderr, expected)

out = ROOT / "validation"
out.mkdir(exist_ok=True)
(out / "results.json").write_text(json.dumps(RESULTS, indent=2))
print(json.dumps({"checks": len(RESULTS), "passed": sum(r["passed"] for r in RESULTS)}, indent=2))
