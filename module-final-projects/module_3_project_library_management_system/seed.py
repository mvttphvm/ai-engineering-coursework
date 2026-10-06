"""
Module 3 Project: Library Management System
seed.py — Populate the database with sample data for testing.
"""

import json
from datetime import date
from pathlib import Path

from models import Base, engine, init_db
from crud import add_author, add_book, add_member, checkout_book, return_book


def seed():
    """Reset the database and load the sample data from sample_data.json."""
    Base.metadata.drop_all(engine)
    init_db()

    data_file = Path(__file__).with_name("sample_data.json")
    with open(data_file) as file:
        data = json.load(file)

    author_ids = {}
    for author_data in data["authors"]:
        author = add_author(author_data["name"], author_data.get("bio"))
        author_ids[author.name] = author.id

    books_by_isbn = {}
    for book_data in data["books"]:
        ids = [author_ids[name] for name in book_data["authors"]]
        book = add_book(
            book_data["title"],
            book_data["isbn"],
            book_data.get("year_published"),
            book_data.get("available_copies", 1),
            author_ids=ids,
        )
        books_by_isbn[book.isbn] = book.id

    members_by_email = {}
    for member_data in data["members"]:
        member = add_member(member_data["name"], member_data["email"])
        members_by_email[member.email] = member.id

    for borrowing_data in data["borrowings"]:
        borrowing = checkout_book(
            books_by_isbn[borrowing_data["book_isbn"]],
            members_by_email[borrowing_data["member_email"]],
            checkout_date=date.fromisoformat(borrowing_data["checkout_date"]),
        )

        if borrowing_data["return_date"]:
            return_book(
                borrowing.id,
                return_date=date.fromisoformat(borrowing_data["return_date"]),
            )

    print("Seed complete!")


if __name__ == "__main__":
    seed()
