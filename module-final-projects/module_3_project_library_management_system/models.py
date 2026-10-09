"""
Module 3 Project: Library Management System
models.py — SQLAlchemy models and database setup
"""

from datetime import date
from pathlib import Path

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DB_PATH = Path(__file__).resolve().parent / "library.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


class Base(DeclarativeBase):
    pass


# Association table for the many-to-many relationship between books and authors.
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    books: Mapped[list["Book"]] = relationship(
        secondary=book_authors,
        back_populates="authors",
    )

    def __repr__(self):
        return f"Author(id={self.id}, name='{self.name}')"


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    membership_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    borrowings: Mapped[list["Borrowing"]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"Member(id={self.id}, name='{self.name}', email='{self.email}')"


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("available_copies >= 0", name="available_copies_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    isbn: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    year_published: Mapped[int | None] = mapped_column(Integer, nullable=True)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    authors: Mapped[list[Author]] = relationship(
        secondary=book_authors,
        back_populates="books",
    )
    borrowings: Mapped[list["Borrowing"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}', copies={self.available_copies})"


class Borrowing(Base):
    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    checkout_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    book: Mapped[Book] = relationship(back_populates="borrowings")
    member: Mapped[Member] = relationship(back_populates="borrowings")

    def __repr__(self):
        return (
            f"Borrowing(id={self.id}, book_id={self.book_id}, "
            f"member_id={self.member_id}, return_date={self.return_date})"
        )


def init_db():
    """Create all database tables if they do not already exist."""
    Base.metadata.create_all(engine)
