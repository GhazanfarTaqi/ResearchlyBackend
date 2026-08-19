from typing import TypedDict

class Paper(TypedDict):
    title: str
    year: int
    doi:str
    citations:int
    url:str
    abstract:str
    authors:list
    local_path:str


