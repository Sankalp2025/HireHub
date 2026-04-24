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

# A generic schema for paginated responses, which includes the list of items, total count, pagination details, and flags for next/previous pages
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
