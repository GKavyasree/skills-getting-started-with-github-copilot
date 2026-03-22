"""
Tests for the Mergington High School Activities API

Tests cover all endpoints:
- GET /activities - Retrieve all activities
- POST /activities/{activity_name}/signup - Sign up for an activity
- DELETE /activities/{activity_name}/unregister - Unregister from an activity
- GET / - Root redirect endpoint
"""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient instance for the API"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities database to initial state before each test.
    This ensures test isolation and prevents test ordering dependencies.
    """
    # Store original state
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# GET /activities Endpoint Tests
# ============================================================================

def test_get_activities_returns_all_activities(client, reset_activities):
    """Test that GET /activities returns all available activities"""
    # Arrange - no setup needed, data is pre-populated in fixtures
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert len(data) == 9
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_get_activities_response_structure(client, reset_activities):
    """Test that activity response has correct structure"""
    # Arrange - no setup needed
    
    # Act
    response = client.get("/activities")
    data = response.json()
    first_activity = data["Chess Club"]
    
    # Assert
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)


def test_get_activities_correct_participant_count(client, reset_activities):
    """Test that participant counts are accurate"""
    # Arrange - no setup needed
    
    # Act
    response = client.get("/activities")
    data = response.json()
    chess_club_participants = data["Chess Club"]["participants"]
    
    # Assert
    assert len(chess_club_participants) == 2
    assert "michael@mergington.edu" in chess_club_participants
    assert "daniel@mergington.edu" in chess_club_participants


# ============================================================================
# POST /activities/{activity_name}/signup Endpoint Tests
# ============================================================================

def test_signup_successful(client, reset_activities):
    """Test successful signup for a new student"""
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert "message" in data
    assert email in data["message"]


def test_signup_adds_participant(client, reset_activities):
    """Test that signup actually adds the participant to the activity"""
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    response_before = client.get("/activities")
    initial_count = len(response_before.json()[activity_name]["participants"])
    
    # Act
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    response_after = client.get("/activities")
    new_count = len(response_after.json()[activity_name]["participants"])
    participants = response_after.json()[activity_name]["participants"]
    
    # Assert
    assert new_count == initial_count + 1
    assert email in participants


def test_signup_duplicate_email_error(client, reset_activities):
    """Test that duplicate signup is rejected"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already in activity
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 400
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity_error(client, reset_activities):
    """Test that signup for non-existent activity returns 404"""
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in data["detail"]


def test_signup_multiple_students(client, reset_activities):
    """Test signing up multiple different students"""
    # Arrange
    activity_name = "Programming Class"
    emails = [
        "student1@mergington.edu",
        "student2@mergington.edu",
        "student3@mergington.edu"
    ]
    
    # Act
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    response_final = client.get("/activities")
    participants = response_final.json()[activity_name]["participants"]
    
    # Assert
    for email in emails:
        assert email in participants


# ============================================================================
# DELETE /activities/{activity_name}/unregister Endpoint Tests
# ============================================================================

def test_unregister_successful(client, reset_activities):
    """Test successful unregistration from an activity"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert "message" in data
    assert email in data["message"]


def test_unregister_removes_participant(client, reset_activities):
    """Test that unregister actually removes the participant"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    response_before = client.get("/activities")
    initial_count = len(response_before.json()[activity_name]["participants"])
    
    # Act
    client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    response_after = client.get("/activities")
    new_count = len(response_after.json()[activity_name]["participants"])
    participants = response_after.json()[activity_name]["participants"]
    
    # Assert
    assert new_count == initial_count - 1
    assert email not in participants


def test_unregister_nonexistent_activity_error(client, reset_activities):
    """Test that unregister from non-existent activity returns 404"""
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in data["detail"]


def test_unregister_nonparticipant_error(client, reset_activities):
    """Test that unregistering non-participant returns 400"""
    # Arrange
    activity_name = "Chess Club"
    email = "nonparticipant@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    data = response.json()
    
    # Assert
    assert response.status_code == 400
    assert "not signed up" in data["detail"]


def test_unregister_then_signup_again(client, reset_activities):
    """Test that a student can sign up again after unregistering"""
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    
    # Act - Signup
    response1 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Act - Unregister
    response2 = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Act - Signup again
    response3 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    response_final = client.get("/activities")
    participants = response_final.json()[activity_name]["participants"]
    
    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert email in participants


# ============================================================================
# GET / Root Endpoint Tests
# ============================================================================

def test_root_redirect(client, reset_activities):
    """Test that root endpoint redirects to static index.html"""
    # Arrange - no setup needed
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert "location" in response.headers
    assert "/static/index.html" in response.headers["location"]


# ============================================================================
# Integration Tests
# ============================================================================

def test_signup_and_unregister_flow(client, reset_activities):
    """Test complete signup and unregister flow"""
    # Arrange
    activity = "Gym Class"
    email = "athlete@mergington.edu"
    response_initial = client.get("/activities")
    initial_participants = len(response_initial.json()[activity]["participants"])
    
    # Act - Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    response_after_signup = client.get("/activities")
    after_signup = len(response_after_signup.json()[activity]["participants"])
    
    # Act - Unregister
    unregister_response = client.delete(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    response_final = client.get("/activities")
    final_count = len(response_final.json()[activity]["participants"])
    
    # Assert
    assert signup_response.status_code == 200
    assert after_signup == initial_participants + 1
    assert unregister_response.status_code == 200
    assert final_count == initial_participants


def test_multiple_activities_independent(client, reset_activities):
    """Test that signups in different activities don't interfere"""
    # Arrange
    email = "student@mergington.edu"
    activity1 = "Chess Club"
    activity2 = "Gym Class"
    
    # Act - Sign up for two activities
    response1 = client.post(
        f"/activities/{activity1}/signup",
        params={"email": email}
    )
    response2 = client.post(
        f"/activities/{activity2}/signup",
        params={"email": email}
    )
    response_verify = client.get("/activities")
    activities_data = response_verify.json()
    
    # Act - Unregister from first activity
    response3 = client.delete(
        f"/activities/{activity1}/unregister",
        params={"email": email}
    )
    response_final = client.get("/activities")
    final_data = response_final.json()
    
    # Assert - Both signups successful
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert email in activities_data[activity1]["participants"]
    assert email in activities_data[activity2]["participants"]
    
    # Assert - Unregister successful, only from first activity
    assert response3.status_code == 200
    assert email not in final_data[activity1]["participants"]
    assert email in final_data[activity2]["participants"]
