"""Printable target: true-scale geometry taken from the scoring constants, deterministic output."""

import importlib.util
import re
from pathlib import Path

from app.scoring.issf import BLACK_RADIUS_MM

spec = importlib.util.spec_from_file_location("make_print_target", Path("scripts/make_print_target.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_pdf_is_deterministic_and_well_formed():
    a, b = mod.build_pdf(), mod.build_pdf()
    assert a == b and a.startswith(b"%PDF-1.4") and a.rstrip().endswith(b"%%EOF")
    xref = int(re.search(rb"startxref\n(\d+)", a).group(1))
    assert a[xref:xref + 4] == b"xref"
    assert b"/MediaBox [0 0 595.276 841.890]" in a                       # A4 in points


def test_black_disc_and_bars_are_drawn_at_true_scale():
    c = mod.content()
    pt = 72.0 / 25.4
    cx, cy = mod.CENTRE_MM
    assert f"{(cx + BLACK_RADIUS_MM) * pt:.4f} {cy * pt:.4f} m" in c    # rightmost point of the 59.5 mm black
    assert c.count(" c h") == 1 + 6 + 4                                  # black, rings 6-1, rings 8/9/10 + inner ten
    assert f"{(cx - 75.0) * pt:.4f} {50.0 * pt:.4f} m {(cx + 75.0) * pt:.4f} {50.0 * pt:.4f} l S" in c   # 150 mm bar
    assert "not an official ISSF target" in c
    committed = Path("docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf")
    assert committed.read_bytes() == mod.build_pdf()                     # the committed file is the generator's output
