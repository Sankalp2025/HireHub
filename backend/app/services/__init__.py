# This module provides service functions for user authentication and management, including registration and login.

# The functions in this module interact with the database to perform operations related to user accounts, 
# such as retrieving user information, registering new users, and authenticating existing users.
from app.services.auth_service import (
    
    authenticate_user,
    get_user_by_email,
    register_user,
    
)

__all__ = ["authenticate_user", "get_user_by_email", "register_user"]
