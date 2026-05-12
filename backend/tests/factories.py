LONG_RESUME_CONTENT = (
    "Python FastAPI PostgreSQL Docker backend API development " * 10
).strip()

LONG_JD_CONTENT = (
    "Python FastAPI PostgreSQL Docker Kubernetes backend API development " * 10
).strip()


def user_payload(
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
) -> dict:
    return {
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def resume_payload(
    title: str = "Test Resume",
    content: str = LONG_RESUME_CONTENT,
) -> dict:
    return {
        "title": title,
        "content": content,
    }


def job_description_payload(
    title: str = "Backend Engineer",
    company: str | None = "Acme",
    role: str | None = "Senior",
    content: str = LONG_JD_CONTENT,
) -> dict:
    return {
        "title": title,
        "company": company,
        "role": role,
        "content": content,
    }


def analysis_raw_payload(
    resume_text: str = LONG_RESUME_CONTENT,
    jd_text: str = LONG_JD_CONTENT,
) -> dict:
    return {
        "resume_text": resume_text,
        "jd_text": jd_text,
    }
