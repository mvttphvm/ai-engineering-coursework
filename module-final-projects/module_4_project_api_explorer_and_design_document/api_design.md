
# Module 4 Project — Part 2: Study Tracker API Design

**Your Name:** Matt Pham
**Date:** October 6, 2026

---

## Application Description

Study Tracker is an app that helps students track how much time they spend studying for different courses. Students can log study sessions, set weekly study goals for each course, and view their progress toward those goals.

---

## Section 1 — Resources

| Resource       | Key Attributes                                                                                                             |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Students       | id (integer), name (string), email (string)                                                                                |
| Courses        | id (integer), name (string), code (string)                                                                                 |
| Study Sessions | id (integer), student_id (integer), course_id (integer), duration_minutes (integer), notes (string), studied_at (datetime) |
| Goals          | id (integer), student_id (integer), course_id (integer), target_hours (integer), active (boolean)                          |

---

## Section 2 — Relationships

- Student ↔ Course: A student can take many courses, and a course can have many students. Many-to-many.
- Student ↔ Study Session: A student can have many study sessions, but each session belongs to one student. This is one-to-many.
- Course ↔ Study Session: A course can have many study sessions, but each session belongs to one course. This is one-to-many.
- Student ↔ Goal: A student can have many goals, but each goal belongs to one student. One-to-many.
- Course ↔ Goal: A course can have many goals, but each goal belongs to one course. One-to-many.

---

## Section 3 — Endpoints

| Method | URI                                | Purpose                   | Auth |
| ------ | ---------------------------------- | ------------------------- | ---- |
| POST   | `/students`                      | Register student          | No   |
| GET    | `/students/{id}`                 | Get student               | Yes  |
| GET    | `/courses`                       | Get courses               | No   |
| GET    | `/courses/{id}`                  | Get one course            | No   |
| GET    | `/study_sessions`                | Get user's sessions       | Yes  |
| GET    | `/study_sessions/{id}`           | Get one session           | Yes  |
| POST   | `/study_sessions`                | Create session            | Yes  |
| PUT    | `/study_sessions/{id}`           | Update session            | Yes  |
| DELETE | `/study_sessions/{id}`           | Delete session            | Yes  |
| GET    | `/study_sessions?course_id={id}` | Filter sessions by course | Yes  |
| POST   | `/goals`                         | Create weekly goal        | Yes  |
| GET    | `/students/{id}/progress`        | View goal progress        | Yes  |

---

## Section 4 — Request/Response Schemas

### POST /study_sessions — Create a New Session

**Request body:**

```json
{
  "course_id": 3,
  "duration_minutes": 90,
  "notes": "Studied REST APIs",
  "studied_at": "2026-10-05T14:30:00"
}
```

**Data types:**

- course_id: integer
- duration_minutes: integer
- notes: string
- studied_at: datetime

**Success response — 201 Created:**

```json
{
  "id": 42,
  "student_id": 7,
  "course_id": 3,
  "duration_minutes": 90,
  "notes": "Studied REST APIs",
  "studied_at": "2026-10-05T14:30:00"
}
```

---

### POST /goals — Create a Weekly Goal

**Request body:**

```json
{
  "course_id": 3,
  "target_hours": 8,
  "active": true
}
```

**Data types:**

- course_id: integer
- target_hours: integer
- active: boolean

**Success response — 201 Created:**

```json
{
  "id": 12,
  "student_id": 7,
  "course_id": 3,
  "target_hours": 8,
  "active": true
}
```

---

### GET /study_sessions — Get Study Sessions

**Response — 200 OK:**

```json
[
  {
    "id": 42,
    "student_id": 7,
    "course_id": 3,
    "duration_minutes": 90,
    "notes": "Studied REST APIs",
    "studied_at": "2026-10-05T14:30:00"
  },
  {
    "id": 43,
    "student_id": 7,
    "course_id": 2,
    "duration_minutes": 60,
    "notes": "Reviewed database concepts",
    "studied_at": "2026-10-06T10:00:00"
  }
]
```

**Data types:**

- response: array
- id: integer
- student_id: integer
- course_id: integer
- duration_minutes: integer
- notes: string
- studied_at: datetime

---

### GET `/students/{id}/progress` — View Goal Progress

**Response — 200 OK:**

```json
{
  "student_id": 7,
  "course_id": 3,
  "course_name": "Web Development",
  "target_hours": 8,
  "completed_minutes": 360,
  "completed_hours": 6,
  "goal_met": false
}
```

**Data types:**

- student_id: integer
- course_id: integer
- course_name: string
- target_hours: integer
- completed_minutes: integer
- completed_hours: integer
- goal_met: boolean

---

## Section 5 — Authentication

### Authentication Method

The API will use **JWT authentication**.

After a student logs in successfully, the server gives the client a JWT access token. The client sends that token with protected requests in the Authorization header.

Example:

```text
Authorization: Bearer <token>
```

### Public Endpoints

The following endpoints can be accessed without authentication:

- POST /students — create/register a student account
- GET /courses — view available courses
- GET /courses/{id} — view a specific course

### Protected Endpoints

Authentication is required for:

- Student account information
- Study sessions
- Study goals
- Progress information
- Creating or modifying protected resources

### Authorization Rules

- Students may create and view their own study sessions.
- Students may only update or delete study sessions they own.
- Students may create and manage their own goals.
- Students may only view their own progress information.

Example:

A student with ID 7 should not be allowed to delete a study session belonging to student ID 12.

The API should return **403 Forbidden** when an authenticated user tries to access a resource they do not have permission to modify.

---

## Section 6 — Error Responses for POST /study_sessions

| Status Code               | Meaning                                                                  |
| ------------------------- | ------------------------------------------------------------------------ |
| 201 Created               | Study session was successfully created                                   |
| 400 Bad Request           | Request is malformed or contains invalid values                          |
| 401 Unauthorized          | User is not logged in or JWT is missing/invalid                          |
| 403 Forbidden             | User is authenticated but does not have permission to perform the action |
| 404 Not Found             | Referenced course does not exist                                         |
| 422 Unprocessable Entity  | Required fields are missing or have incorrect data types                 |
| 500 Internal Server Error | Unexpected server-side error occurred                                    |

### Examples

**400 Bad Request**

```json
{
  "error": "duration_minutes must be greater than 0"
}
```

**401 Unauthorized**

```json
{
  "error": "Authentication required"
}
```

**404 Not Found**

```json
{
  "error": "Course not found"
}
```

**422 Unprocessable Entity**

```json
{
  "error": "course_id must be an integer"
}
```

---

## Summary

The Study Tracker API uses REST-style resources and HTTP methods to let students manage courses, study sessions, and weekly goals.

JWT authentication protects student data, filtering allows clients to retrieve specific study sessions, and standard HTTP status codes communicate successful and failed requests.
