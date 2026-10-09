"""Safely add missing sample data without deleting existing library records."""
import json
from datetime import date
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Base, engine, init_db, Author, Book, Member, Borrowing
from crud import add_author, add_book, add_member, checkout_book, return_book


def seed(reset=False):
    if reset:
        Base.metadata.drop_all(engine)
    init_db()
    data = json.loads(Path(__file__).with_name('sample_data.json').read_text(encoding='utf-8'))
    with Session(engine) as session:
        authors = {a.name: a.id for a in session.scalars(select(Author))}
        books = {b.isbn: b.id for b in session.scalars(select(Book))}
        members = {m.email.lower(): m.id for m in session.scalars(select(Member))}

    for item in data['authors']:
        if item['name'] not in authors:
            authors[item['name']] = add_author(item['name'], item.get('bio')).id

    for item in data['books']:
        if item['isbn'] not in books:
            books[item['isbn']] = add_book(
                item['title'], item['isbn'], item.get('year_published'),
                item.get('available_copies', 1),
                [authors[name] for name in item['authors']]
            ).id

    for item in data['members']:
        email = item['email'].strip().lower()
        if email not in members:
            members[email] = add_member(item['name'], email).id

    for item in data['borrowings']:
        book_id = books[item['book_isbn']]
        member_id = members[item['member_email'].strip().lower()]
        checkout_date = date.fromisoformat(item['checkout_date'])
        return_date = date.fromisoformat(item['return_date']) if item['return_date'] else None
        with Session(engine) as session:
            exists = session.scalar(select(Borrowing.id).where(
                Borrowing.book_id == book_id,
                Borrowing.member_id == member_id,
                Borrowing.checkout_date == checkout_date,
            ).limit(1)) is not None
        if not exists:
            borrowing = checkout_book(book_id, member_id, checkout_date=checkout_date)
            if return_date:
                return_book(borrowing.id, return_date=return_date)
    print('Seed complete! Existing records preserved; missing sample records added.')


if __name__ == '__main__':
    import sys
    if '--reset' in sys.argv:
        if input('This DELETES all existing library data. Type RESET to continue: ').strip() != 'RESET':
            print('Cancelled.')
            sys.exit(0)
        seed(reset=True)
    else:
        seed()
