"""Single source of truth for Social Styles score -> grid position math.

Every renderer derives marker placement from these functions so the views can
never drift apart again:
  - individual results page SVG (results.html + social_styles_grid.js)
  - team dashboard SVG (team/dashboard.html)
  - presentation CSS grid (team/presentation.html, server + live-poll JS)
  - matplotlib PDF chart (app/assessment/utils.py)

Conventions (see CLAUDE.md "Social Styles Framework Reference"):
  - X axis = Assertiveness: left = low (ASKS), right = high (TELLS)
  - Y axis = Responsiveness: top = low (CONTROLS), bottom = high (EMOTES)
  - Quadrants: Analytical top-left, Driver top-right,
               Amiable bottom-left, Expressive bottom-right
  - Style cutoff: strict ``> 2.5`` midpoint (a score of exactly 2.5 is the LOW
    side of its dimension), matching the scoring.ts reference spec.

The JavaScript mirror lives in app/static/js/social_styles_grid.js and must
stay numerically identical -- tests/test_geometry.py asserts parity.
"""

LO = 1
HI = 4
MIDPOINT = 2.5

# SVG grid (results.html, dashboard.html): viewBox "0 0 400 400", plot area 50-350.
SVG_ORIGIN = 50
SVG_SPAN = 300

QUADRANT_COLORS = {
    "ANALYTICAL": "#1565c0",
    "DRIVER": "#c62828",
    "AMIABLE": "#2e7d32",
    "EXPRESSIVE": "#f57c00",
}


def _clamp_normalize(value, lo, hi):
    return (min(max(value, lo), hi) - lo) / (hi - lo)


def normalize_position(assertiveness, responsiveness, lo=LO, hi=HI):
    """Return ``(nx, ny)`` in 0..1.

    nx: 0 = low assertiveness (ASKS), 1 = high assertiveness (TELLS).
    ny: 0 = low responsiveness (CONTROLS, top),
        1 = high responsiveness (EMOTES, bottom).
    Inputs are clamped to ``[lo, hi]`` first.
    """
    return (
        _clamp_normalize(assertiveness, lo, hi),
        _clamp_normalize(responsiveness, lo, hi),
    )


def svg_position(assertiveness, responsiveness):
    """Marker position in the 400x400 SVG grid (plot area 50-350)."""
    nx, ny = normalize_position(assertiveness, responsiveness)
    return SVG_ORIGIN + nx * SVG_SPAN, SVG_ORIGIN + ny * SVG_SPAN


def percent_position(assertiveness, responsiveness):
    """Marker position as ``(x_pct, y_pct)`` for the percentage-positioned grid."""
    nx, ny = normalize_position(assertiveness, responsiveness)
    return nx * 100, ny * 100


def quadrant(assertiveness, responsiveness, midpoint=MIDPOINT):
    """Return the social-style quadrant name for a pair of scores.

    Uses strict ``>`` against ``midpoint``: a score of exactly ``midpoint`` is
    the LOW side of that dimension.
    """
    high_a = assertiveness > midpoint
    high_r = responsiveness > midpoint
    if high_a and high_r:
        return "EXPRESSIVE"
    if high_a and not high_r:
        return "DRIVER"
    if not high_a and high_r:
        return "AMIABLE"
    return "ANALYTICAL"


def quadrant_color(assertiveness, responsiveness):
    """Hex color for the marker, derived from the scores' quadrant."""
    return QUADRANT_COLORS[quadrant(assertiveness, responsiveness)]


def style_color(style):
    """Hex color for an already-determined style name (e.g. a stored value)."""
    return QUADRANT_COLORS.get(str(style).upper(), "#757575")
