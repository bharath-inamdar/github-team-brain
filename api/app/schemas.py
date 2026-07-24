from pydantic import BaseModel, ConfigDict


class RepositoryCreate(BaseModel):
    """
    Schema used when creating a new repository.
    This represents the data sent by the client.
    """
    name: str
    owner: str


class RepositoryResponse(BaseModel):
    """
    Schema used when returning repository data to the client.
    """
    id: int
    name: str
    owner: str

    model_config = ConfigDict(from_attributes=True)