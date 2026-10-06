# Module 3 Project — 5-Minute Presentation

Before recording, run `python seed.py` once so the IDs match the demo below.

## 0:00–1:00 — ERD

SCREEN: Open `README.md` and scroll to the ERD.

SAY:

Hi, I'm Matt, and this is my Module 3 Library Management System project. My database has four main models: books, authors, members, and borrowings.

Books and authors have a many-to-many relationship because one book can have multiple authors and one author can write multiple books. I used the `book_authors` association table to connect them.

Borrowings connect books and members. One member can have many borrowing records, and one book can also have many borrowing records over time. Each individual borrowing belongs to one book and one member and stores the checkout date and return date.

DON'T SAY: Do not read every column in the ERD. Just point to the tables and relationships as you explain them.

## 1:00–3:30 — Live CLI Demo

SCREEN: Open the terminal and run `python main.py`.

### Add a book

Choose option `1` and enter:

- Title: `Python Basics`
- ISBN: `DEMO-001`
- Year: `2026`
- Available copies: `1`

SAY:

First I'll add a new book. The program stores the book in the SQLite database using SQLAlchemy.

The new book should be Book ID `6` if you ran `seed.py` immediately before the demo.

### Check it out

Choose option `4`.

Enter:

- Book ID: `6`
- Member ID: `2`

Member 2 is Bob Martinez in the seeded data.

SAY:

Now I'll check the book out to a member. When a checkout succeeds, the program creates a borrowing record and decreases the book's available copies by one.

The new Borrowing ID should be `7`. Remember that number for the return step.

### View the member's borrowings

Choose option `6` and enter Member ID `2`.

SAY:

Here I can see Bob's active borrowing. The query only returns borrowings where `return_date` is still NULL.

### Return the book

Choose option `5` and enter Borrowing ID `7`.

SAY:

When the book is returned, the program sets the return date and increases the book's available copies by one.

Optional if you have time: choose option `6` again and enter Member ID `2`. It should now say there are no active borrowings.

DON'T SAY: Do not demonstrate every menu option. The assignment only requires add, checkout, view, and return for the live demo.

## 3:30–4:30 — Design Decision

SCREEN: Open `models.py` and scroll to the `Borrowing` model.

SAY:

One design decision I made was using a separate Borrowing model instead of using a simple association table between books and members.

The relationship needs its own data, especially `checkout_date` and `return_date`, so making Borrowing a model makes it much easier to keep borrowing history and query current or overdue books.

I used a normal association table for books and authors because that relationship doesn't need extra information for this project.

DON'T SAY: You do not need to explain every SQLAlchemy line in the model.

## 4:30–5:00 — Hardest Challenge

SCREEN: Open `crud.py` and scroll to `checkout_book()` and `return_book()`.

SAY:

The hardest part was keeping the borrowing record and the available copy count consistent. A checkout has to create the borrowing and decrease the available copies, while a return has to update the same borrowing and increase the copies again.

I handled those changes in the same SQLAlchemy session and added checks so a book with zero copies can't be checked out and the same borrowing can't be returned twice.

That's my Library Management System project.

DON'T SAY: Don't get into SQLAlchemy internals unless the instructor asks a follow-up question.
