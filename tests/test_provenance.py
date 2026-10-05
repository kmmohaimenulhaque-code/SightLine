"""Sample provenance records (DAT-01)."""

import pytest

from ml.datasets import provenance as p

FILES = [{"path": "data/synthetic/x.png", "sha256": "0" * 64, "media_type": "image/png"}]


def test_valid_synthetic_record():
    rec = p.make_record("syn-1", "SYNTHETIC", {"name": "gen", "version": "0.1.0"}, FILES, {"seed": 1})
    assert p.validate_record(rec) == []
    assert rec["licence"] == "SIGHTLINE-internal"


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda r: r.pop("source"), "missing field 'source'"),
        (lambda r: r.update(category="REAL"), "category"),
        (lambda r: r.update(category="DERIVED", parents=[]), "parents"),
        (lambda r: r.update(category="EXTERNAL"), "external licence"),
        (lambda r: r.update(files=[]), "files"),
    ],
)
def test_invalid_records_are_rejected(mutation, message):
    rec = p.make_record("syn-1", "SYNTHETIC", {"name": "gen"}, FILES, {})
    mutation(rec)
    assert any(message in e for e in p.validate_record(rec))


def test_make_record_refuses_invalid():
    with pytest.raises(ValueError):
        p.make_record("x", "NOT_A_CATEGORY", {}, FILES, {})


def test_jsonl_roundtrip_and_hash(tmp_path):
    rec = p.make_record("syn-2", "SYNTHETIC", {"name": "gen"}, FILES, {"a": 1})
    path = tmp_path / "m.jsonl"
    p.write_jsonl([rec], path)
    assert p.read_jsonl(path) == [rec]
    f = tmp_path / "blob.bin"
    f.write_bytes(b"sightline")
    assert p.sha256_file(f) == p.sha256_bytes(b"sightline")
