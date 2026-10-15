# Student Services Dashboard

INFS605 Assignment 2 microservices project.

## Services

- **Student Profile** stores and returns student information.
- **Course Catalogue** creates and returns course information.
- **Feedback** stores course feedback and checks the student and course first.
- **Notification** records a notification when feedback is submitted.
- **Admin Portal** provides the student interface.

Each service runs in its own Docker container and has its own database.

## Architecture

```text
Admin Portal ──> Student Profile ──> Student database

Postman ───────> Course Catalogue ─> Course database
   │
   ├───────────> Feedback ─────────> Feedback database
   │                 │
   │                 ├──> Student Profile
   │                 ├──> Course Catalogue
   │                 └──> Notification ──> Notification database
   │
   └───────────> Notification
```

## Run the system

From the project folder, run:

```bash
docker compose up --build
```

Open the Admin Portal at `http://localhost:3000`.

To stop the containers, press `Ctrl+C`.

## API endpoints

| Service | Port | Endpoints |
|---|---:|---|
| Student Profile | 5001 | `GET /students`, `GET /students/<id>` |
| Course Catalogue | 5002 | `POST /courses`, `GET /courses`, `GET /courses/<id>` |
| Feedback | 5003 | `POST /feedback`, `GET /feedback` |
| Notification | 5004 | `POST /notifications`, `GET /notifications` |


assignment-repo/
├── admin-frontend/
├── student-profile/
├── course-catalogue/
├── feedback/
├── notification/
├── postman/
├── screenshots/
├── docker-compose.yml
└── README.md

### Example requests

Create a course:

```json
{
  "code": "INFS605",
  "title": "Microservices",
  "description": "Course catalogue test"
}
```

Submit feedback:

```json
{
  "student_id": 4,
  "course_id": 1,
  "rating": 5,
  "comment": "Good course"
}
```

Create a notification:

```json
{
  "feedback_id": 1,
  "recipient": "student@example.com",
  "message": "Feedback received"
}
```

Feedback ratings must be from 1 to 5. Feedback is rejected if the student or course does not exist.

## Testing

The Postman collection is in `postman/INFS605 Assignment 2 UAT.postman_collection.json`.

The collection completed with **10 passed tests and 0 failed**. It checks successful requests, the Feedback-to-Notification flow, an invalid rating, and a missing student.

Example results:

- Creating feedback returned `201 Created` and `notification_recorded: true`.
- A rating of `6` returned `400 Bad Request`.
- A missing student returned `404 Not Found`.

The Postman run screenshot is in `screenshots/postman-uat-results.png`.