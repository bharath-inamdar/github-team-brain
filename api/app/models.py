from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)

    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)

    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)

    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)

    default_branch = Column(String, nullable=False)

    # One repository can have many issues
    issues = relationship(
        "Issue",
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False,
    )

    github_issue_number = Column(Integer, nullable=False)

    title = Column(String, nullable=False)

    body = Column(Text, nullable=True)

    state = Column(String, nullable=False)

    author = Column(String, nullable=False)

    repository = relationship(
        "Repository",
        back_populates="issues",
    )