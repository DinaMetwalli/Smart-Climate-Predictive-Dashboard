import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from src.api.services.user_manager_service import UserManagerService
from src.utils.errors import (UsernameAlreadyExistsError, PasswordTooShortError,
                              PasswordDoesNotMatchError, UserDoesNotExistError,
                              UsernameTooShortError)


@patch("src.api.services.user_manager_service.db")
def test_register_user_success(mock_db):
    
    # Simulate mock call to check if username is already taken
    mock_db.execute_and_fetch_one.side_effect = [
        None,
        ("some-uuid",)
    ]

    service = UserManagerService()
    result = service.register_user("newuser", "password123", "password123")
    user_id = service.get_user("newuser")

    assert result == True
    assert user_id is not None
    
    # Verify the insert was attempted
    mock_db.execute_and_commit.assert_called_once()

@patch("src.api.services.user_manager_service.db")
def test_register_user_already_exists(mock_db):
    
    # Returning a row to simulate the username already being taken
    mock_db.execute_and_fetch_one.return_value = ("some-uuid",)

    service = UserManagerService()
    with pytest.raises(UsernameAlreadyExistsError):
        service.register_user("existinguser", "password123", "password123")

@patch("src.api.services.user_manager_service.db")
def test_register_user_passwords_dont_match(mock_db):
    
    # Simulate mock call to check if username is already taken
    mock_db.execute_and_fetch_one.return_value = None

    service = UserManagerService()
    with pytest.raises(PasswordDoesNotMatchError):
        service.register_user("newuser", "password123", "differentpassword")

@patch("src.api.services.user_manager_service.db")
def test_register_user_password_too_short(mock_db):
    
    # Simulate mock call to check if username is already taken
    mock_db.execute_and_fetch_one.return_value = None

    service = UserManagerService()
    with pytest.raises(PasswordTooShortError):
        service.register_user("newuser", "short", "short")

@patch("src.api.services.user_manager_service.db")
def test_login_user_success(mock_db):
    
    username = "demouser"
    password = "password123"
    hashed = generate_password_hash(password)
    
    # Simulate database execute and fetch one through mock
    mock_db.execute_and_fetch_one.return_value = (
        "test-uuid",
        username,
        hashed
    )

    # Login demo user and assert correct results
    user_service = UserManagerService()
    result = user_service.login_user(username, password)
    
    assert result == {"id": "test-uuid", "username": username}

@patch("src.api.services.user_manager_service.db")
def test_login_user_does_not_exist(mock_db):
    
    username = "randomuser"
    password = "password123"
    
    # Simulate database execute and fetch one through mock
    mock_db.execute_and_fetch_one.return_value = None

    user_service = UserManagerService()
    with pytest.raises(UserDoesNotExistError):
        user_service.login_user(username, password)

@patch("src.api.services.user_manager_service.db")
def test_login_incorrect_password(mock_db):
    
    username = "randomuser"
    password = "incorrectpassword"
    hashed = generate_password_hash("correctpassword")
    
    # Simulate database execute and fetch one through mock
    mock_db.execute_and_fetch_one.return_value = (
        "test-uuid",
        username,
        hashed
    )

    user_service = UserManagerService()
    with pytest.raises(PasswordDoesNotMatchError):
        user_service.login_user(username, password)

@patch("src.api.services.user_manager_service.db")
def test_delete_user_success(mock_db):
    mock_db.execute_and_fetch_one.side_effect = [
        None,
        ("some-uuid",)
    ]
    mock_db.execute_and_fetch_all.return_value = []

    service = UserManagerService()
    service.register_user("newuser", "password123", "password123")
    user = service.get_user("newuser")
    result = service.delete_user(user[0])

    assert result == True
    mock_db.execute_and_commit.assert_any_call(
        "UPDATE users SET active = %s WHERE id = %s",
        False, user[0]
    )

@patch("src.api.services.user_manager_service.db")
def test_update_username_success(mock_db):
    
    # Simulate mock call to get current user's ID and check if username is already taken
    mock_db.execute_and_fetch_one.side_effect = [
        ("some-uuid",),
        None,
        ("some-uuid",)
    ]

    service = UserManagerService()

    # Get the current user's ID
    current_users_id = service.get_user("oldusername")
    result = service.update_username(current_users_id[0], "newusername")
    
    # Check that the new username exists
    updated_users_id = service.get_user("newusername")
    
    assert result == True
    assert current_users_id[0] == updated_users_id[0]

@patch("src.api.services.user_manager_service.db")
def test_update_username_invalid(mock_db):
    
    # Simulate mock call to get current user's ID and check if username is already taken
    mock_db.execute_and_fetch_one.side_effect = [
        ("some-uuid",),
        None
    ]

    service = UserManagerService()

    current_users_id = service.get_user("oldusername")
    with pytest.raises(UsernameTooShortError):
        service.update_username(current_users_id[0], "un")

    # Assert new username does not exist
    with pytest.raises(UserDoesNotExistError):
        service.get_user("un")

@patch("src.api.services.user_manager_service.db")
def test_update_password_success(mock_db):
    
    current_password = "password123"
    new_password = "newpassword"
    hashed = generate_password_hash(current_password)
    
    # Simulate mock call to get current user's ID and check current password hash
    mock_db.execute_and_fetch_one.side_effect = [
        ("some-uuid",),
        (hashed,)
    ]

    service = UserManagerService()
    current_users_id = service.get_user("currentuser")
    result = service.update_password(current_users_id[0], current_password, new_password)
    
    mock_db.execute_and_commit.assert_called_once()
    assert result == True

@patch("src.api.services.user_manager_service.db")
def test_update_password_incorrect_current_password(mock_db):
    
    current_password = "wrongpassword"
    new_password = "newpassword"
    hashed = generate_password_hash("password123")
    
    # Simulate mock call to get current user's ID and check current password hash
    mock_db.execute_and_fetch_one.side_effect = [
        ("some-uuid",),
        (hashed,)
    ]

    service = UserManagerService()
    current_users_id = service.get_user("currentuser")
    
    with pytest.raises(PasswordDoesNotMatchError):
        service.update_password(current_users_id[0], current_password, new_password)