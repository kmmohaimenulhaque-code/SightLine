"""Sample-level provenance records (DATASET_SPEC.md §2) — creation, hashing and validation.

Deliberately dependency-free (no jsonschema): the validator enforces required fields, the category enumeration and
basic types. ``data/manifests/schema/sample_record.schema.json`` documents the same contract for other tools.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path

CATEGORIES = ("EXTERNAL", "TEAM_COLLECTED", "SYNTHETIC", "DERIVED", "MODEL_OUTPUT", "SIMULATION_OUTPUT")
REQUIRED_FIELDS = ("sample_id", "category", "created_utc", "source", "files", "licence", "parents", "parameters")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo_root: str | Path = ".") -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def make_record(
    sample_id: str,
    category: str,
    source: dict,
    files: list[dict],
    parameters: dict,
    licence: str = "SIGHTLINE-internal",
    parents: list[str] | None = None,
    ground_truth: dict | None = None,
    notes: str | None = None,
    created_utc: str | None = None,
) -> dict:
    rec = {
        "sample_id": sample_id,
        "category": category,
        "created_utc": created_utc or utc_now(),
        "source": source,
        "files": files,
        "licence": licence,
        "parents": list(parents or []),
        "parameters": parameters,
    }
    if ground_truth is not None:
        rec["ground_truth"] = ground_truth
    if notes:
        rec["notes"] = notes
    errors = validate_record(rec)
    if errors:
        raise ValueError("; ".join(errors))
    return rec


def validate_record(rec: dict) -> list[str]:
    errors = [f"missing field '{k}'" for k in REQUIRED_FIELDS if k not in rec]
    if errors:
        return errors
    if rec["category"] not in CATEGORIES:
        errors.append(f"category '{rec['category']}' not in {CATEGORIES}")
    if not isinstance(rec["sample_id"], str) or not rec["sample_id"]:
        errors.append("sample_id must be a non-empty string")
    if not isinstance(rec["files"], list) or not rec["files"]:
        errors.append("files must be a non-empty list")
    else:
        for f in rec["files"]:
            if not isinstance(f, dict) or not {"path", "sha256", "media_type"} <= set(f):
                errors.append("each file needs path, sha256 and media_type")
                break
    if not isinstance(rec["parents"], list):
        errors.append("parents must be a list")
    if rec["category"] == "DERIVED" and not rec.get("parents"):
        errors.append("DERIVED samples must list their parents")
    if rec["category"] == "EXTERNAL" and rec.get("licence") in (None, "", "SIGHTLINE-internal"):
        errors.append("EXTERNAL samples must record the external licence")
    if not isinstance(rec["source"], dict):
        errors.append("source must be an object")
    if not isinstance(rec["parameters"], dict):
        errors.append("parameters must be an object")
    return errors


def write_jsonl(records: list[dict], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
