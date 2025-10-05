#!/usr/bin/env python3
"""
Integration tests for Social Styles Assessment web application.
Tests the complete flow from form submission to result calculation.
"""

import requests
from bs4 import BeautifulSoup
import re
import sys

BASE_URL = "http://localhost:5001"

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "ANALYTICAL - All 1s",
        "assertiveness": [1] * 15,
        "responsiveness": [1] * 15,
        "expected_style": "ANALYTICAL",
        "expected_assert": 1.0,
        "expected_resp": 1.0
    },
    {
        "name": "DRIVER - High assert, low resp",
        "assertiveness": [4] * 15,
        "responsiveness": [1] * 15,
        "expected_style": "DRIVER",
        "expected_assert": 4.0,
        "expected_resp": 1.0
    },
    {
        "name": "AMIABLE - Low assert, high resp",
        "assertiveness": [1] * 15,
        "responsiveness": [4] * 15,
        "expected_style": "AMIABLE",
        "expected_assert": 1.0,
        "expected_resp": 4.0
    },
    {
        "name": "EXPRESSIVE - All 4s",
        "assertiveness": [4] * 15,
        "responsiveness": [4] * 15,
        "expected_style": "EXPRESSIVE",
        "expected_assert": 4.0,
        "expected_resp": 4.0
    },
    {
        "name": "Borderline DRIVER (2.53, 2.27)",
        "assertiveness": [3,3,2,2,3,2,3,2,3,2,3,2,3,2,3],  # avg = 2.53
        "responsiveness": [2,2,2,2,3,2,2,3,2,2,3,2,2,3,2],  # avg = 2.27
        "expected_style": "DRIVER",
        "expected_assert": 2.53,
        "expected_resp": 2.27
    },
    {
        "name": "Borderline AMIABLE (2.27, 2.53)",
        "assertiveness": [2,2,2,2,3,2,2,3,2,2,3,2,2,3,2],  # avg = 2.27
        "responsiveness": [3,3,2,2,3,2,3,2,3,2,3,2,3,2,3],  # avg = 2.53
        "expected_style": "AMIABLE",
        "expected_assert": 2.27,
        "expected_resp": 2.53
    },
    {
        "name": "Moderate EXPRESSIVE (2.8, 2.73)",
        "assertiveness": [3,3,3,2,3,3,3,2,3,3,3,2,3,3,3],  # avg = 2.8
        "responsiveness": [3,3,2,3,3,3,2,3,3,3,2,3,3,3,2],  # avg = 2.73
        "expected_style": "EXPRESSIVE",
        "expected_assert": 2.8,
        "expected_resp": 2.73
    },
]


def get_csrf_token(session):
    """Get CSRF token from the assessment form"""
    response = session.get(f"{BASE_URL}/assessment/take/1?guest=True")
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        return csrf_input.get('value')
    return None


def submit_assessment(session, csrf_token, assertiveness, responsiveness):
    """Submit assessment with given responses"""
    data = {'csrf_token': csrf_token}

    # Add assertiveness responses (questions 1-15)
    for i, value in enumerate(assertiveness, 1):
        data[f'assertiveness_{i}'] = str(value)

    # Add responsiveness responses (questions 16-30)
    for i, value in enumerate(responsiveness, 16):
        data[f'responsiveness_{i}'] = str(value)

    response = session.post(
        f"{BASE_URL}/assessment/take/1?guest=True",
        data=data,
        allow_redirects=True
    )

    return response


def extract_results(html):
    """Extract assessment results from the response HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    # Try to find scores and social style in the page
    # This will depend on your actual HTML structure
    text = soup.get_text()

    # Look for social style mentions
    social_styles = ['ANALYTICAL', 'DRIVER', 'AMIABLE', 'EXPRESSIVE']
    detected_style = None
    for style in social_styles:
        if style in text:
            detected_style = style
            break

    # Try to find scores - look for patterns like "2.5" or "Assertiveness: 2.5"
    assert_pattern = re.search(r'(?:Assertiveness|assertiveness)[\s:]+(\d+\.?\d*)', text)
    resp_pattern = re.search(r'(?:Responsiveness|responsiveness)[\s:]+(\d+\.?\d*)', text)

    assert_score = float(assert_pattern.group(1)) if assert_pattern else None
    resp_score = float(resp_pattern.group(1)) if resp_pattern else None

    return {
        'style': detected_style,
        'assertiveness': assert_score,
        'responsiveness': resp_score,
        'raw_text': text[:500]  # First 500 chars for debugging
    }


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 80)
    print("SOCIAL STYLES ASSESSMENT - INTEGRATION TESTS")
    print("=" * 80)
    print()

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✓ Server is running at {BASE_URL}")
        print()
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: Could not connect to {BASE_URL}")
        print(f"  Make sure the application is running with: docker-compose up")
        return False

    passed = 0
    failed = 0
    errors = []

    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"Test {i}: {scenario['name']}")
        print("-" * 80)

        try:
            # Create a new session for each test
            session = requests.Session()

            # Get CSRF token
            csrf_token = get_csrf_token(session)
            if not csrf_token:
                print("  ✗ Failed to get CSRF token")
                failed += 1
                errors.append({'test': scenario['name'], 'error': 'No CSRF token'})
                print()
                continue

            # Submit assessment
            response = submit_assessment(
                session,
                csrf_token,
                scenario['assertiveness'],
                scenario['responsiveness']
            )

            # Extract results
            results = extract_results(response.text)

            # Validate
            style_match = results['style'] == scenario['expected_style']

            # For scores, allow small floating point differences
            assert_match = results['assertiveness'] is not None and \
                          abs(results['assertiveness'] - scenario['expected_assert']) < 0.1
            resp_match = results['responsiveness'] is not None and \
                        abs(results['responsiveness'] - scenario['expected_resp']) < 0.1

            print(f"  Social Style: {results['style']} (expected: {scenario['expected_style']}) {'✓' if style_match else '✗'}")

            if results['assertiveness'] is not None:
                print(f"  Assertiveness: {results['assertiveness']:.2f} (expected: {scenario['expected_assert']:.2f}) {'✓' if assert_match else '✗'}")
            else:
                print(f"  Assertiveness: Not found ✗")
                assert_match = False

            if results['responsiveness'] is not None:
                print(f"  Responsiveness: {results['responsiveness']:.2f} (expected: {scenario['expected_resp']:.2f}) {'✓' if resp_match else '✗'}")
            else:
                print(f"  Responsiveness: Not found ✗")
                resp_match = False

            # Overall result
            if style_match and assert_match and resp_match:
                print(f"  Result: ✓ PASSED")
                passed += 1
            else:
                print(f"  Result: ✗ FAILED")
                failed += 1
                errors.append({
                    'test': scenario['name'],
                    'expected': f"{scenario['expected_style']} ({scenario['expected_assert']:.2f}, {scenario['expected_resp']:.2f})",
                    'actual': f"{results['style']} ({results['assertiveness']}, {results['responsiveness']})"
                })

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed += 1
            errors.append({'test': scenario['name'], 'error': str(e)})

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
            if 'expected' in error:
                print(f"    Expected: {error['expected']}")
                print(f"    Actual:   {error['actual']}")
            else:
                print(f"    Error: {error.get('error', 'Unknown error')}")

    print()
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
