class Paper(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    publication_date: str
    journal: str
    doi: str
    url: str