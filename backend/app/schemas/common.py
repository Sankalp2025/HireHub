from typing import Generic, TypeVar

from pydantic import BaseModel

# Common schemas for API responses, including generic response structures and error handling
T = TypeVar("T")


class APIError(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel, Generic[T]):
    data: T | None
    error: APIError | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
