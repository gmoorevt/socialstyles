"""
Tests for Social Styles Assessment scoring logic.

These tests validate the scoring algorithm against the specification
defined in resources/scoring.ts and resources/SOCIAL_STYLES_APP_PRD.md.

Key spec rules:
- Assertiveness: average of questions 1-15 (1-4 scale)
- Responsiveness: average of questions 16-30 (1-4 scale)
- Style determination uses 2.5 midpoint:
    - DRIVER:     assertiveness > 2.5, responsiveness <= 2.5
    - EXPRESSIVE: assertiveness > 2.5, responsiveness > 2.5
    - AMIABLE:    assertiveness <= 2.5, responsiveness > 2.5
    - ANALYTICAL: assertiveness <= 2.5, responsiveness <= 2.5
  (Per scoring.ts: strict '>' for the high side, not '>=')
"""

import pytest
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.assessment import Assessment, AssessmentResult


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def result(app):
    """Create an AssessmentResult instance for testing."""
    with app.app_context():
        r = AssessmentResult(user_id=1, assessment_id=1)
        return r


def make_responses(assertiveness_values, responsiveness_values):
    """Build a responses dict from two lists of 15 values each.

    Keys 1-15 are assertiveness, 16-30 are responsiveness.
    """
    responses = {}
    for i, val in enumerate(assertiveness_values, start=1):
        responses[str(i)] = val
    for i, val in enumerate(responsiveness_values, start=16):
        responses[str(i)] = val
    return responses


# ============================================================
# SCORE CALCULATION TESTS
# ============================================================

class TestScoreCalculation:
    """Test that calculate_scores() computes correct averages."""

    def test_all_ones(self, result):
        """All minimum responses should give scores of 1.0."""
        result.set_responses(make_responses([1]*15, [1]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(1.0)
        assert r == pytest.approx(1.0)

    def test_all_fours(self, result):
        """All maximum responses should give scores of 4.0."""
        result.set_responses(make_responses([4]*15, [4]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(4.0)
        assert r == pytest.approx(4.0)

    def test_all_twos(self, result):
        """All 2s should give scores of 2.0."""
        result.set_responses(make_responses([2]*15, [2]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(2.0)
        assert r == pytest.approx(2.0)

    def test_all_threes(self, result):
        """All 3s should give scores of 3.0."""
        result.set_responses(make_responses([3]*15, [3]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(3.0)
        assert r == pytest.approx(3.0)

    def test_mixed_assertiveness(self, result):
        """Mixed assertiveness with known average."""
        # 8 threes + 7 fours = 24 + 28 = 52, avg = 52/15 = 3.4667
        result.set_responses(make_responses([3]*8 + [4]*7, [2]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(52/15, abs=0.01)

    def test_mixed_responsiveness(self, result):
        """Mixed responsiveness with known average."""
        # 10 ones + 5 threes = 10 + 15 = 25, avg = 25/15 = 1.6667
        result.set_responses(make_responses([2]*15, [1]*10 + [3]*5))
        a, r = result.calculate_scores()
        assert r == pytest.approx(25/15, abs=0.01)

    def test_asymmetric_scores(self, result):
        """High assertiveness, low responsiveness."""
        result.set_responses(make_responses([4]*15, [1]*15))
        a, r = result.calculate_scores()
        assert a == pytest.approx(4.0)
        assert r == pytest.approx(1.0)

    def test_precise_calculation(self, result):
        """Verify exact arithmetic for a specific response set."""
        assert_vals = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3]
        resp_vals = [4, 3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4, 3, 2]
        result.set_responses(make_responses(assert_vals, resp_vals))
        a, r = result.calculate_scores()
        assert a == pytest.approx(sum(assert_vals) / 15, abs=0.001)
        assert r == pytest.approx(sum(resp_vals) / 15, abs=0.001)

    def test_scores_in_valid_range(self, result):
        """Scores must always be between 1.0 and 4.0."""
        import random
        random.seed(42)
        for _ in range(20):
            a_vals = [random.randint(1, 4) for _ in range(15)]
            r_vals = [random.randint(1, 4) for _ in range(15)]
            result.set_responses(make_responses(a_vals, r_vals))
            a, r = result.calculate_scores()
            assert 1.0 <= a <= 4.0, f"Assertiveness {a} out of range"
            assert 1.0 <= r <= 4.0, f"Responsiveness {r} out of range"

    def test_missing_response_defaults_to_zero(self, result):
        """Missing responses should default to 0 (current behavior)."""
        # Only provide assertiveness responses, no responsiveness
        responses = {str(i): 3 for i in range(1, 16)}
        result.set_responses(responses)
        a, r = result.calculate_scores()
        assert a == pytest.approx(3.0)
        assert r == pytest.approx(0.0)  # Missing responses = 0


# ============================================================
# STYLE DETERMINATION TESTS
# ============================================================

class TestStyleDetermination:
    """Test that determine_social_style() maps scores to correct quadrants.

    Per the spec (scoring.ts:171-178), the midpoint is 2.5 and the
    determination uses strict '>' (not '>='):
        assertiveness > 2.5 AND responsiveness > 2.5 → EXPRESSIVE
        assertiveness > 2.5 AND responsiveness <= 2.5 → DRIVER
        assertiveness <= 2.5 AND responsiveness > 2.5 → AMIABLE
        assertiveness <= 2.5 AND responsiveness <= 2.5 → ANALYTICAL
    """

    def test_clear_analytical(self, result):
        """Low assertiveness, low responsiveness → ANALYTICAL."""
        result.assertiveness_score = 1.5
        result.responsiveness_score = 1.5
        assert result.determine_social_style() == "ANALYTICAL"

    def test_clear_driver(self, result):
        """High assertiveness, low responsiveness → DRIVER."""
        result.assertiveness_score = 3.5
        result.responsiveness_score = 1.5
        assert result.determine_social_style() == "DRIVER"

    def test_clear_amiable(self, result):
        """Low assertiveness, high responsiveness → AMIABLE."""
        result.assertiveness_score = 1.5
        result.responsiveness_score = 3.5
        assert result.determine_social_style() == "AMIABLE"

    def test_clear_expressive(self, result):
        """High assertiveness, high responsiveness → EXPRESSIVE."""
        result.assertiveness_score = 3.5
        result.responsiveness_score = 3.5
        assert result.determine_social_style() == "EXPRESSIVE"

    # --- Boundary tests at exactly 2.5 ---
    # Per spec (scoring.ts:173): uses strict '>' not '>='
    # So exactly 2.5 should be treated as the LOW side

    def test_boundary_both_at_midpoint(self, result):
        """Both scores exactly at 2.5 → ANALYTICAL per spec (strict >).

        The spec uses strict '>' for the high side, meaning 2.5 is NOT
        considered high assertiveness or high responsiveness.
        BUG: Current code uses >= which would return EXPRESSIVE.
        """
        result.assertiveness_score = 2.5
        result.responsiveness_score = 2.5
        style = result.determine_social_style()
        # Per spec: both at 2.5 means neither is "high", so ANALYTICAL
        assert style == "ANALYTICAL", (
            f"Expected ANALYTICAL at (2.5, 2.5) per spec (strict > midpoint), "
            f"got {style}. Current code uses >= which incorrectly yields EXPRESSIVE."
        )

    def test_boundary_assert_at_midpoint_resp_low(self, result):
        """Assertiveness exactly 2.5, responsiveness low → ANALYTICAL per spec.

        BUG: Current code uses >= which would return DRIVER.
        """
        result.assertiveness_score = 2.5
        result.responsiveness_score = 1.5
        style = result.determine_social_style()
        assert style == "ANALYTICAL", (
            f"Expected ANALYTICAL at (2.5, 1.5) per spec, got {style}. "
            f"Current code uses >= which incorrectly yields DRIVER."
        )

    def test_boundary_assert_at_midpoint_resp_high(self, result):
        """Assertiveness exactly 2.5, responsiveness high → AMIABLE per spec.

        BUG: Current code uses >= which would return EXPRESSIVE.
        """
        result.assertiveness_score = 2.5
        result.responsiveness_score = 3.5
        style = result.determine_social_style()
        assert style == "AMIABLE", (
            f"Expected AMIABLE at (2.5, 3.5) per spec, got {style}. "
            f"Current code uses >= which incorrectly yields EXPRESSIVE."
        )

    def test_boundary_assert_high_resp_at_midpoint(self, result):
        """Assertiveness high, responsiveness exactly 2.5 → DRIVER per spec.

        BUG: Current code uses < for resp which would return DRIVER (correct),
        but >= for assert (inconsistent with spec).
        """
        result.assertiveness_score = 3.5
        result.responsiveness_score = 2.5
        style = result.determine_social_style()
        assert style == "DRIVER", (
            f"Expected DRIVER at (3.5, 2.5) per spec, got {style}."
        )

    def test_boundary_assert_low_resp_at_midpoint(self, result):
        """Assertiveness low, responsiveness exactly 2.5 → ANALYTICAL per spec.

        BUG: Current code has resp >= 2.5 → AMIABLE, but spec says > 2.5.
        """
        result.assertiveness_score = 1.5
        result.responsiveness_score = 2.5
        style = result.determine_social_style()
        assert style == "ANALYTICAL", (
            f"Expected ANALYTICAL at (1.5, 2.5) per spec (strict > for resp), "
            f"got {style}. Current code uses >= which incorrectly yields AMIABLE."
        )

    # --- Just above/below boundary ---

    def test_just_above_midpoint_both(self, result):
        """Both scores just above 2.5 → EXPRESSIVE."""
        result.assertiveness_score = 2.51
        result.responsiveness_score = 2.51
        assert result.determine_social_style() == "EXPRESSIVE"

    def test_just_below_midpoint_both(self, result):
        """Both scores just below 2.5 → ANALYTICAL."""
        result.assertiveness_score = 2.49
        result.responsiveness_score = 2.49
        assert result.determine_social_style() == "ANALYTICAL"

    def test_just_above_assert_just_below_resp(self, result):
        """Assert just above 2.5, resp just below → DRIVER."""
        result.assertiveness_score = 2.51
        result.responsiveness_score = 2.49
        assert result.determine_social_style() == "DRIVER"

    def test_just_below_assert_just_above_resp(self, result):
        """Assert just below 2.5, resp just above → AMIABLE."""
        result.assertiveness_score = 2.49
        result.responsiveness_score = 2.51
        assert result.determine_social_style() == "AMIABLE"

    # --- Extreme values ---

    def test_minimum_scores(self, result):
        """Both at minimum (1.0) → ANALYTICAL."""
        result.assertiveness_score = 1.0
        result.responsiveness_score = 1.0
        assert result.determine_social_style() == "ANALYTICAL"

    def test_maximum_scores(self, result):
        """Both at maximum (4.0) → EXPRESSIVE."""
        result.assertiveness_score = 4.0
        result.responsiveness_score = 4.0
        assert result.determine_social_style() == "EXPRESSIVE"

    def test_max_assert_min_resp(self, result):
        """Max assertiveness, min responsiveness → DRIVER."""
        result.assertiveness_score = 4.0
        result.responsiveness_score = 1.0
        assert result.determine_social_style() == "DRIVER"

    def test_min_assert_max_resp(self, result):
        """Min assertiveness, max responsiveness → AMIABLE."""
        result.assertiveness_score = 1.0
        result.responsiveness_score = 4.0
        assert result.determine_social_style() == "AMIABLE"


# ============================================================
# END-TO-END SCORING TESTS
# ============================================================

class TestEndToEndScoring:
    """Test complete flow: responses → scores → style."""

    def test_strong_driver_profile(self, result):
        """Someone who is very assertive but not responsive → DRIVER."""
        result.set_responses(make_responses([4]*15, [1]*15))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(4.0)
        assert result.responsiveness_score == pytest.approx(1.0)
        assert result.social_style == "DRIVER"

    def test_strong_analytical_profile(self, result):
        """Someone low on both dimensions → ANALYTICAL."""
        result.set_responses(make_responses([1]*15, [1]*15))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(1.0)
        assert result.responsiveness_score == pytest.approx(1.0)
        assert result.social_style == "ANALYTICAL"

    def test_strong_expressive_profile(self, result):
        """Someone high on both dimensions → EXPRESSIVE."""
        result.set_responses(make_responses([4]*15, [4]*15))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(4.0)
        assert result.responsiveness_score == pytest.approx(4.0)
        assert result.social_style == "EXPRESSIVE"

    def test_strong_amiable_profile(self, result):
        """Someone low assertiveness, high responsiveness → AMIABLE."""
        result.set_responses(make_responses([1]*15, [4]*15))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(1.0)
        assert result.responsiveness_score == pytest.approx(4.0)
        assert result.social_style == "AMIABLE"

    def test_moderate_driver(self, result):
        """Moderate driver: mostly 3s assertiveness, mostly 2s responsiveness."""
        a_vals = [3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3]  # avg = 3.2
        r_vals = [2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2]  # avg = 1.8
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(sum(a_vals)/15, abs=0.01)
        assert result.responsiveness_score == pytest.approx(sum(r_vals)/15, abs=0.01)
        assert result.social_style == "DRIVER"

    def test_moderate_amiable(self, result):
        """Moderate amiable: mostly 2s assertiveness, mostly 3s responsiveness."""
        a_vals = [2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2]  # avg = 1.8
        r_vals = [3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3]  # avg = 3.2
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.assertiveness_score == pytest.approx(sum(a_vals)/15, abs=0.01)
        assert result.responsiveness_score == pytest.approx(sum(r_vals)/15, abs=0.01)
        assert result.social_style == "AMIABLE"

    def test_realistic_expressive_profile(self, result):
        """Realistic expressive: varied but trending high on both."""
        a_vals = [3, 4, 3, 3, 4, 3, 4, 3, 3, 4, 3, 4, 3, 3, 4]  # avg ~3.4
        r_vals = [4, 3, 3, 4, 3, 4, 3, 3, 4, 3, 4, 3, 3, 4, 3]  # avg ~3.4
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.assertiveness_score > 2.5
        assert result.responsiveness_score > 2.5
        assert result.social_style == "EXPRESSIVE"

    def test_realistic_analytical_profile(self, result):
        """Realistic analytical: varied but trending low on both."""
        a_vals = [2, 1, 2, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 2, 1]  # avg ~1.6
        r_vals = [1, 2, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 2, 1, 2]  # avg ~1.6
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.assertiveness_score < 2.5
        assert result.responsiveness_score < 2.5
        assert result.social_style == "ANALYTICAL"

    def test_boundary_responses_yield_midpoint(self, result):
        """Responses that average exactly to 2.5.

        Per spec, exactly 2.5 on both should be ANALYTICAL (strict >).
        BUG: Current code returns EXPRESSIVE due to >= comparison.
        """
        # 7 twos + 8 threes = 14 + 24 = 38, 38/15 = 2.5333... (above 2.5)
        # 8 twos + 7 threes = 16 + 21 = 37, 37/15 = 2.4667... (below 2.5)
        # To get exactly 2.5: need sum = 37.5 — not possible with integers
        # Closest: alternating 2,3 gives (2+3)*7 + 2 = 37 → 2.467 or +3 = 38 → 2.533
        # So we can't get exactly 2.5 with integer responses — test the boundary behavior
        # with 2.467 (below) and 2.533 (above)

        # Below midpoint on both
        a_vals = [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2]  # sum=37, avg=2.467
        r_vals = [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2]  # sum=37, avg=2.467
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.social_style == "ANALYTICAL"

    def test_above_midpoint_responses(self, result):
        """Responses that average just above 2.5."""
        a_vals = [3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]  # sum=38, avg=2.533
        r_vals = [3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]  # sum=38, avg=2.533
        result.set_responses(make_responses(a_vals, r_vals))
        result.calculate_scores()
        assert result.social_style == "EXPRESSIVE"


# ============================================================
# RESPONSE HANDLING TESTS
# ============================================================

class TestResponseHandling:
    """Test response serialization and edge cases."""

    def test_responses_roundtrip(self, result):
        """Responses survive JSON serialization/deserialization."""
        responses = make_responses([3]*15, [2]*15)
        result.set_responses(responses)
        retrieved = result.get_responses()
        assert retrieved == responses

    def test_string_keys_in_responses(self, result):
        """Responses dict uses string keys (matching form data)."""
        responses = make_responses([3]*15, [2]*15)
        result.set_responses(responses)
        retrieved = result.get_responses()
        for key in retrieved:
            assert isinstance(key, str), f"Key {key} should be a string"

    def test_calculate_scores_sets_style(self, result):
        """calculate_scores() must also set the social_style."""
        result.set_responses(make_responses([4]*15, [1]*15))
        result.calculate_scores()
        assert result.social_style is not None
        assert result.social_style in ("DRIVER", "EXPRESSIVE", "AMIABLE", "ANALYTICAL")

    def test_calculate_scores_returns_tuple(self, result):
        """calculate_scores() returns (assertiveness, responsiveness) tuple."""
        result.set_responses(make_responses([3]*15, [2]*15))
        ret = result.calculate_scores()
        assert isinstance(ret, tuple)
        assert len(ret) == 2


# ============================================================
# CHART AND PDF CONSISTENCY TESTS
# ============================================================

class TestChartConsistency:
    """Test that chart/PDF generation uses the same scores."""

    def test_chart_uses_correct_scores(self, app):
        """The chart function receives the same scores stored in the result."""
        from app.assessment.utils import generate_social_style_chart

        with app.app_context():
            result = AssessmentResult(user_id=1, assessment_id=1)
            result.set_responses(make_responses([4]*15, [1]*15))
            result.calculate_scores()

            # The chart should be generated with the result's scores
            chart = generate_social_style_chart(
                result.assertiveness_score,
                result.responsiveness_score
            )
            assert chart is not None
            assert chart.startswith('data:image/png;base64,')

    def test_style_description_matches_style(self, app):
        """Style description lookup returns data for all valid styles."""
        from app.assessment.utils import get_social_style_description

        for style in ("DRIVER", "EXPRESSIVE", "AMIABLE", "ANALYTICAL"):
            desc = get_social_style_description(style)
            assert desc['description'], f"No description for {style}"
            assert len(desc['strengths']) > 0, f"No strengths for {style}"
            assert len(desc['challenges']) > 0, f"No challenges for {style}"
            assert len(desc['tips']) > 0, f"No tips for {style}"


# ============================================================
# SPEC COMPLIANCE TESTS
# ============================================================

class TestSpecCompliance:
    """Tests validating alignment with the spec in resources/.

    These tests document known discrepancies between the current
    implementation and the specification.
    """

    def test_spec_boundary_uses_strict_greater_than(self, result):
        """Spec (scoring.ts:173) uses '>' not '>=' for style determination.

        At exactly (2.5, 2.5), neither dimension is strictly > 2.5,
        so the result should be ANALYTICAL.
        """
        result.assertiveness_score = 2.5
        result.responsiveness_score = 2.5
        assert result.determine_social_style() == "ANALYTICAL"

    def test_spec_boundary_assert_exactly_2_5(self, result):
        """Assertiveness exactly 2.5 should NOT be considered 'high'.

        Spec: assertiveness > 2.5 → high, else low.
        """
        result.assertiveness_score = 2.5
        result.responsiveness_score = 1.0
        assert result.determine_social_style() == "ANALYTICAL"

    def test_spec_boundary_resp_exactly_2_5(self, result):
        """Responsiveness exactly 2.5 should NOT be considered 'high'.

        Spec: responsiveness > 2.5 → high, else low.
        """
        result.assertiveness_score = 1.0
        result.responsiveness_score = 2.5
        assert result.determine_social_style() == "ANALYTICAL"

    def test_all_four_boundary_combinations(self, result):
        """Test all combinations where one or both scores are exactly 2.5.

        Per spec (strict >), 2.5 always maps to the 'low' side.
        """
        expected_per_spec = {
            (2.5, 2.5): "ANALYTICAL",  # both low per spec
            (2.5, 1.0): "ANALYTICAL",  # assert low per spec
            (2.5, 3.5): "AMIABLE",     # assert low, resp high
            (1.0, 2.5): "ANALYTICAL",  # resp low per spec
            (3.5, 2.5): "DRIVER",      # assert high, resp low per spec
        }

        for (a, r), expected in expected_per_spec.items():
            result.assertiveness_score = a
            result.responsiveness_score = r
            actual = result.determine_social_style()
            assert actual == expected, f"At ({a}, {r}): expected {expected}, got {actual}"

    def test_style_determination_consistency_with_scoring_ts(self, result):
        """Verify style determination matches scoring.ts getStyle() for non-boundary values."""
        # These are all non-boundary cases where >= and > agree
        test_cases = [
            (1.0, 1.0, "ANALYTICAL"),
            (1.5, 1.5, "ANALYTICAL"),
            (2.0, 2.0, "ANALYTICAL"),
            (2.4, 2.4, "ANALYTICAL"),
            (3.0, 1.0, "DRIVER"),
            (3.5, 2.0, "DRIVER"),
            (4.0, 1.0, "DRIVER"),
            (1.0, 3.0, "AMIABLE"),
            (2.0, 3.5, "AMIABLE"),
            (1.0, 4.0, "AMIABLE"),
            (3.0, 3.0, "EXPRESSIVE"),
            (3.5, 3.5, "EXPRESSIVE"),
            (4.0, 4.0, "EXPRESSIVE"),
        ]

        for a, r, expected in test_cases:
            result.assertiveness_score = a
            result.responsiveness_score = r
            actual = result.determine_social_style()
            assert actual == expected, f"At ({a}, {r}): expected {expected}, got {actual}"
