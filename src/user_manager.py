from .utils.database_config import db
from.utils.errors import PasswordTooShortError, InvalidUsername, UsernameAlreadyExistsError, UsernameTooShortError, UserDoesNotExist
from werkzeug.security import generate_password_hash, check_password_hash

import datetime;

class UserManager:
    def __init__(self):
        print("→ insitialized User Manager ←")

    def get_all_users(self) -> bool | dict:
        users = db.execute_and_fetch_all(
            "SELECT id, username, active FROM users WHERE active = %s;",
            (True,)
            )
        
        if not users:
            return False
        return users
    
    def get_user(self, username: str) -> bool | dict:
        user = db.execute_and_fetch_one(
            "SELECT id, username, active FROM users WHERE active = %s AND username = %s;", 
            True, username
        )
        
        if not user:
            raise UserDoesNotExist("No matching accounts could be found for the provided username.")
        return user
    
    def register_user(self, username: str, password: str) -> bool:
        
        # Complete all input validation checks first
        if self.validate_password(password) and self.validate_username(username):
            password_hash = generate_password_hash(password)
            timestamp = datetime.datetime.now()
            db.execute_and_commit(
                "INSERT INTO users (username, password_hash, creation_timestamp, active) VALUES (%s, %s, %s, %s)",
                username, password_hash, timestamp, True
                )

            print(f"User {username} inserted at {timestamp}.")
            return True
    
    def login_user(self, username: str, password: str) -> bool | dict:
        user = db.execute_and_fetch_one(
            "SELECT id, username, password_hash FROM users WHERE username = %s AND active = %s",
            username, True
        )

        if not user:
            raise UserDoesNotExist("No matching accounts could be found for the provided username.")
        
        if check_password_hash(user[2], password):
            return {
                'id': user[0],
                'username': user[1]
            }
        else:
            return False
        
    def delete_user(self, user_id:str) -> bool:
        deactivate = db.execute_and_commit(
            "UPDATE users SET active = %s WHERE id = %s",
            False, user_id
        )

        if not deactivate:
            return False
        return True
        
    def validate_password(self, password:str) -> bool:
        if len(password) < 8:
            raise PasswordTooShortError("The provided password is too short. It must contain at least 8 or more characters.")
        return True
    
    def validate_username(self, username:str) -> bool:
        if len(username) < 3:
            raise UsernameTooShortError("The provided username is too short. It must contain at least 8 or more characters.")
        
        user = db.execute_and_fetch_one(
            "SELECT id FROM users WHERE username  = %s;",
            username
            )
        if user is not None:
            raise UsernameAlreadyExistsError("A user with the given username already exists. Please choose a different one.")
        return True