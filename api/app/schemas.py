from pydantic import BaseModel


class RepositoryCreate(BaseModel):
    name: str
    owner: str