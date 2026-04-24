# This module provides service functions for user authentication and management, including registration and login.

# The functions in this module interact with the database to perform operations related to user accounts, 
# such as retrieving user information, registering new users, and authenticating existing users.
from app.services.auth_service import (
    authenticate_user,
    get_user_by_email,
    register_user,
)
from app.services.resume_service import (
    create_resume,
    delete_resume,
    get_resume_by_id,
    list_resumes,
    update_resume,
)

__all__ = [
    "authenticate_user",
    "create_resume",
    "delete_resume",
    "get_resume_by_id",
    "get_user_by_email",
    "list_resumes",
    "register_user",
    "update_resume",
]
