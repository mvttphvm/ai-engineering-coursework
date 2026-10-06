"""
Module 3 Project: Library Management System
crud.py — Create, Read, Update, Delete operations
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from models import engine, Book, Author, Member, Borrowing


# ──────────────────────────────────────────
# CREATE
# ──────────────────────────────────────────

def add_book(title: str, isbn: str, year_published: int = None,
             available_copies: int = 1, author_ids: list[int] = None):
    """Add a new book to the database. Returns the created Book object."""
    if not title.strip():
        raise ValueError("Title cannot be blank.")
    if not isbn.strip():
        raise ValueError("ISBN cannot be blank.")
    if available_copies < 0:
        raise ValueError("Available copies cannot be negative.")

    with Session(engine, expire_on_commit=False) as session:
        try:
            book = Book(
                title=title.strip(),
                isbn=isbn.strip(),
                year_published=year_published,
                available_copies=available_copies,
            )

            if author_ids:
                authors = list(
                    session.scalars(select(Author).where(Author.id.in_(author_ids)))
                )
                if len(authors) != len(set(author_ids)):
                    raise ValueError("One or more author IDs were not found.")
                book.authors = authors

            session.add(book)
            session.commit()
            return book
        except IntegrityError:
            session.rollback()
            raise ValueError("A book with that ISBN already exists.")


def add_author(name: str, bio: str = None):
    """Add a new author. Returns the created Author object."""
    if not name.strip():
        raise ValueError("Author name cannot be blank.")

    with Session(engine, expire_on_commit=False) as session:
        try:
            author = Author(name=name.strip(), bio=bio.strip() if bio else None)
            session.add(author)
            session.commit()
            return author
        except SQLAlchemyError:
            session.rollback()
            raise ValueError("Could not add the author.")


def add_member(name: str, email: str):
    """
    Register a new member with today's date as membership_date.
    Returns the created Member object.
    """
    if not name.strip():
        raise ValueError("Member name cannot be blank.")
    if not email.strip() or "@" not in email:
        raise ValueError("Please enter a valid email address.")

    with Session(engine, expire_on_commit=False) as session:
        try:
            member = Member(
                name=name.strip(),
                email=email.strip().lower(),
                membership_date=date.today(),
            )
            session.add(member)
            session.commit()
            return member
        except IntegrityError:
            session.rollback()
            raise ValueError("A member with that email already exists.")


def checkout_book(book_id: int, member_id: int, checkout_date: date = None):
    """
    Check out a book to a member.
    Decrements available_copies by 1 and sets checkout_date.
    Raises ValueError if the book is unavailable or IDs are invalid.
    Returns the created Borrowing object.
    """
    with Session(engine, expire_on_commit=False) as session:
        book = session.get(Book, book_id)
        member = session.get(Member, member_id)

        if book is None:
            raise ValueError("Book not found.")
        if member is None:
            raise ValueError("Member not found.")
        if book.available_copies <= 0:
            raise ValueError("That book has no available copies.")

        borrowing = Borrowing(
            book=book,
            member=member,
            checkout_date=checkout_date or date.today(),
        )
        book.available_copies -= 1

        try:
            session.add(borrowing)
            session.commit()
            return borrowing
        except SQLAlchemyError:
            session.rollback()
            raise ValueError("Could not check out the book.")


# ──────────────────────────────────────────
# READ
# ──────────────────────────────────────────

def list_books():
    """Return a list of all Book objects."""
    with Session(engine) as session:
        return list(session.scalars(select(Book).order_by(Book.title)))


def search_books_by_title(title: str):
    """Return books whose title contains the given string (case-insensitive)."""
    with Session(engine) as session:
        stmt = select(Book).where(Book.title.ilike(f"%{title.strip()}%"))
        return list(session.scalars(stmt.order_by(Book.title)))


def find_books_by_author(author_name: str):
    """Return all books associated with an author whose name contains author_name."""
    with Session(engine) as session:
        stmt = (
            select(Book)
            .join(Book.authors)
            .where(Author.name.ilike(f"%{author_name.strip()}%"))
            .options(selectinload(Book.authors))
            .distinct()
            .order_by(Book.title)
        )
        return list(session.scalars(stmt))


def list_member_borrowings(member_id: int):
    """Return all active (unreturned) Borrowing objects for the given member."""
    with Session(engine) as session:
        stmt = (
            select(Borrowing)
            .where(
                Borrowing.member_id == member_id,
                Borrowing.return_date.is_(None),
            )
            .options(selectinload(Borrowing.book))
            .order_by(Borrowing.checkout_date)
        )
        return list(session.scalars(stmt))


def list_overdue_books(days: int = 14):
    """
    Return Borrowing objects where return_date is NULL and
    checkout_date is more than `days` days ago.
    """
    cutoff_date = date.today() - timedelta(days=days)

    with Session(engine) as session:
        stmt = (
            select(Borrowing)
            .where(
                Borrowing.return_date.is_(None),
                Borrowing.checkout_date < cutoff_date,
            )
            .options(
                selectinload(Borrowing.book),
                selectinload(Borrowing.member),
            )
            .order_by(Borrowing.checkout_date)
        )
        return list(session.scalars(stmt))


# ──────────────────────────────────────────
# UPDATE
# ──────────────────────────────────────────

def return_book(borrowing_id: int, return_date: date = None):
    """
    Mark a borrowing as returned.
    Sets return_date and increments book.available_copies by 1.
    Raises ValueError if the borrowing is not found or already returned.
    """
    with Session(engine, expire_on_commit=False) as session:
        borrowing = session.get(Borrowing, borrowing_id)

        if borrowing is None:
            raise ValueError("Borrowing not found.")
        if borrowing.return_date is not None:
            raise ValueError("That book has already been returned.")

        borrowing.return_date = return_date or date.today()
        borrowing.book.available_copies += 1

        try:
            session.commit()
            return borrowing
        except SQLAlchemyError:
            session.rollback()
            raise ValueError("Could not return the book.")


def update_member_email(member_id: int, new_email: str):
    """Update the email address for a member. Returns the updated Member object."""
    if not new_email.strip() or "@" not in new_email:
        raise ValueError("Please enter a valid email address.")

    with Session(engine, expire_on_commit=False) as session:
        member = session.get(Member, member_id)
        if member is None:
            raise ValueError("Member not found.")

        try:
            member.email = new_email.strip().lower()
            session.commit()
            return member
        except IntegrityError:
            session.rollback()
            raise ValueError("A member with that email already exists.")


# ──────────────────────────────────────────
# DELETE
# ──────────────────────────────────────────

def delete_book(book_id: int):
    """
    Delete a book from the database.
    Raises ValueError if the book has any active (unreturned) borrowings.
    """
    with Session(engine) as session:
        book = session.get(Book, book_id)
        if book is None:
            raise ValueError("Book not found.")

        active = session.scalar(
            select(Borrowing).where(
                Borrowing.book_id == book_id,
                Borrowing.return_date.is_(None),
            )
        )
        if active:
            raise ValueError("Cannot delete a book that is currently borrowed.")

        try:
            session.delete(book)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise ValueError("Could not delete the book.")


def delete_member(member_id: int):
    """
    Delete a member from the database.
    Raises ValueError if the member has any active (unreturned) borrowings.
    """
    with Session(engine) as session:
        member = session.get(Member, member_id)
        if member is None:
            raise ValueError("Member not found.")

        active = session.scalar(
            select(Borrowing).where(
                Borrowing.member_id == member_id,
                Borrowing.return_date.is_(None),
            )
        )
        if active:
            raise ValueError("Cannot delete a member with active borrowings.")

        try:
            session.delete(member)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise ValueError("Could not delete the member.")
