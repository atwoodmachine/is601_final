from builtins import range
import pytest
from sqlalchemy import select
from app.dependencies import get_settings
from app.models.user_model import User, UserRole
from app.services.user_service import UserService
from app.utils.nickname_gen import generate_nickname

pytestmark = pytest.mark.asyncio

# Test creating a user with valid data
async def test_create_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "valid_user@example.com",
        "password": "ValidPassword123!",
        "role": UserRole.ADMIN.name
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test creating a user with invalid data
async def test_create_user_with_invalid_data(db_session, email_service):
    user_data = {
        "nickname": "",  # Invalid nickname
        "email": "invalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is None

# Test fetching a user by ID when the user exists
async def test_get_by_id_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_id(db_session, user.id)
    assert retrieved_user.id == user.id

# Test fetching a user by ID when the user does not exist
async def test_get_by_id_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    retrieved_user = await UserService.get_by_id(db_session, non_existent_user_id)
    assert retrieved_user is None

# Test fetching a user by nickname when the user exists
async def test_get_by_nickname_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved_user.nickname == user.nickname

# Test fetching a user by nickname when the user does not exist
async def test_get_by_nickname_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_nickname(db_session, "non_existent_nickname")
    assert retrieved_user is None

# Test fetching a user by email when the user exists
async def test_get_by_email_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_email(db_session, user.email)
    assert retrieved_user.email == user.email

# Test fetching a user by email when the user does not exist
async def test_get_by_email_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_email(db_session, "non_existent_email@example.com")
    assert retrieved_user is None

# Test updating a user with valid data
async def test_update_user_valid_data(db_session, user):
    new_email = "updated_email@example.com"
    updated_user = await UserService.update(db_session, user.id, {"email": new_email})
    assert updated_user is not None
    assert updated_user.email == new_email

# Test updating a user with invalid data
async def test_update_user_invalid_data(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {"email": "invalidemail"})
    assert updated_user is None

# Test deleting a user who exists
async def test_delete_user_exists(db_session, user):
    deletion_success = await UserService.delete(db_session, user.id)
    assert deletion_success is True

# Test attempting to delete a user who does not exist
async def test_delete_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    deletion_success = await UserService.delete(db_session, non_existent_user_id)
    assert deletion_success is False

# Test listing users with pagination
async def test_list_users_with_pagination(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.list_users(db_session, skip=0, limit=10)
    users_page_2 = await UserService.list_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

# Test registering a user with valid data
async def test_register_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "role": UserRole.ADMIN
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test attempting to register a user with invalid data
async def test_register_user_with_invalid_data(db_session, email_service):
    user_data = {
        "email": "registerinvalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is None

# Test successful user login
async def test_login_user_successful(db_session, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "MySuperPassword$1234",
    }
    logged_in_user = await UserService.login_user(db_session, user_data["email"], user_data["password"])
    assert logged_in_user is not None

# Test user login with incorrect email
async def test_login_user_incorrect_email(db_session):
    user = await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    assert user is None

# Test user login with incorrect password
async def test_login_user_incorrect_password(db_session, user):
    user = await UserService.login_user(db_session, user.email, "IncorrectPassword!")
    assert user is None

# Test account lock after maximum failed login attempts
async def test_account_lock_after_failed_logins(db_session, verified_user):
    max_login_attempts = get_settings().max_login_attempts
    for _ in range(max_login_attempts):
        await UserService.login_user(db_session, verified_user.email, "wrongpassword")
    
    is_locked = await UserService.is_account_locked(db_session, verified_user.email)
    assert is_locked, "The account should be locked after the maximum number of failed login attempts."

# Test resetting a user's password
async def test_reset_password(db_session, user):
    new_password = "NewPassword123!"
    reset_success = await UserService.reset_password(db_session, user.id, new_password)
    assert reset_success is True

# Test verifying a user's email
async def test_verify_email_with_token(db_session, user):
    token = "valid_token_example"  # This should be set in your user setup if it depends on a real token
    user.verification_token = token  # Simulating setting the token in the database
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, token)
    assert result is True

# Test unlocking a user's account
async def test_unlock_user_account(db_session, locked_user):
    unlocked = await UserService.unlock_user_account(db_session, locked_user.id)
    assert unlocked, "The account should be unlocked"
    refreshed_user = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed_user.is_locked, "The user should no longer be locked"
    
#Testing for search/fileter related features and cases
async def test_get_by_search_nickname(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, nickname=user.nickname)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].nickname == user.nickname

async def test_get_by_search_email(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, email=user.email)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].email == user.email

async def test_get_by_search_role(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.get_by_search(db_session, role=UserRole.AUTHENTICATED, skip=0, limit=10)
    users_page_2 = await UserService.get_by_search(db_session, role=UserRole.AUTHENTICATED, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id
    assert users_page_1[0].role == UserRole.AUTHENTICATED

async def test_get_by_search_is_professional(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, is_professional=False)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].is_professional == False

async def test_get_by_search_date_range(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, created_before=user.created_at, created_after=user.created_at)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].created_at == user.created_at

async def test_get_by_search_not_exists(db_session):
    retrieved_users = await UserService.get_by_search(db_session, nickname="nick", email="nothere@nowhere.com", role=UserRole.AUTHENTICATED)
    assert len(retrieved_users) == 0

#search combinations
async def test_get_by_search_all(db_session, user):
    retrieved_users = await UserService.get_by_search(
        db_session, 
        nickname=user.nickname, 
        email=user.email, 
        role=UserRole.AUTHENTICATED,
        is_professional=user.is_professional,
        created_after=user.created_at,
        created_before=user.created_at)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].id == user.id
    assert retrieved_users[0].nickname == user.nickname
    assert retrieved_users[0].email == user.email
    assert retrieved_users[0].role == UserRole.AUTHENTICATED

async def test_get_by_search_email_nickname(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, nickname=user.nickname, email=user.email)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].nickname == user.nickname
    assert retrieved_users[0].email == user.email

async def test_get_by_search_email_role(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, email=user.email, role=UserRole.AUTHENTICATED)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].email == user.email
    assert retrieved_users[0].role == UserRole.AUTHENTICATED

async def test_get_by_search_nickname_role(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, nickname=user.nickname, role=UserRole.AUTHENTICATED)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].nickname == user.nickname
    assert retrieved_users[0].role == UserRole.AUTHENTICATED

async def test_get_by_search_role_date_range(db_session, user):
    retrieved_users = await UserService.get_by_search(db_session, role=UserRole.AUTHENTICATED, created_before=user.created_at, created_after=user.created_at)
    assert len(retrieved_users) == 1
    assert retrieved_users[0].created_at == user.created_at
    assert retrieved_users[0].role == UserRole.AUTHENTICATED