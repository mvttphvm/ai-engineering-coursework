"""
Module 3 Project: Library Management System
main.py — Command-line interface
"""

from models import init_db
from crud import (
    add_book,
    add_member,
    checkout_book,
    return_book,
    list_books,
    search_books_by_title,
    list_member_borrowings,
    list_overdue_books,
)


def handle_add_book():
    """Prompt for book details and add to the database."""
    title = input("Title: ").strip()
    isbn = input("ISBN: ").strip()
    year_text = input("Year published (press Enter if unknown): ").strip()
    copies_text = input("Available copies: ").strip()

    try:
        year_published = int(year_text) if year_text else None
        available_copies = int(copies_text)
        book = add_book(title, isbn, year_published, available_copies)
        print(f"Added book #{book.id}: {book.title}")
    except ValueError as error:
        print("Error:", error)


def handle_add_member():
    """Prompt for member details and register in the database."""
    name = input("Member name: ").strip()
    email = input("Email: ").strip()

    try:
        member = add_member(name, email)
        print(f"Added member #{member.id}: {member.name}")
    except ValueError as error:
        print("Error:", error)


def handle_search_books():
    """Prompt for a search term and display matching books."""
    search_term = input("Search title: ").strip()
    books = search_books_by_title(search_term)

    if not books:
        print("No matching books found.")
        return

    for book in books:
        print(
            f"ID: {book.id} | {book.title} | ISBN: {book.isbn} | "
            f"Available: {book.available_copies}"
        )


def handle_checkout():
    """Prompt for book ID and member ID, then check out the book."""
    books = list_books()

    print("\nBooks:")
    for book in books:
        print(f"{book.id}. {book.title} - {book.available_copies} available")

    try:
        book_id = int(input("Book ID: ").strip())
        member_id = int(input("Member ID: ").strip())
        borrowing = checkout_book(book_id, member_id)
        print(f"Book checked out. Borrowing ID: {borrowing.id}")
    except ValueError as error:
        print("Error:", error)


def handle_return():
    """Prompt for a borrowing ID and return the book."""
    try:
        borrowing_id = int(input("Borrowing ID: ").strip())
        borrowing = return_book(borrowing_id)
        print(f"Borrowing #{borrowing.id} returned successfully.")
    except ValueError as error:
        print("Error:", error)


def handle_member_borrowings():
    """Display all active borrowings for a member."""
    try:
        member_id = int(input("Member ID: ").strip())
    except ValueError:
        print("Error: Member ID must be a number.")
        return

    borrowings = list_member_borrowings(member_id)

    if not borrowings:
        print("No active borrowings found for that member.")
        return

    for borrowing in borrowings:
        print(
            f"Borrowing ID: {borrowing.id} | "
            f"Book: {borrowing.book.title} | "
            f"Checked out: {borrowing.checkout_date}"
        )


def handle_overdue():
    """Display all overdue borrowings."""
    borrowings = list_overdue_books()

    if not borrowings:
        print("No overdue books found.")
        return

    for borrowing in borrowings:
        print(
            f"Borrowing ID: {borrowing.id} | "
            f"Book: {borrowing.book.title} | "
            f"Member: {borrowing.member.name} | "
            f"Checked out: {borrowing.checkout_date}"
        )


def main():
    init_db()

    while True:
        print("\n📚 Library Management System")
        print("1. Add a book")
        print("2. Add a member")
        print("3. Search books")
        print("4. Check out a book")
        print("5. Return a book")
        print("6. View member's borrowings")
        print("7. View overdue books")
        print("8. Exit")

        choice = input("\nChoose an option (1-8): ").strip()

        if choice == "1":
            handle_add_book()
        elif choice == "2":
            handle_add_member()
        elif choice == "3":
            handle_search_books()
        elif choice == "4":
            handle_checkout()
        elif choice == "5":
            handle_return()
        elif choice == "6":
            handle_member_borrowings()
        elif choice == "7":
            handle_overdue()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-8.")


if __name__ == "__main__":
    main()
