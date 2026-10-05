# Design Your Own API — Your Response

* **Event Planner** - create events, manage RSVPs, send reminders

Create a design document that includes:

1. **Resources** - List all the things in your system (minimum 3 resources)
2. **Relationships** - How do they connect? (at least one one-to-many and identify any many-to-many)
3. **Endpoints** - Full CRUD for your primary resource, plus at least 3 endpoints for related resources. Include the HTTP method and URI for each.
4. **Schemas** - Request and response schemas for at least 2 POST endpoints and 2 GET endpoints
5. **Authentication** - Which endpoints are public? Which require login? Who can access what?
6. **Error responses** - For your most important endpoint, list all possible status codes and what they mean



Event Planner API Design

1. Resources

Users - people using the app

Events - events created by users

RSVPs - tracks who is attending an event

Reminders - reminders sent for events

2. Relationships

One User can create many Events → one-to-many

One Event can have many Reminders → one-to-many

Users can RSVP to many Events, and Events can have many Users → many-to-many through RSVPs

3. Endpoints

Events - Full CRUD

POST /events - Create an event

GET /events - Get all events

GET /events/{event_id} - Get one event

PUT /events/{event_id} - Update an event

PATCH /events/{event_id} - Change the location.

DELETE /events/{event_id} - Delete an event

Related Resources

POST /events/{event_id}/rsvps - RSVP to an event

GET /events/{event_id}/rsvps - Get RSVPs for an event

POST /events/{event_id}/reminders - Create a reminder

4. Schemas

POST /events

Request:

{
"title": "Birthday Party",
"date": "2026-10-20",
"location": "Los Angeles"
}

Response:

{
"id": 1,
"title": "Birthday Party",
"date": "2026-10-20",
"location": "Los Angeles"
}

POST /events/{event_id}/rsvps

Request:

{
"status": "attending"
}

Response:

{
"event_id": 1,
"user_id": 5,
"status": "attending"
}

GET /events

Response:

[
{
"id": 1,
"title": "Birthday Party",
"date": "2026-10-20",
"location": "Los Angeles"
}
]

GET /events/{event_id}

Response:

{
"id": 1,
"title": "Birthday Party",
"date": "2026-10-20",
"location": "Los Angeles"
}

5. Authentication

* GET /events - Public, anyone can view events
* GET /events/{event_id} - Public, anyone can view an event
* POST /events - Login required, any logged-in user can create an event
* PATCH /events/{event_id} - Login required, only the event creator can update it
* DELETE /events/{event_id} - Login required, only the event creator can delete it
* POST /events/{event_id}/rsvps - Login required, users can RSVP for themselves
* GET /events/{event_id}/rsvps - Login required, only the event creator can view the RSVP list
* POST /events/{event_id}/reminders - Login required, only the event creator can create reminders

6. Error Responses

For POST /events:

201 Created - Event was created successfully

400 Bad Request - Missing or invalid event data

401 Unauthorized - User is not logged in

403 Forbidden - User does not have permission

500 Internal Server Error - Something went wrong on the server
