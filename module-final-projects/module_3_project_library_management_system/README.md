# Library Management System

This is my Module 3 final project. I built a command-line library management program using Python, SQLite, and SQLAlchemy. The program stores information about books, authors, and library members. It also keeps track of book checkouts and returns.

## What the Program Does

The menu lets you:

- Add books, authors, and members.
- Search for books by title or author.
- View books, authors, members, and their IDs.
- Check out and return books.
- See a member's current checkouts.
- Find overdue books (more than 14 days old).
- Update a member's email address.
- Delete books and members that do not have borrowing history.
- View all borrowing records, including returned books.

The program also checks for common mistakes, such as entering an ID that does not exist, checking out a book with no available copies, or using an ISBN or email address that is already in the database.

## Files

- `main.py` — Runs the menu and asks the user for input.
- `models.py` — Defines the database tables and relationships.
- `crud.py` — Contains the functions for adding, reading, updating, and deleting records.
- `seed.py` — Adds missing sample records without overwriting existing data.
- `sample_data.json` — Contains the example books, authors, members, and borrowings.
- `requirements.txt` — Lists the Python package needed for the project.
- `library_erd.png` — Diagram of the database tables and relationships.
- `README.md` — Explains the project and how to run it.

The program uses `library.db` to store records. The included database has sample records for testing.

## How to Run the Project

Open a terminal in the project folder.

1. Install SQLAlchemy:

   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. If you want to load the example records, run:

   ```bash
   python3 seed.py
   ```

   Running this again is safe: existing records are preserved, and missing sample records are added without duplicates. The program also works without sample data, so this step is optional.
3. Start the menu:

   ```bash
   python3 main.py
   ```

   Enter a menu number and follow the prompts. The program shows the available IDs when you need to select a book, author, member, or borrowing.

On later runs, you can just use `python3 main.py`. The records stay saved in `library.db`.

**Reset warning:** Running `python3 seed.py --reset` and typing `RESET` deletes the existing database records and reloads the examples. Do not use it if you want to keep your current data.

## Database Tables and Relationships

I used five tables:

| Table            | Main columns                                                      | Purpose                                                        |
| ---------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- |
| `authors`      | id (PK), name, bio                                                | Stores author information.                                     |
| `books`        | id (PK), title, isbn (unique), year_published, available_copies   | Stores book information.                                       |
| `members`      | id (PK), name, email (unique), membership_date                    | Stores library members.                                        |
| `book_authors` | book_id (FK), author_id (FK)                                      | Connects books and authors. Both columns form the primary key. |
| `borrowings`   | id (PK), book_id (FK), member_id (FK), checkout_date, return_date | Records each checkout and return.                              |

PK means primary key, which identifies a record. FK means foreign key, which connects one table to another. 

### Database Relationships (ERD)

![Library database entity-relationship diagram](library_erd.png)

The diagram shows all five tables. `book_authors` connects books and authors (many-to-many). Each borrowing belongs to one book and one member, while books and members can each have multiple borrowing records (one-to-many).

A book can have multiple authors, and an author can write multiple books. The `book_authors` table connects them without repeating the same book information.

A book can also be checked out many times. I used a separate `borrowings` table because each checkout has its own member, checkout date, and return date. This allows the program to keep borrowing history even after a book is returned.

## How Checkouts and Returns Work

When a member checks out a book, the program checks that the book and member exist and that at least one copy is available. It then creates a borrowing record and subtracts one from the available copies.

When the book is returned, the program saves the return date and adds one back to the available copies. It also prevents the same borrowing from being returned twice.

## Testing

I tested the project using the sample data and checked the main features, including adding records, searching, checking out and returning books, and viewing borrowing history. I also checked cases such as duplicate ISBNs, invalid IDs, unavailable books, and trying to delete a record with borrowing history.

## One Thing I Had to Think Through

One design decision was whether to store borrowing information in the `books` table. I used a separate table because one book can have many checkouts over time. Keeping those records separate makes it easier to track both current borrowings and past returns.

## How to Demo the Program

Run `python3 main.py`, choose `8` to see all records, then `4` to check out an available book to a listed member. Use the borrowing ID returned by option `4` in option `5` to return it. Database records persist across restarts.
