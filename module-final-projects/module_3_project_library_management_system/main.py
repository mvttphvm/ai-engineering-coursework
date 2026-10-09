"""Interactive CLI for the library management system."""
from models import init_db
from crud import (
    add_author, add_book, add_member, checkout_book, delete_book, delete_member,
    find_books_by_author, list_authors, list_books, list_borrowings, list_members,
    list_member_borrowings, list_overdue_books, return_book, search_books_by_title,
    update_member_email,
)


def show_books(available_only=False):
    books = [b for b in list_books() if not available_only or b.available_copies > 0]
    print('\nBooks:')
    for b in books:
        print(f'  ID {b.id}: {b.title} | ISBN {b.isbn} | {b.available_copies} available')
    if not books:
        print('  None found.')
    return bool(books)


def show_members():
    members = list_members()
    print('\nMembers:')
    for m in members:
        print(f'  ID {m.id}: {m.name} | {m.email}')
    if not members:
        print('  None found.')
    return bool(members)


def show_authors():
    authors = list_authors()
    print('\nAuthors:')
    for a in authors:
        print(f'  ID {a.id}: {a.name}')
    if not authors:
        print('  None found.')
    return bool(authors)


def show_borrowings(active_only=True):
    borrowings = list_borrowings(active_only)
    print('\nActive borrowings:' if active_only else '\nBorrowing history:')
    for b in borrowings:
        print(f'  ID {b.id}: {b.book.title} | {b.member.name} | out {b.checkout_date} | returned {b.return_date or "NOT YET"}')
    if not borrowings:
        print('  None found.')
    return bool(borrowings)


def read_positive_id(value):
    value = value.strip()
    if not value.isdigit() or int(value) < 1:
        raise ValueError('Enter a positive numeric ID.')
    return int(value)


def read_id(prompt):
    return read_positive_id(input(prompt))


def add_book_ui():
    print("\nADD A NEW BOOK")
    print("Existing authors (optional):")
    show_authors()
    title = input('Title: ').strip()
    isbn = input('ISBN: ').strip()
    year = input('Year published (optional): ').strip()
    copies = input('Available copies (default 1): ').strip()
    ids = input('Author IDs, comma-separated (optional): ').strip()
    author_ids = [read_positive_id(x) for x in ids.split(',')] if ids else None
    book = add_book(title, isbn, int(year) if year else None, int(copies) if copies else 1, author_ids)
    print(f'Added book ID {book.id}: {book.title}')


def add_member_ui():
    member = add_member(input('Member name: '), input('Email: '))
    print(f'Added member ID {member.id}: {member.name}')


def add_author_ui():
    author = add_author(input('Author name: '), input('Bio (optional): '))
    print(f'Added author ID {author.id}: {author.name}')


def search_ui():
    mode = input('Search by (1) title or (2) author? ').strip()
    if mode == '1':
        books = search_books_by_title(input('Title contains: '))
    elif mode == '2':
        books = find_books_by_author(input('Author name contains: '))
    else:
        print('Invalid search option.')
        return
    if not books:
        print('No matching books.')
    for b in books:
        print(f'  ID {b.id}: {b.title} | ISBN {b.isbn} | {b.available_copies} available')


def checkout_ui():
    if not show_books(available_only=True): return
    if not show_members(): return
    borrowing = checkout_book(read_id('Book ID: '), read_id('Member ID: '))
    print(f'Checked out successfully. Borrowing ID {borrowing.id}')


def return_ui():
    if not show_borrowings(): return
    borrowing = return_book(read_id('Borrowing ID to return: '))
    print(f'Returned borrowing ID {borrowing.id}')


def member_borrowings_ui():
    if not show_members(): return
    member_id = read_id('Member ID: ')
    if member_id not in {m.id for m in list_members()}:
        raise ValueError('Member not found.')
    borrowings = list_member_borrowings(member_id)
    if not borrowings:
        print('No active borrowings for that member.')
    for b in borrowings:
        print(f'  Borrowing ID {b.id}: {b.book.title} | checked out {b.checkout_date}')


def overdue_ui():
    borrowings = list_overdue_books()
    if not borrowings:
        print('No overdue books.')
    for b in borrowings:
        print(f'  Borrowing ID {b.id}: {b.book.title} | {b.member.name} | checked out {b.checkout_date}')


def update_email_ui():
    if not show_members(): return
    member = update_member_email(read_id('Member ID: '), input('New email: '))
    print(f'Updated member ID {member.id}: {member.email}')


def delete_book_ui():
    if not show_books(): return
    book_id = read_id('Book ID to delete: ')
    if input(f'Type DELETE to permanently delete book ID {book_id}: ').strip() != 'DELETE':
        print('Cancelled.')
        return
    delete_book(book_id)
    print('Book deleted.')


def delete_member_ui():
    if not show_members(): return
    member_id = read_id('Member ID to delete: ')
    if input(f'Type DELETE to permanently delete member ID {member_id}: ').strip() != 'DELETE':
        print('Cancelled.')
        return
    delete_member(member_id)
    print('Member deleted.')


def show_all_records():
    show_books()
    show_members()
    show_authors()
    show_borrowings()


def show_full_history():
    show_borrowings(active_only=False)


MENU = {
    '1': ('Add book', add_book_ui),
    '2': ('Add member', add_member_ui),
    '3': ('Search books by title or author', search_ui),
    '4': ('Check out book', checkout_ui),
    '5': ('Return book', return_ui),
    '6': ('View member active borrowings', member_borrowings_ui),
    '7': ('View overdue books', overdue_ui),
    '8': ('View all books, members, authors, and active borrowings', show_all_records),
    '9': ('Add author', add_author_ui),
    '10': ('Update member email', update_email_ui),
    '11': ('Delete book', delete_book_ui),
    '12': ('Delete member', delete_member_ui),
    '13': ('View full borrowing history', show_full_history),
}


def main():
    init_db()
    while True:
        print('\nLIBRARY MANAGEMENT SYSTEM')
        for key, (name, _) in MENU.items():
            print(f'{key}. {name}')
        print('0. Exit')
        try:
            choice = input('Choose an option: ').strip()
            if choice == '0':
                print('Goodbye!')
                return
            if choice not in MENU:
                print('Invalid menu choice.')
                continue
            MENU[choice][1]()
        except (ValueError, EOFError, KeyboardInterrupt) as exc:
            if isinstance(exc, (EOFError, KeyboardInterrupt)):
                print('\nGoodbye!')
                return
            print(f'Error: {exc}')


if __name__ == '__main__':
    main()
