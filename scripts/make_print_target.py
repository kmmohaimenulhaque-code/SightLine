"""Write the printable SIGHTLINE test target as a vector PDF at true scale (A4), with calibration bars.

Run:  python scripts/make_print_target.py [--out docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf]

The geometry is the ISSF 10 m air pistol target as encoded in ``app/scoring/issf.py`` (ring diameters, 59.5 mm black,
0.15 mm lines — the same layout the synthetic generator and the pattern-aware estimator assume). It is an
"ISSF-style" test print, not an official ISSF target: it carries no ring numerals and no manufacturer approval.
Two bars (150 mm and 100 mm) let the operator check the printer's scale in both directions; the black's diameter must
still be measured and entered in every capture manifest.

The PDF is written by hand (no dependency): a page, one content stream, one standard font.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scoring.issf import BLACK_LINE_RADII_MM, BLACK_RADIUS_MM, WHITE_LINE_RADII_MM  # noqa: E402

PRINT_ID = "SL-T1-A4"
PAGE_MM = (210.0, 297.0)
CENTRE_MM = (105.0, 160.0)          # target centre on the page, from the bottom-left corner
CARD_MM = 170.0
LINE_MM = 0.15
PT = 72.0 / 25.4
K = 0.5522847498307936              # Bezier circle constant


def _circle(cx: float, cy: float, r: float) -> str:
    c = K * r
    p = lambda *v: " ".join(f"{x * PT:.4f}" for x in v)
    return (f"{p(cx + r, cy)} m {p(cx + r, cy + c, cx + c, cy + r, cx, cy + r)} c "
            f"{p(cx - c, cy + r, cx - r, cy + c, cx - r, cy)} c {p(cx - r, cy - c, cx - c, cy - r, cx, cy - r)} c "
            f"{p(cx + c, cy - r, cx + r, cy - c, cx + r, cy)} c h")


def _line(x0: float, y0: float, x1: float, y1: float) -> str:
    return f"{x0 * PT:.4f} {y0 * PT:.4f} m {x1 * PT:.4f} {y1 * PT:.4f} l S"


def _text(x: float, y: float, size_pt: float, s: str) -> str:
    s = s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    return f"BT /F1 {size_pt:g} Tf {x * PT:.3f} {y * PT:.3f} Td ({s}) Tj ET"


def content() -> str:
    cx, cy = CENTRE_MM
    half = CARD_MM / 2.0
    ops = ["0 g 0 G", f"{_circle(cx, cy, BLACK_RADIUS_MM)} f", f"{LINE_MM * PT:.4f} w"]
    ops += [f"0 G {_circle(cx, cy, r)} S" for r in BLACK_LINE_RADII_MM]         # rings 6..1: black lines on white
    ops += [f"1 G {_circle(cx, cy, r)} S" for r in WHITE_LINE_RADII_MM]         # rings 8, 9, 10, inner ten: white on black
    ops.append("0.6 G")                                                         # grey corner marks of the 170 mm card
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * half, cy + sy * half
            ops += [_line(x, y, x + sx * 6.0, y), _line(x, y, x, y + sy * 6.0)]
    ops.append(f"0 G {0.25 * PT:.4f} w")                                        # calibration bars with end ticks
    bx0, by = cx - 75.0, 50.0
    ops += [_line(bx0, by, bx0 + 150.0, by), _line(bx0, by - 3, bx0, by + 3), _line(bx0 + 150.0, by - 3, bx0 + 150.0, by + 3)]
    vx, vy0 = 10.0, cy - 50.0
    ops += [_line(vx, vy0, vx, vy0 + 100.0), _line(vx - 3, vy0, vx + 3, vy0), _line(vx - 3, vy0 + 100.0, vx + 3, vy0 + 100.0)]
    ops += ["0 g",
            _text(bx0, by - 7.0, 8, "150.0 mm between the outer ticks (measure and note the value)"),
            _text(vx + 3.0, vy0 + 40.0, 8, "100.0 mm"),
            _text(20.0, 30.0, 8, f"SIGHTLINE test target {PRINT_ID} - ISSF-style geometry, not an official ISSF target."),
            _text(20.0, 26.0, 8, "Print at 100 % (actual size, no fit-to-page). Black disc nominal 59.5 mm: MEASURE it; "
                                 "corner marks = 170 mm card."),
            _text(20.0, 22.0, 8, "For a non-functional training instrument. Camera measurement use only.")]
    return "\n".join(ops) + "\n"


def build_pdf() -> bytes:
    stream = content().encode("latin-1")
    w, h = PAGE_MM[0] * PT, PAGE_MM[1] * PT
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w:.3f} {h:.3f}] /Contents 4 0 R "
            f"/Resources << /Font << /F1 5 0 R >> >> >>".encode(),
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info << /Title (SIGHTLINE test target {PRINT_ID}) >> >>\n".encode()
    out += f"startxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf")
    args = ap.parse_args()
    path = Path(__file__).resolve().parents[1] / args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_pdf())
    print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
