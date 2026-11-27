from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


Paging = Annotated[PageParams, Depends(page_params)]
