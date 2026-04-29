# This module provides service functions for user authentication and management, including registration and login.

# The functions in this module interact with the database to perform operations related to user accounts, 
# such as retrieving user information, registering new users, and authenticating existing users.
from app.services.auth_service import (
    authenticate_user,
    get_user_by_email,
    register_user,
)
from app.services.analysis_service import (
    AnalysisInputError,
    AnalysisResourceNotFoundError,
    create_analysis,
    get_analysis_by_id,
    list_analyses,
)
from app.services.job_description_service import (
    create_job_description,
    delete_job_description,
    get_job_description_by_id,
    list_job_descriptions,
    update_job_description,
)
from app.services.resume_service import (
    create_resume,
    delete_resume,
    get_resume_by_id,
    list_resumes,
    update_resume,
)

__all__ = [
    "AnalysisInputError",
    "AnalysisResourceNotFoundError",
    "authenticate_user",
    "create_analysis",
    "create_job_description",
    "create_resume",
    "delete_job_description",
    "delete_resume",
    "get_analysis_by_id",
    "get_job_description_by_id",
    "get_resume_by_id",
    "get_user_by_email",
    "list_analyses",
    "list_job_descriptions",
    "list_resumes",
    "register_user",
    "update_job_description",
    "update_resume",
]
