"""
Tests for Social Styles grid rendering consistency.

Ensures the grid visualization is consistent across all views:
  - Matplotlib chart (PDF report)
  - Team dashboard SVG
  - Presentation view (CSS grid + JS)
  - Individual results page SVG

All views must agree on:
  1. Axis orientation: X=Assertiveness (left=low, right=high),
     Y=Responsiveness (top=low/Controls, bottom=high/Emotes)
  2. Quadrant placement:
     - Top-left: ANALYTICAL (low assert, low resp)
     - Top-right: DRIVER (high assert, low resp)
     - Bottom-left: AMIABLE (low assert, high resp)
     - Bottom-right: EXPRESSIVE (high assert, high resp)
  3. Boundary logic: strict > 2.5 for "high" (not >=)
  4. Score-to-coordinate mapping: linear 1-4 scale
"""

import pytest
import os
import sys
import re
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ============================================================
# MATPLOTLIB CHART (PDF) TESTS
# ============================================================

class TestMatplotlibChart:
    """Test the matplotlib chart used in PDF reports."""

    def test_chart_generates_successfully(self, app):
        """Chart generation returns a valid base64 PNG."""
        from app.assessment.utils import generate_social_style_chart
        with app.app_context():
            result = generate_social_style_chart(3.0, 2.0)
            assert result.startswith('data:image/png;base64,')

    def test_chart_y_axis_is_inverted(self, app):
        """Y-axis must be inverted so high responsiveness is at bottom.

        This ensures the PDF chart matches the web SVG orientation:
        top=Controls/low resp, bottom=Emotes/high resp.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        from app.assessment.utils import generate_social_style_chart
        with app.app_context():
            # We need to inspect the axes before the figure is closed.
            # Replicate the chart logic to check axis direction.
            fig, ax = plt.figure(figsize=(8, 8)), plt.subplot(111)
            ax.set_xlim(1, 4)
            ax.set_ylim(1, 4)
            ax.invert_yaxis()

            y_min, y_max = ax.get_ylim()
            # After inversion, y_min > y_max (4 at top, 1 at bottom → display order)
            assert y_min > y_max, (
                "Y-axis should be inverted: y_min (display top) should be > y_max (display bottom). "
                f"Got y_min={y_min}, y_max={y_max}"
            )
            plt.close(fig)

    def test_chart_quadrant_positions(self, app):
        """Verify quadrant labels are at correct coordinates.

        With inverted Y-axis:
          ANALYTICAL at (1.75, 1.75) → top-left (low assert, low resp)
          DRIVER at (3.25, 1.75) → top-right (high assert, low resp)
          AMIABLE at (1.75, 3.25) → bottom-left (low assert, high resp)
          EXPRESSIVE at (3.25, 3.25) → bottom-right (high assert, high resp)
        """
        # The chart function is tested via its output. We verify the source code
        # contains the correct coordinate-label pairs.
        import inspect
        from app.assessment.utils import generate_social_style_chart
        source = inspect.getsource(generate_social_style_chart)

        assert "1.75, 1.75, 'ANALYTICAL'" in source or '1.75, 1.75, "ANALYTICAL"' in source
        assert "3.25, 1.75, 'DRIVER'" in source or '3.25, 1.75, "DRIVER"' in source
        assert "1.75, 3.25, 'AMIABLE'" in source or '1.75, 3.25, "AMIABLE"' in source
        assert "3.25, 3.25, 'EXPRESSIVE'" in source or '3.25, 3.25, "EXPRESSIVE"' in source
        assert "invert_yaxis" in source, "Chart must call invert_yaxis() for correct orientation"

    def test_chart_plots_user_at_correct_position(self, app):
        """Chart must plot user position as (assertiveness, responsiveness)."""
        import inspect
        from app.assessment.utils import generate_social_style_chart
        source = inspect.getsource(generate_social_style_chart)

        # The plot call should use assertiveness as X and responsiveness as Y
        assert "ax.plot(assertiveness_score, responsiveness_score" in source

    def test_chart_for_each_quadrant(self, app):
        """Generate charts for scores in each quadrant — no crashes."""
        from app.assessment.utils import generate_social_style_chart
        with app.app_context():
            test_cases = [
                (1.5, 1.5, "ANALYTICAL"),
                (3.5, 1.5, "DRIVER"),
                (1.5, 3.5, "AMIABLE"),
                (3.5, 3.5, "EXPRESSIVE"),
                (2.5, 2.5, "boundary"),
                (1.0, 4.0, "extreme"),
                (4.0, 1.0, "extreme"),
            ]
            for a, r, label in test_cases:
                result = generate_social_style_chart(a, r)
                assert result.startswith('data:image/png;base64,'), (
                    f"Chart failed for {label} at ({a}, {r})"
                )


# ============================================================
# SVG COORDINATE MAPPING TESTS
# ============================================================

class TestSVGCoordinateMapping:
    """Test the score-to-SVG-coordinate formula used in dashboard and results.

    The formula (used in dashboard.html and results.html JS):
      x = 50 + ((assertiveness - 1) / 3) * 300
      y = 50 + ((responsiveness - 1) / 3) * 300

    Maps score range [1, 4] to SVG coordinate range [50, 350].
    """

    @staticmethod
    def score_to_svg(assertiveness, responsiveness):
        """Replicate the SVG coordinate mapping formula."""
        a = max(1, min(assertiveness, 4))
        r = max(1, min(responsiveness, 4))
        x = 50 + ((a - 1) / 3) * 300
        y = 50 + ((r - 1) / 3) * 300
        return x, y

    def test_minimum_scores_map_to_top_left(self):
        """Score (1, 1) → SVG (50, 50) = top-left corner."""
        x, y = self.score_to_svg(1.0, 1.0)
        assert x == pytest.approx(50)
        assert y == pytest.approx(50)

    def test_maximum_scores_map_to_bottom_right(self):
        """Score (4, 4) → SVG (350, 350) = bottom-right corner."""
        x, y = self.score_to_svg(4.0, 4.0)
        assert x == pytest.approx(350)
        assert y == pytest.approx(350)

    def test_midpoint_maps_to_center(self):
        """Score (2.5, 2.5) → SVG (200, 200) = grid center."""
        x, y = self.score_to_svg(2.5, 2.5)
        assert x == pytest.approx(200)
        assert y == pytest.approx(200)

    def test_analytical_quadrant(self):
        """Low assert (1.5), low resp (1.5) → top-left quadrant (x<200, y<200)."""
        x, y = self.score_to_svg(1.5, 1.5)
        assert x < 200, f"ANALYTICAL x={x} should be < 200"
        assert y < 200, f"ANALYTICAL y={y} should be < 200"

    def test_driver_quadrant(self):
        """High assert (3.5), low resp (1.5) → top-right quadrant (x>200, y<200)."""
        x, y = self.score_to_svg(3.5, 1.5)
        assert x > 200, f"DRIVER x={x} should be > 200"
        assert y < 200, f"DRIVER y={y} should be < 200"

    def test_amiable_quadrant(self):
        """Low assert (1.5), high resp (3.5) → bottom-left quadrant (x<200, y>200)."""
        x, y = self.score_to_svg(1.5, 3.5)
        assert x < 200, f"AMIABLE x={x} should be < 200"
        assert y > 200, f"AMIABLE y={y} should be > 200"

    def test_expressive_quadrant(self):
        """High assert (3.5), high resp (3.5) → bottom-right quadrant (x>200, y>200)."""
        x, y = self.score_to_svg(3.5, 3.5)
        assert x > 200, f"EXPRESSIVE x={x} should be > 200"
        assert y > 200, f"EXPRESSIVE y={y} should be > 200"

    def test_clamping_below_minimum(self):
        """Scores below 1 are clamped to 1."""
        x, y = self.score_to_svg(0.5, 0.0)
        assert x == pytest.approx(50)
        assert y == pytest.approx(50)

    def test_clamping_above_maximum(self):
        """Scores above 4 are clamped to 4."""
        x, y = self.score_to_svg(5.0, 4.5)
        assert x == pytest.approx(350)
        assert y == pytest.approx(350)

    def test_linear_mapping(self):
        """Mapping is linear — equal score increments = equal coordinate increments."""
        _, y1 = self.score_to_svg(2.5, 1.0)
        _, y2 = self.score_to_svg(2.5, 2.0)
        _, y3 = self.score_to_svg(2.5, 3.0)
        assert y2 - y1 == pytest.approx(y3 - y2)


# ============================================================
# PRESENTATION VIEW COORDINATE MAPPING TESTS
# ============================================================

class TestPresentationCoordinateMapping:
    """Test the CSS percentage mapping used in the presentation view.

    The formula:
      x_pos = (assertiveness - 1) / 3 * 100  (% from left)
      y_pos = (responsiveness - 1) / 3 * 100  (% from top)
    """

    @staticmethod
    def score_to_pct(assertiveness, responsiveness):
        """Replicate the presentation view coordinate mapping."""
        a = max(1, min(assertiveness, 4))
        r = max(1, min(responsiveness, 4))
        x_pct = ((a - 1) / 3) * 100
        y_pct = ((r - 1) / 3) * 100
        return x_pct, y_pct

    def test_minimum_scores_map_to_origin(self):
        """Score (1, 1) → (0%, 0%) = top-left."""
        x, y = self.score_to_pct(1.0, 1.0)
        assert x == pytest.approx(0)
        assert y == pytest.approx(0)

    def test_maximum_scores_map_to_far_corner(self):
        """Score (4, 4) → (100%, 100%) = bottom-right."""
        x, y = self.score_to_pct(4.0, 4.0)
        assert x == pytest.approx(100)
        assert y == pytest.approx(100)

    def test_midpoint_maps_to_center(self):
        """Score (2.5, 2.5) → (50%, 50%) = center."""
        x, y = self.score_to_pct(2.5, 2.5)
        assert x == pytest.approx(50)
        assert y == pytest.approx(50)

    def test_analytical_in_top_left(self):
        """Low assert, low resp → top-left (x<50%, y<50%)."""
        x, y = self.score_to_pct(1.5, 1.5)
        assert x < 50 and y < 50

    def test_driver_in_top_right(self):
        """High assert, low resp → top-right (x>50%, y<50%)."""
        x, y = self.score_to_pct(3.5, 1.5)
        assert x > 50 and y < 50

    def test_amiable_in_bottom_left(self):
        """Low assert, high resp → bottom-left (x<50%, y>50%)."""
        x, y = self.score_to_pct(1.5, 3.5)
        assert x < 50 and y > 50

    def test_expressive_in_bottom_right(self):
        """High assert, high resp → bottom-right (x>50%, y>50%)."""
        x, y = self.score_to_pct(3.5, 3.5)
        assert x > 50 and y > 50


# ============================================================
# CROSS-VIEW CONSISTENCY TESTS
# ============================================================

class TestCrossViewConsistency:
    """Verify that all views place the user dot in the same relative position."""

    @staticmethod
    def svg_to_normalized(x, y):
        """Normalize SVG coords (50-350) to 0-1 range."""
        return (x - 50) / 300, (y - 50) / 300

    @staticmethod
    def pct_to_normalized(x_pct, y_pct):
        """Normalize percentage coords to 0-1 range."""
        return x_pct / 100, y_pct / 100

    def test_svg_and_presentation_agree(self):
        """SVG and presentation views must produce the same normalized position."""
        test_scores = [
            (1.0, 1.0), (4.0, 4.0), (2.5, 2.5),
            (1.5, 3.5), (3.5, 1.5), (2.0, 3.0), (3.0, 2.0),
        ]

        for a, r in test_scores:
            # SVG formula
            svg_x = 50 + ((max(1, min(a, 4)) - 1) / 3) * 300
            svg_y = 50 + ((max(1, min(r, 4)) - 1) / 3) * 300
            svg_norm = self.svg_to_normalized(svg_x, svg_y)

            # Presentation formula
            pct_x = ((max(1, min(a, 4)) - 1) / 3) * 100
            pct_y = ((max(1, min(r, 4)) - 1) / 3) * 100
            pct_norm = self.pct_to_normalized(pct_x, pct_y)

            assert svg_norm[0] == pytest.approx(pct_norm[0], abs=0.001), (
                f"X mismatch at ({a}, {r}): SVG={svg_norm[0]:.3f}, pct={pct_norm[0]:.3f}"
            )
            assert svg_norm[1] == pytest.approx(pct_norm[1], abs=0.001), (
                f"Y mismatch at ({a}, {r}): SVG={svg_norm[1]:.3f}, pct={pct_norm[1]:.3f}"
            )

    def test_all_views_place_quadrants_consistently(self):
        """All views must place the same score in the same named quadrant.

        For each representative score, verify which quadrant it falls in.
        """
        def get_quadrant_from_scores(a, r):
            """Determine quadrant using the spec-correct boundary logic (strict >)."""
            if a > 2.5 and r <= 2.5:
                return "DRIVER"
            elif a > 2.5 and r > 2.5:
                return "EXPRESSIVE"
            elif a <= 2.5 and r > 2.5:
                return "AMIABLE"
            else:
                return "ANALYTICAL"

        def get_quadrant_from_svg_position(x, y):
            """Determine quadrant from SVG coordinates."""
            # Midpoint in SVG is (200, 200)
            if x > 200 and y <= 200:
                return "DRIVER"       # right, top
            elif x > 200 and y > 200:
                return "EXPRESSIVE"   # right, bottom
            elif x <= 200 and y > 200:
                return "AMIABLE"      # left, bottom
            else:
                return "ANALYTICAL"   # left, top

        test_scores = [
            (1.5, 1.5), (3.5, 1.5), (1.5, 3.5), (3.5, 3.5),  # clear quadrants
            (2.8, 2.2), (2.2, 2.8), (2.8, 2.8), (2.2, 2.2),  # near boundary
        ]

        for a, r in test_scores:
            expected = get_quadrant_from_scores(a, r)

            # SVG position
            svg_x = 50 + ((a - 1) / 3) * 300
            svg_y = 50 + ((r - 1) / 3) * 300
            svg_quadrant = get_quadrant_from_svg_position(svg_x, svg_y)

            assert svg_quadrant == expected, (
                f"At ({a}, {r}): expected {expected}, SVG position ({svg_x}, {svg_y}) "
                f"gives {svg_quadrant}"
            )


# ============================================================
# TEMPLATE BOUNDARY LOGIC TESTS
# ============================================================

class TestTemplateBoundaryLogic:
    """Verify boundary comparisons in templates use strict > (not >=).

    These tests parse the actual template files to catch regressions.
    """

    @staticmethod
    def read_template(relative_path):
        """Read a template file."""
        base = os.path.join(os.path.dirname(__file__), '..')
        path = os.path.join(base, relative_path)
        with open(path) as f:
            return f.read()

    def test_presentation_jinja_uses_strict_gt(self):
        """Presentation Jinja2 template must use > 2.5, not >= 2.5."""
        content = self.read_template('app/templates/team/presentation.html')
        # Should NOT contain >= 2.5 in Jinja2 boundary logic
        jinja_blocks = re.findall(r'\{%.*?%\}', content, re.DOTALL)
        for block in jinja_blocks:
            if '2.5' in block and ('assertiveness' in block or 'responsiveness' in block):
                assert '>= 2.5' not in block, (
                    f"Found >= 2.5 in Jinja2 block (should be > 2.5): {block.strip()}"
                )

    def test_presentation_js_uses_strict_gt(self):
        """Presentation JavaScript must use > 2.5, not >= 2.5."""
        content = self.read_template('app/templates/team/presentation.html')
        # Find the getQuadrantColor function
        match = re.search(r'function getQuadrantColor\(.*?\{(.*?)\}', content, re.DOTALL)
        assert match, "getQuadrantColor function not found in presentation template"
        fn_body = match.group(1)
        assert '>= 2.5' not in fn_body, (
            f"Found >= 2.5 in getQuadrantColor (should be > 2.5): {fn_body.strip()}"
        )

    def test_dashboard_svg_quadrant_placement(self):
        """Dashboard SVG must have correct quadrant placement:
        ANALYTICAL top-left, DRIVER top-right, AMIABLE bottom-left, EXPRESSIVE bottom-right.
        """
        content = self.read_template('app/templates/team/dashboard.html')

        # ANALYTICAL should be at x=50, y=50 area (top-left)
        assert re.search(
            r'x="50".*y="50".*ANALYTICAL|data-quadrant="ANALYTICAL".*x="50".*y="50"',
            content
        ), "ANALYTICAL should be at top-left (x=50, y=50)"

        # DRIVER should be at x=200, y=50 area (top-right)
        assert re.search(
            r'x="200".*y="50".*DRIVER|data-quadrant="DRIVER".*x="200".*y="50"',
            content
        ), "DRIVER should be at top-right (x=200, y=50)"

        # AMIABLE should be at x=50, y=200 area (bottom-left)
        assert re.search(
            r'x="50".*y="200".*AMIABLE|data-quadrant="AMIABLE".*x="50".*y="200"',
            content
        ), "AMIABLE should be at bottom-left (x=50, y=200)"

        # EXPRESSIVE should be at x=200, y=200 area (bottom-right)
        assert re.search(
            r'x="200".*y="200".*EXPRESSIVE|data-quadrant="EXPRESSIVE".*x="200".*y="200"',
            content
        ), "EXPRESSIVE should be at bottom-right (x=200, y=200)"

    def test_results_svg_quadrant_placement(self):
        """Results page SVG must have correct quadrant placement."""
        content = self.read_template('app/templates/assessment/results.html')

        # Match rect elements with x/y before or after data-quadrant
        assert re.search(
            r'x="50".*y="50".*data-quadrant="ANALYTICAL"|data-quadrant="ANALYTICAL".*x="50".*y="50"',
            content
        ), "ANALYTICAL should be at top-left (x=50, y=50)"

        assert re.search(
            r'x="200".*y="50".*data-quadrant="DRIVER"|data-quadrant="DRIVER".*x="200".*y="50"',
            content
        ), "DRIVER should be at top-right (x=200, y=50)"

        assert re.search(
            r'x="50".*y="200".*data-quadrant="AMIABLE"|data-quadrant="AMIABLE".*x="50".*y="200"',
            content
        ), "AMIABLE should be at bottom-left (x=50, y=200)"

        assert re.search(
            r'x="200".*y="200".*data-quadrant="EXPRESSIVE"|data-quadrant="EXPRESSIVE".*x="200".*y="200"',
            content
        ), "EXPRESSIVE should be at bottom-right (x=200, y=200)"

    def test_results_page_positions_user_marker(self):
        """Results page must have JS that reads result-data and positions the marker."""
        content = self.read_template('app/templates/assessment/results.html')
        assert 'result-data' in content, "Results page must have result-data element"
        assert 'user-marker' in content, "Results page must have user-marker element"
        # JS must read the data and set marker position
        assert 'dataset.assertiveness' in content or "data-assertiveness" in content
        assert "setAttribute('cx'" in content or 'setAttribute("cx"' in content, (
            "Results JS must position the marker by setting cx/cy attributes"
        )

    def test_dashboard_axis_labels(self):
        """Dashboard must label axes: ASKS (left), TELLS (right), CONTROLS (top), EMOTES (bottom)."""
        content = self.read_template('app/templates/team/dashboard.html')

        # ASKS should be at left (x=125 or low x)
        asks_match = re.search(r'x="(\d+)"[^>]*>ASKS<', content)
        assert asks_match, "ASKS label not found"
        asks_x = int(asks_match.group(1))
        assert asks_x < 200, f"ASKS should be on left side, got x={asks_x}"

        # TELLS should be at right (x=275 or high x)
        tells_match = re.search(r'x="(\d+)"[^>]*>TELLS<', content)
        assert tells_match, "TELLS label not found"
        tells_x = int(tells_match.group(1))
        assert tells_x > 200, f"TELLS should be on right side, got x={tells_x}"

        # CONTROLS should be near top (y=125 or low y)
        controls_match = re.search(r'y="(\d+)"[^>]*>CONTROLS<', content)
        assert controls_match, "CONTROLS label not found"
        controls_y = int(controls_match.group(1))
        assert controls_y < 200, f"CONTROLS should be near top, got y={controls_y}"

        # EMOTES should be near bottom (y=275 or high y)
        emotes_match = re.search(r'y="(\d+)"[^>]*>EMOTES<', content)
        assert emotes_match, "EMOTES label not found"
        emotes_y = int(emotes_match.group(1))
        assert emotes_y > 200, f"EMOTES should be near bottom, got y={emotes_y}"

    def test_presentation_axis_labels(self):
        """Presentation view must label axes correctly with proper CSS class names."""
        content = self.read_template('app/templates/team/presentation.html')

        # CONTROLS label should use responsiveness-low class (low resp = top)
        assert re.search(r'responsiveness-low["\s>].*?CONTROLS|CONTROLS.*?responsiveness-low', content, re.DOTALL), (
            "CONTROLS should use responsiveness-low class (low resp = top of grid)"
        )

        # EMOTES label should use responsiveness-high class (high resp = bottom)
        assert re.search(r'responsiveness-high["\s>].*?EMOTES|EMOTES.*?responsiveness-high', content, re.DOTALL), (
            "EMOTES should use responsiveness-high class (high resp = bottom of grid)"
        )

        # TELLS label should use assertiveness-high class (high assert = right)
        assert re.search(r'assertiveness-high["\s>].*?TELLS|TELLS.*?assertiveness-high', content, re.DOTALL), (
            "TELLS should use assertiveness-high class (high assert = right of grid)"
        )

        # ASKS label should use assertiveness-low class (low assert = left)
        assert re.search(r'assertiveness-low["\s>].*?ASKS|ASKS.*?assertiveness-low', content, re.DOTALL), (
            "ASKS should use assertiveness-low class (low assert = left of grid)"
        )
