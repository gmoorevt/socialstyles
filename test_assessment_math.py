#!/usr/bin/env python3
"""
Comprehensive test suite for Social Styles Assessment scoring logic.
Tests all four social style quadrants with edge cases.
"""

import sys
import json
from datetime import datetime

# Test scenarios for each social style
# Format: (name, assertiveness_responses, responsiveness_responses, expected_style, expected_assert_score, expected_resp_score)

TEST_SCENARIOS = [
    # ANALYTICAL: Low Assertiveness (<2.5), Low Responsiveness (<2.5)
    {
        "name": "Pure ANALYTICAL (all 1s)",
        "assertiveness": [1] * 15,  # Questions 1-15
        "responsiveness": [1] * 15,  # Questions 16-30
        "expected_style": "ANALYTICAL",
        "expected_assertiveness": 1.0,
        "expected_responsiveness": 1.0
    },
    {
        "name": "Strong ANALYTICAL (mostly 1s and 2s)",
        "assertiveness": [1, 1, 2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 1, 2],
        "responsiveness": [2, 1, 1, 2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 1],
        "expected_style": "ANALYTICAL",
        "expected_assertiveness": 1.4,
        "expected_responsiveness": 1.4
    },
    {
        "name": "Borderline ANALYTICAL (just under 2.5)",
        "assertiveness": [2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 2],  # avg = 2.27
        "responsiveness": [2, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2],  # avg = 2.27
        "expected_style": "ANALYTICAL",
        "expected_assertiveness": 2.27,
        "expected_responsiveness": 2.27
    },

    # DRIVER: High Assertiveness (≥2.5), Low Responsiveness (<2.5)
    {
        "name": "Pure DRIVER (high assert, low resp)",
        "assertiveness": [4] * 15,
        "responsiveness": [1] * 15,
        "expected_style": "DRIVER",
        "expected_assertiveness": 4.0,
        "expected_responsiveness": 1.0
    },
    {
        "name": "Strong DRIVER (mostly 3s and 4s assertiveness, 1s and 2s responsiveness)",
        "assertiveness": [4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4],
        "responsiveness": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1],
        "expected_style": "DRIVER",
        "expected_assertiveness": 3.53,
        "expected_responsiveness": 1.47
    },
    {
        "name": "Borderline DRIVER (assert at 2.5, resp under 2.5)",
        "assertiveness": [3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 3, 2, 3],  # avg = 2.53
        "responsiveness": [2, 2, 2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2],  # avg = 2.2
        "expected_style": "DRIVER",
        "expected_assertiveness": 2.53,
        "expected_responsiveness": 2.2
    },

    # AMIABLE: Low Assertiveness (<2.5), High Responsiveness (≥2.5)
    {
        "name": "Pure AMIABLE (low assert, high resp)",
        "assertiveness": [1] * 15,
        "responsiveness": [4] * 15,
        "expected_style": "AMIABLE",
        "expected_assertiveness": 1.0,
        "expected_responsiveness": 4.0
    },
    {
        "name": "Strong AMIABLE (mostly 1s and 2s assertiveness, 3s and 4s responsiveness)",
        "assertiveness": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1],
        "responsiveness": [4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4],
        "expected_style": "AMIABLE",
        "expected_assertiveness": 1.47,
        "expected_responsiveness": 3.53
    },
    {
        "name": "Borderline AMIABLE (assert under 2.5, resp at 2.5)",
        "assertiveness": [2, 2, 2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2],  # avg = 2.2
        "responsiveness": [3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 3, 2, 3],  # avg = 2.53
        "expected_style": "AMIABLE",
        "expected_assertiveness": 2.2,
        "expected_responsiveness": 2.53
    },

    # EXPRESSIVE: High Assertiveness (≥2.5), High Responsiveness (≥2.5)
    {
        "name": "Pure EXPRESSIVE (all 4s)",
        "assertiveness": [4] * 15,
        "responsiveness": [4] * 15,
        "expected_style": "EXPRESSIVE",
        "expected_assertiveness": 4.0,
        "expected_responsiveness": 4.0
    },
    {
        "name": "Strong EXPRESSIVE (mostly 3s and 4s)",
        "assertiveness": [4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4],
        "responsiveness": [3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3],
        "expected_style": "EXPRESSIVE",
        "expected_assertiveness": 3.53,
        "expected_responsiveness": 3.53
    },
    {
        "name": "Borderline EXPRESSIVE (both at 2.5)",
        "assertiveness": [3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 3, 2, 3],  # avg = 2.53
        "responsiveness": [3, 3, 2, 2, 3, 3, 2, 2, 3, 3, 2, 2, 3, 2, 3],  # avg = 2.53
        "expected_style": "EXPRESSIVE",
        "expected_assertiveness": 2.53,
        "expected_responsiveness": 2.53
    },

    # EDGE CASES - Exact boundary testing (2.5 cutoff)
    {
        "name": "Exact boundary - ANALYTICAL to AMIABLE",
        "assertiveness": [2, 2, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2],  # avg = 2.267 (< 2.5)
        "responsiveness": [3, 3, 2, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],  # avg = 2.533 (≥ 2.5)
        "expected_style": "AMIABLE",
        "expected_assertiveness": 2.27,
        "expected_responsiveness": 2.53
    },
    {
        "name": "Exact boundary - ANALYTICAL to DRIVER",
        "assertiveness": [3, 3, 2, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],  # avg = 2.533 (≥ 2.5)
        "responsiveness": [2, 2, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2],  # avg = 2.267 (< 2.5)
        "expected_style": "DRIVER",
        "expected_assertiveness": 2.53,
        "expected_responsiveness": 2.27
    },
    {
        "name": "Mixed responses - moderate EXPRESSIVE",
        "assertiveness": [3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3],  # avg = 2.8
        "responsiveness": [3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2],  # avg = 2.73
        "expected_style": "EXPRESSIVE",
        "expected_assertiveness": 2.8,
        "expected_responsiveness": 2.73
    },
]


class AssessmentCalculator:
    """Mimics the AssessmentResult.calculate_scores() logic"""

    @staticmethod
    def calculate_scores(assertiveness_responses, responsiveness_responses):
        """Calculate scores based on responses"""
        assert_total = sum(assertiveness_responses)
        resp_total = sum(responsiveness_responses)

        assert_score = assert_total / 15
        resp_score = resp_total / 15

        return assert_score, resp_score

    @staticmethod
    def determine_social_style(assert_score, resp_score):
        """Determine social style based on scores"""
        if assert_score >= 2.5 and resp_score >= 2.5:
            return "EXPRESSIVE"
        elif assert_score >= 2.5 and resp_score < 2.5:
            return "DRIVER"
        elif assert_score < 2.5 and resp_score >= 2.5:
            return "AMIABLE"
        else:
            return "ANALYTICAL"


def run_tests():
    """Run all test scenarios and report results"""
    print("=" * 80)
    print("SOCIAL STYLES ASSESSMENT - SCORING VALIDATION TESTS")
    print("=" * 80)
    print()

    passed = 0
    failed = 0
    errors = []

    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"Test {i}: {scenario['name']}")
        print("-" * 80)

        # Calculate scores
        assert_score, resp_score = AssessmentCalculator.calculate_scores(
            scenario['assertiveness'],
            scenario['responsiveness']
        )

        # Determine style
        social_style = AssessmentCalculator.determine_social_style(assert_score, resp_score)

        # Round scores to 2 decimal places for comparison
        assert_score = round(assert_score, 2)
        resp_score = round(resp_score, 2)

        # Validate results
        assert_match = abs(assert_score - scenario['expected_assertiveness']) < 0.01
        resp_match = abs(resp_score - scenario['expected_responsiveness']) < 0.01
        style_match = social_style == scenario['expected_style']

        print(f"  Assertiveness: {assert_score:.2f} (expected: {scenario['expected_assertiveness']:.2f}) {'✓' if assert_match else '✗'}")
        print(f"  Responsiveness: {resp_score:.2f} (expected: {scenario['expected_responsiveness']:.2f}) {'✓' if resp_match else '✗'}")
        print(f"  Social Style: {social_style} (expected: {scenario['expected_style']}) {'✓' if style_match else '✗'}")

        # Overall result
        if assert_match and resp_match and style_match:
            print(f"  Result: ✓ PASSED")
            passed += 1
        else:
            print(f"  Result: ✗ FAILED")
            failed += 1
            errors.append({
                'test': scenario['name'],
                'expected': f"{scenario['expected_style']} ({scenario['expected_assertiveness']:.2f}, {scenario['expected_responsiveness']:.2f})",
                'actual': f"{social_style} ({assert_score:.2f}, {resp_score:.2f})"
            })

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(TEST_SCENARIOS)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/len(TEST_SCENARIOS)*100):.1f}%")

    if errors:
        print()
        print("FAILED TESTS:")
        for error in errors:
            print(f"  • {error['test']}")
            print(f"    Expected: {error['expected']}")
            print(f"    Actual:   {error['actual']}")

    print()

    # Additional validation checks
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    # Check boundary conditions
    print("\n1. Boundary Validation (2.5 cutoff):")
    boundary_tests = [
        (2.49, 2.49, "ANALYTICAL"),
        (2.50, 2.49, "DRIVER"),
        (2.49, 2.50, "AMIABLE"),
        (2.50, 2.50, "EXPRESSIVE"),
    ]

    for assert_val, resp_val, expected in boundary_tests:
        result = AssessmentCalculator.determine_social_style(assert_val, resp_val)
        status = "✓" if result == expected else "✗"
        print(f"  ({assert_val:.2f}, {resp_val:.2f}) → {result} (expected: {expected}) {status}")

    # Check score range validation
    print("\n2. Score Range Validation (1.0 to 4.0):")
    range_tests = [
        ([1]*15, 1.0, "minimum"),
        ([4]*15, 4.0, "maximum"),
        ([2,3]*7 + [2], 2.5, "midpoint"),
    ]

    for responses, expected, desc in range_tests:
        score, _ = AssessmentCalculator.calculate_scores(responses, [1]*15)
        status = "✓" if abs(score - expected) < 0.01 else "✗"
        print(f"  {desc}: {score:.2f} (expected: {expected:.2f}) {status}")

    print()
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
