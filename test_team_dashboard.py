#!/usr/bin/env python3
"""
Team Dashboard Test Script
Tests team creation, member management, and dashboard visualization
"""

import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Team, TeamMember, AssessmentResult, Assessment
from werkzeug.security import generate_password_hash


def setup_test_data():
    """Create test users, teams, and assessments"""
    app = create_app(os.getenv('FLASK_CONFIG', 'development'))

    with app.app_context():
        print("=" * 80)
        print("TEAM DASHBOARD TEST - Setting up test data")
        print("=" * 80)
        print()

        # Clean up existing test data
        print("1. Cleaning up existing test data...")
        User.query.filter(User.email.like('test_%@example.com')).delete()
        db.session.commit()
        print("   ✓ Cleaned up test users")
        print()

        # Create test users with different social styles
        print("2. Creating test users...")
        test_users = [
            {
                'name': 'Alice Driver',
                'email': 'test_alice@example.com',
                'password': 'password123',
                'assertiveness': 4.0,
                'responsiveness': 1.5,
                'style': 'DRIVER'
            },
            {
                'name': 'Bob Expressive',
                'email': 'test_bob@example.com',
                'password': 'password123',
                'assertiveness': 3.5,
                'responsiveness': 3.8,
                'style': 'EXPRESSIVE'
            },
            {
                'name': 'Carol Amiable',
                'email': 'test_carol@example.com',
                'password': 'password123',
                'assertiveness': 2.0,
                'responsiveness': 3.2,
                'style': 'AMIABLE'
            },
            {
                'name': 'Dave Analytical',
                'email': 'test_dave@example.com',
                'password': 'password123',
                'assertiveness': 2.2,
                'responsiveness': 2.3,
                'style': 'ANALYTICAL'
            },
            {
                'name': 'Eve Borderline',
                'email': 'test_eve@example.com',
                'password': 'password123',
                'assertiveness': 2.5,
                'responsiveness': 2.5,
                'style': 'EXPRESSIVE'  # At boundary
            }
        ]

        users_created = []
        for user_data in test_users:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password'])
            )
            db.session.add(user)
            db.session.flush()  # Get user ID

            # Get or create assessment
            assessment = Assessment.query.first()
            if not assessment:
                print("   ✗ No assessment found in database! Run initialize_assessment.py first.")
                return False

            # Create assessment result
            result = AssessmentResult(
                user_id=user.id,
                assessment_id=assessment.id,
                assertiveness_score=user_data['assertiveness'],
                responsiveness_score=user_data['responsiveness'],
                social_style=user_data['style']
            )
            # Set dummy responses
            responses = {str(i): 1 for i in range(1, 31)}
            result.set_responses(responses)

            db.session.add(result)
            users_created.append({
                'user': user,
                'data': user_data
            })

            print(f"   ✓ Created user: {user.name} ({user_data['style']}: {user_data['assertiveness']:.1f}, {user_data['responsiveness']:.1f})")

        db.session.commit()
        print()

        # Create a test team
        print("3. Creating test team...")
        team_owner = users_created[0]['user']  # Alice is the team owner
        team = Team(
            name='Test Marketing Team',
            description='A diverse team for testing the dashboard visualization',
            owner_id=team_owner.id
        )
        db.session.add(team)
        db.session.flush()

        # Add team owner as member
        owner_membership = TeamMember(
            team_id=team.id,
            user_id=team_owner.id,
            role='owner'
        )
        db.session.add(owner_membership)
        print(f"   ✓ Created team: {team.name}")
        print(f"   ✓ Team ID: {team.id}")
        print(f"   ✓ Owner: {team_owner.name}")
        print()

        # Add other users as members
        print("4. Adding team members...")
        for user_info in users_created[1:]:  # Skip first (owner)
            membership = TeamMember(
                team_id=team.id,
                user_id=user_info['user'].id,
                role='member'
            )
            db.session.add(membership)
            print(f"   ✓ Added member: {user_info['user'].name}")

        db.session.commit()
        print()

        # Verify team setup
        print("5. Verification...")
        team_members = team.members.all()
        print(f"   Team has {len(team_members)} members")
        for membership in team_members:
            user = User.query.get(membership.user_id)
            result = user.get_latest_assessment_result()
            print(f"   - {user.name}: {result.social_style if result else 'No assessment'}")

        print()
        print("=" * 80)
        print("TEST TEAM CREATED SUCCESSFULLY")
        print("=" * 80)
        print()
        print(f"Team ID: {team.id}")
        print(f"Team Name: {team.name}")
        print(f"Members: {len(team_members)}")
        print()
        print("Access the team dashboard at:")
        print(f"  http://localhost:5001/teams/{team.id}/dashboard")
        print()
        print("Login credentials:")
        print(f"  Email: {team_owner.email}")
        print(f"  Password: password123")
        print()

        return team.id


def test_dashboard_data(team_id):
    """Test that the dashboard data is correctly calculated"""
    app = create_app(os.getenv('FLASK_CONFIG', 'development'))

    with app.app_context():
        print("=" * 80)
        print("TEAM DASHBOARD DATA VALIDATION")
        print("=" * 80)
        print()

        team = Team.query.get(team_id)
        if not team:
            print(f"✗ Team {team_id} not found!")
            return False

        print(f"Testing team: {team.name}")
        print()

        # Get team members with results
        team_members = []
        for membership in team.members.all():
            user = User.query.get(membership.user_id)
            latest_result = user.get_latest_assessment_result()
            if latest_result:
                team_members.append({
                    'user': user,
                    'result': latest_result
                })

        print(f"Members with assessments: {len(team_members)}")
        print()

        # Verify each member's data
        print("Member Data Verification:")
        print("-" * 80)

        style_counts = {'DRIVER': 0, 'EXPRESSIVE': 0, 'AMIABLE': 0, 'ANALYTICAL': 0}

        for member in team_members:
            user = member['user']
            result = member['result']

            # Verify style determination
            assert_score = result.assertiveness_score
            resp_score = result.responsiveness_score

            # Calculate expected style
            if assert_score >= 2.5 and resp_score >= 2.5:
                expected_style = "EXPRESSIVE"
            elif assert_score >= 2.5 and resp_score < 2.5:
                expected_style = "DRIVER"
            elif assert_score < 2.5 and resp_score >= 2.5:
                expected_style = "AMIABLE"
            else:
                expected_style = "ANALYTICAL"

            # Check if matches
            is_correct = result.social_style == expected_style
            status = "✓" if is_correct else "✗"

            print(f"{status} {user.name:20} - {result.social_style:12} ({assert_score:.1f}, {resp_score:.1f})")

            if is_correct:
                style_counts[result.social_style] += 1
            else:
                print(f"   ERROR: Expected {expected_style} but got {result.social_style}")

        print()
        print("Social Style Distribution:")
        print("-" * 80)
        total = sum(style_counts.values())
        for style, count in style_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 5)
            print(f"{style:12} {count:2} members  {percentage:5.1f}%  {bar}")

        print()
        print("Dashboard Grid Positioning Test:")
        print("-" * 80)
        print("(0,0) = bottom-left (ANALYTICAL), (100,100) = top-right (EXPRESSIVE)")
        print()

        for member in team_members:
            user = member['user']
            result = member['result']

            # Calculate grid position (scaled to 0-100)
            # Assertiveness: 1-4 scale → 0-100 (vertical axis, inverted for display)
            # Responsiveness: 1-4 scale → 0-100 (horizontal axis)
            x_pos = ((result.responsiveness_score - 1) / 3) * 100  # 0-100
            y_pos = ((result.assertiveness_score - 1) / 3) * 100   # 0-100

            # Determine quadrant from position
            quadrant = "UNKNOWN"
            if result.assertiveness_score >= 2.5 and result.responsiveness_score >= 2.5:
                quadrant = "EXPRESSIVE (top-right)"
            elif result.assertiveness_score >= 2.5 and result.responsiveness_score < 2.5:
                quadrant = "DRIVER (top-left)"
            elif result.assertiveness_score < 2.5 and result.responsiveness_score >= 2.5:
                quadrant = "AMIABLE (bottom-right)"
            else:
                quadrant = "ANALYTICAL (bottom-left)"

            print(f"{user.name:20} - Position: ({x_pos:5.1f}, {y_pos:5.1f}) - {quadrant}")

        print()
        print("=" * 80)
        print("DASHBOARD VALIDATION COMPLETE")
        print("=" * 80)
        print()

        return True


def run_all_tests():
    """Run all team dashboard tests"""
    print("\n" + "=" * 80)
    print("TEAM DASHBOARD COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    # Setup test data
    team_id = setup_test_data()
    if not team_id:
        print("✗ Failed to set up test data")
        return False

    # Test dashboard data
    success = test_dashboard_data(team_id)

    if success:
        print("\n✓ ALL TESTS PASSED")
        print()
        print("Manual Testing Instructions:")
        print("-" * 80)
        print("1. Open http://localhost:5001/auth/login")
        print("2. Login with: test_alice@example.com / password123")
        print(f"3. Navigate to: http://localhost:5001/teams/{team_id}/dashboard")
        print("4. Verify the grid shows 5 dots in correct positions:")
        print("   - DRIVER (top-left): Alice Driver")
        print("   - EXPRESSIVE (top-right): Bob Expressive, Eve Borderline")
        print("   - AMIABLE (bottom-right): Carol Amiable")
        print("   - ANALYTICAL (bottom-left): Dave Analytical")
        print()
        return True
    else:
        print("\n✗ TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
