from src.utils.database_config import db
from src.utils.errors import (PasswordTooShortError, PasswordDoesNotMatchError,
                              UsernameAlreadyExistsError, UsernameTooShortError,
                              UserDoesNotExistError)
from werkzeug.security import generate_password_hash, check_password_hash

import datetime;

class UserManagerService:
    def __init__(self):
        print("→ insitialized User Manager ←")
    
    def get_user(self, username: str) -> bool | dict:
        user = db.execute_and_fetch_one(
            "SELECT id FROM users WHERE active = %s AND username = %s;", 
            True, username
        )
        
        if not user:
            raise UserDoesNotExistError("No matching accounts could be found for the provided username.")
        return user
    
    def register_user(self, username: str, password: str, same_password: str) -> bool:
        
        # Complete all input validation checks first
        if self.validate_username(username) and self.validate_same_password(password, same_password) and self.validate_password(password):
            password_hash = generate_password_hash(password)
            timestamp = datetime.datetime.now()
            db.execute_and_commit(
                "INSERT INTO users (username, password_hash, creation_timestamp, active) VALUES (%s, %s, %s, %s)",
                username, password_hash, timestamp, True
                )

            print(f"User {username} inserted at {timestamp}.")
            return True
    
    def login_user(self, username: str, password: str) -> dict:
        user = db.execute_and_fetch_one(
            "SELECT id, username, password_hash FROM users WHERE username = %s AND active = %s",
            username, True
        )

        if not user:
            raise UserDoesNotExistError("No matching accounts could be found for the provided username.")
        
        if check_password_hash(user[2], password):
            return {
                'id': user[0],
                'username': user[1]
            }
        else:
            raise PasswordDoesNotMatchError("The password entered was incorrect.")
        
    def update_username(self, user_id: str, username: str) -> bool:
        if self.validate_username(username):
            db.execute_and_commit(
                "UPDATE users SET username = %s WHERE id = %s",
                username, user_id
            )

            return True
        return False
    
    def update_password(self, user_id: str, curr_password: str, new_password: str) -> bool:
        curr_password_hash = db.execute_and_fetch_one(
            "SELECT password_hash FROM users WHERE id = %s",
            user_id
        )
        
        if check_password_hash(curr_password_hash[0], curr_password) and self.validate_password(new_password):
            password_hash = generate_password_hash(new_password)
            db.execute_and_commit(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                password_hash, user_id
            )

            return True
        else:
            raise PasswordDoesNotMatchError("The current password you entered is incorrect.")
        
    def delete_user(self, user_id:str) -> bool:
        # Get all associated analysis IDs with the user
        analyses = db.execute_and_fetch_all("SELECT id FROM analysis_history WHERE user_id = %s", user_id)

        # Deactivate their account
        deactivate = db.execute_and_commit(
            "UPDATE users SET active = %s WHERE id = %s",
            False, user_id
        )

        if not analyses and deactivate:
            return True

        # Delete their upload history
        db.execute_and_commit("DELETE FROM analysis_uploads WHERE analysis_id IN %s", analyses[0])

        if not deactivate:
            return False
        return True
        
    def validate_password(self, password:str) -> bool:
        if len(password) < 8:
            raise PasswordTooShortError("The provided password is too short. It must contain at least 8 or more characters.")
        return True
    
    def validate_same_password(self, password:str, same_password:str) -> bool:
        if same_password != password:
            raise PasswordDoesNotMatchError("Passwords do not match.")
        return True
    
    def validate_username(self, username:str) -> bool:
        if len(username) < 3:
            raise UsernameTooShortError("The provided username is too short. It must contain at least 4 or more characters.")
        
        user = db.execute_and_fetch_one(
            "SELECT id FROM users WHERE username  = %s;",
            username
            )
        if user is not None:
            raise UsernameAlreadyExistsError("A user with the given username already exists. Please choose a different one.")
        return True