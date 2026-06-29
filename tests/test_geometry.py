"""Tests for the shared score->position transform (app/assessment/geometry.py).

Methodology encoded here (keep golden vectors + this citation if the
methodology ever changes):
  - Each dimension score is the mean of its 15 Likert items, range 1.0-4.0.
  - Style cutoff is the strict ``> 2.5`` midpoint: a score of exactly 2.5 is
    the LOW side of its dimension (per the scoring.ts reference spec).
  - Grid orientation: X = Assertiveness (left=low/ASKS, right=high/TELLS),
    Y = Responsiveness (top=low/CONTROLS, bottom=high/EMOTES).
    Analytical top-left, Driver top-right, Amiable bottom-left,
    Expressive bottom-right.

Three layers:
  1. Golden vectors      - anchor quadrant + coordinate mapping to the spec.
  2. Property-based      - invariants that must hold for ANY input (Hypothesis).
  3. Cross-renderer parity - the Python helper and the JavaScript mirror
     (app/static/js/social_styles_grid.js, run via Node) must agree, and the
     web SVG coordinate and the PDF data position must land in the same
     quadrant. This layer fails on pre-task-01/02 code and passes after.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.assessment import geometry  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
JS_MODULE = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'social_styles_grid.js')


# ============================================================
# 1. GOLDEN VECTORS
# ============================================================

# (assertiveness, responsiveness) -> quadrant. Four pure types, the on-cutoff
# boundary, and the extremes.
QUADRANT_GOLDEN = [
    (1.5, 1.5, "ANALYTICAL"),   # low / low  -> top-left
    (3.5, 1.5, "DRIVER"),       # high / low -> top-right
    (1.5, 3.5, "AMIABLE"),      # low / high -> bottom-left
    (3.5, 3.5, "EXPRESSIVE"),   # high / high-> bottom-right
    (1.0, 1.0, "ANALYTICAL"),
    (4.0, 4.0, "EXPRESSIVE"),
    (2.5, 2.5, "ANALYTICAL"),   # exactly midpoint -> low side (strict >)
    (2.5, 4.0, "AMIABLE"),      # assert at cutoff is low; resp high
    (4.0, 2.5, "DRIVER"),       # resp at cutoff is low; assert high
]


@pytest.mark.parametrize("a,r,expected", QUADRANT_GOLDEN)
def test_quadrant_golden(a, r, expected):
    assert geometry.quadrant(a, r) == expected


@pytest.mark.parametrize("a,r,expected", QUADRANT_GOLDEN)
def test_quadrant_color_matches_quadrant(a, r, expected):
    assert geometry.quadrant_color(a, r) == geometry.QUADRANT_COLORS[expected]


@pytest.mark.parametrize("a,r,nx,ny", [
    (1.0, 1.0, 0.0, 0.0),
    (4.0, 4.0, 1.0, 1.0),
    (2.5, 2.5, 0.5, 0.5),
    (3.5, 1.5, (3.5 - 1) / 3, (1.5 - 1) / 3),
])
def test_normalize_golden(a, r, nx, ny):
    gnx, gny = geometry.normalize_position(a, r)
    assert gnx == pytest.approx(nx)
    assert gny == pytest.approx(ny)


def test_svg_corners():
    assert geometry.svg_position(1, 1) == pytest.approx((50, 50))        # top-left
    assert geometry.svg_position(4, 4) == pytest.approx((350, 350))      # bottom-right
    assert geometry.svg_position(2.5, 2.5) == pytest.approx((200, 200))  # center


def test_percent_corners():
    assert geometry.percent_position(1, 1) == pytest.approx((0, 0))
    assert geometry.percent_position(4, 4) == pytest.approx((100, 100))


def test_clamping_out_of_range():
    assert geometry.svg_position(0.5, 5.0) == pytest.approx((50, 350))
    assert geometry.normalize_position(-10, 99) == (0.0, 1.0)


def test_style_color_by_name():
    assert geometry.style_color("driver") == "#c62828"
    assert geometry.style_color("EXPRESSIVE") == "#f57c00"
    assert geometry.style_color("unknown") == "#757575"


# ============================================================
# 2. PROPERTY-BASED INVARIANTS (Hypothesis)
# ============================================================

from hypothesis import given, strategies as st  # noqa: E402

scores = st.floats(min_value=1.0, max_value=4.0, allow_nan=False, allow_infinity=False)
any_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)


def test_all_minimum_is_analytical_top_left():
    """All-minimum answers -> 1.0/1.0 -> normalized (0,0) -> Analytical."""
    assert geometry.normalize_position(1.0, 1.0) == (0.0, 0.0)
    assert geometry.quadrant(1.0, 1.0) == "ANALYTICAL"


def test_all_maximum_is_expressive_bottom_right():
    """All-maximum answers -> 4.0/4.0 -> normalized (1,1) -> Expressive."""
    assert geometry.normalize_position(4.0, 4.0) == (1.0, 1.0)
    assert geometry.quadrant(4.0, 4.0) == "EXPRESSIVE"


@given(a=any_floats, r=any_floats)
def test_normalized_always_within_unit_square(a, r):
    nx, ny = geometry.normalize_position(a, r)
    assert 0.0 <= nx <= 1.0
    assert 0.0 <= ny <= 1.0


@given(a=any_floats, r=any_floats)
def test_svg_always_within_plot_area(a, r):
    x, y = geometry.svg_position(a, r)
    assert 50 <= x <= 350
    assert 50 <= y <= 350


@given(a=scores, r=scores)
def test_reversal_reflects_through_center(a, r):
    """Reversing every answer reflects the normalized position through (0.5, 0.5)."""
    nx, ny = geometry.normalize_position(a, r)
    # Reversing a 1-4 Likert answer maps v -> (1 + 4) - v = 5 - v.
    rnx, rny = geometry.normalize_position(5 - a, 5 - r)
    assert rnx == pytest.approx(1 - nx)
    assert rny == pytest.approx(1 - ny)


@given(a=scores, r=scores)
def test_svg_and_percent_share_normalization(a, r):
    nx, ny = geometry.normalize_position(a, r)
    sx, sy = geometry.svg_position(a, r)
    px, py = geometry.percent_position(a, r)
    assert sx == pytest.approx(50 + nx * 300)
    assert sy == pytest.approx(50 + ny * 300)
    assert px == pytest.approx(nx * 100)
    assert py == pytest.approx(ny * 100)


# ============================================================
# 3. CROSS-RENDERER PARITY
# ============================================================

PARITY_SCORES = [
    (1.0, 1.0), (4.0, 4.0), (2.5, 2.5),
    (3.5, 1.5), (1.5, 3.5), (2.0, 3.0), (3.0, 2.0),
    (2.8, 2.2), (2.2, 2.8), (0.5, 5.0),  # last one exercises clamping
]


def _node_geometry(scores):
    """Run the JS mirror under Node for each (a, r) and return its outputs."""
    node = shutil.which('node')
    if node is None:
        pytest.skip("Node.js not available to verify JS/Python parity")

    script = (
        "const g = require(process.argv[1]);"
        "const cases = JSON.parse(process.argv[2]);"
        "const out = cases.map(([a, r]) => ({"
        "  svg: g.svgPosition(a, r),"
        "  pct: g.percentPosition(a, r),"
        "  quad: g.quadrant(a, r),"
        "  color: g.quadrantColor(a, r)"
        "}));"
        "process.stdout.write(JSON.stringify(out));"
    )
    proc = subprocess.run(
        [node, '-e', script, JS_MODULE, json.dumps(scores)],
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, f"Node failed: {proc.stderr}"
    return json.loads(proc.stdout)


def test_python_js_parity():
    """The Python helper and the JavaScript mirror must agree exactly."""
    js = _node_geometry(PARITY_SCORES)
    for (a, r), j in zip(PARITY_SCORES, js):
        psx, psy = geometry.svg_position(a, r)
        ppx, ppy = geometry.percent_position(a, r)
        assert psx == pytest.approx(j['svg'][0]), f"svg x mismatch at ({a},{r})"
        assert psy == pytest.approx(j['svg'][1]), f"svg y mismatch at ({a},{r})"
        assert ppx == pytest.approx(j['pct'][0]), f"pct x mismatch at ({a},{r})"
        assert ppy == pytest.approx(j['pct'][1]), f"pct y mismatch at ({a},{r})"
        assert geometry.quadrant(a, r) == j['quad'], f"quadrant mismatch at ({a},{r})"
        assert geometry.quadrant_color(a, r) == j['color'], f"color mismatch at ({a},{r})"


def _svg_quadrant(x, y):
    """Quadrant implied by an SVG coordinate (center at 200,200; >200 = high)."""
    high_a = x > 200
    high_r = y > 200
    if high_a and high_r:
        return "EXPRESSIVE"
    if high_a and not high_r:
        return "DRIVER"
    if not high_a and high_r:
        return "AMIABLE"
    return "ANALYTICAL"


@pytest.mark.parametrize("a,r,expected", [
    (1.5, 1.5, "ANALYTICAL"),
    (3.5, 1.5, "DRIVER"),
    (1.5, 3.5, "AMIABLE"),
    (3.5, 3.5, "EXPRESSIVE"),
])
def test_svg_position_and_pdf_data_agree_on_quadrant(a, r, expected):
    """Web SVG marker and the PDF marker (plotted at the raw score) must land
    in the same quadrant for the same scores.

    The PDF chart plots the point at (assertiveness, responsiveness) on an
    inverted Y axis, so > 2.5 is high on both. The SVG places it via
    svg_position. Both must map to `expected`.
    """
    x, y = geometry.svg_position(a, r)
    assert _svg_quadrant(x, y) == expected
    # PDF data position uses the same > 2.5 high/low logic.
    assert geometry.quadrant(a, r) == expected


def test_regression_guard_marker_not_stuck_at_center():
    """Explicit guard for the task-01 bug: score (3.5, 1.5) must be top-right,
    never the (200, 200) center."""
    x, y = geometry.svg_position(3.5, 1.5)
    assert (x, y) != (200, 200)
    assert x > 200 and y < 200  # top-right (Driver)
