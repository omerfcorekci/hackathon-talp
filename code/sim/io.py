"""External input and per-run append-only output; never generate personas."""

import json
import os
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_personas(path):
    rows = []
    seen = set()
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError(f"Persona input line {number} needs a nonempty string id")
        if not isinstance(row.get("group"), str) or not row["group"]:
            raise ValueError(f"Persona input line {number} needs a group")
        if row["id"] in seen:
            raise ValueError(f"Duplicate persona id on line {number}")
        seen.add(row["id"])
        rows.append(row)
    if not rows:
        raise ValueError("Supply a nonempty external personas.jsonl file")
    return rows


class RunWriter:
    def __init__(self, output):
        self.path = Path(output)
        self.path.mkdir(parents=True, exist_ok=True)
        if any(self.path.iterdir()):
            raise ValueError("Output directory must be empty; use a new directory for each run")

    def _encode(self, value):
        text = json.dumps(value, ensure_ascii=False, allow_nan=False)
        key = os.environ.get("TALP_KEY")
        if key and key in text:
            raise ValueError("Refusing to write data containing TALP_KEY")
        return text

    def append(self, filename, value):
        text = self._encode(value)
        # Called synchronously on one event loop: no await splits a JSONL append.
        with (self.path / filename).open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")

    def write(self, filename, value):
        text = self._encode(value)
        temporary = self.path / (filename + ".tmp")
        temporary.write_text(text + "\n", encoding="utf-8")
        temporary.replace(self.path / filename)

    def copy_personas(self, source):
        data = Path(source).read_bytes()
        key = os.environ.get("TALP_KEY")
        if key and key.encode() in data:
            raise ValueError("Refusing to copy persona input containing TALP_KEY")
        (self.path / "personas.jsonl").write_bytes(data)
