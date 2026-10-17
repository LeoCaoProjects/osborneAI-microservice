import os

import psycopg2
import requests
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Use the other services compose names
STUDENT_PROFILE_URL = os.getenv("STUDENT_PROFILE_URL", "http://student-profile:5001")
COURSE_CATALOGUE_URL = os.getenv("COURSE_CATALOGUE_URL", "http://course-catalogue:5002")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://notification:5004")


def get_connection():
    # Read the deedback database address from docker compose
    return psycopg2.connect(os.environ["DATABASE_URL"])


@app.route("/feedback", methods=["GET"])
def get_feedback():
    # Get all saved feedback from this services database
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, student_id, course_id, rating, comment, created_at
            FROM feedback
            ORDER BY id
            """
        )
        feedback_records = cursor.fetchall()

        return jsonify(feedback_records), 200

    except psycopg2.Error:
        app.logger.exception("Could not get feedback")
        return jsonify({"error": "Could not get feedback"}), 503

    finally:
        # Close the database after the request
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.route("/feedback", methods=["POST"])
def create_feedback():
    # Read the feedback details from the request
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    required_fields = ("student_id", "course_id", "rating", "comment")
    if not all(field in data for field in required_fields):
        return jsonify(
            {"error": "student_id, course_id, rating, and comment are required"}
        ), 400

    student_id = data["student_id"]
    course_id = data["course_id"]
    rating = data["rating"]
    comment = data["comment"]

    # Check that the ids and rating are numbers with valid values
    if not isinstance(student_id, int) or student_id < 1:
        return jsonify({"error": "student_id must be a positive number"}), 400

    if not isinstance(course_id, int) or course_id < 1:
        return jsonify({"error": "course_id must be a positive number"}), 400

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "rating must be a number from 1 to 5"}), 400

    if not isinstance(comment, str) or not comment.strip():
        return jsonify({"error": "comment must contain text"}), 400

    # Ask student profile and course catalogue to check these records
    try:
        student_response = requests.get(
            f"{STUDENT_PROFILE_URL}/students/{student_id}",
            timeout=3,
        )
        course_response = requests.get(
            f"{COURSE_CATALOGUE_URL}/courses/{course_id}",
            timeout=3,
        )
    except requests.RequestException:
        return jsonify({"error": "A student or course service is unavailable"}), 503

    if student_response.status_code == 404:
        return jsonify({"error": "Student was not found"}), 404

    if course_response.status_code == 404:
        return jsonify({"error": "Course was not found"}), 404

    if not student_response.ok or not course_response.ok:
        return jsonify({"error": "Could not check the student or course"}), 503

    student = student_response.json()
    course = course_response.json()

    # Save the feedback in feedbacks own database
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO feedback (student_id, course_id, rating, comment)
            VALUES (%s, %s, %s, %s)
            RETURNING id, student_id, course_id, rating, comment, created_at
            """,
            (student_id, course_id, rating, comment.strip()),
        )
        saved_feedback = cursor.fetchone()
        connection.commit()

    except psycopg2.Error:
        app.logger.exception("Could not save feedback")
        return jsonify({"error": "Could not save feedback"}), 503

    finally:
        # Close the database resources after saving
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

    # Ask notification to record a message for the student
    notification_recorded = False

    try:
        notification_response = requests.post(
            f"{NOTIFICATION_URL}/notifications",
            json={
                "feedback_id": saved_feedback["id"],
                "recipient": student["email"],
                "message": f"Feedback received for {course['title']}.",
            },
            timeout=3,
        )
        notification_recorded = notification_response.status_code == 201
    except requests.RequestException:
        # Feedback is saved even if notification is temporarily unavailable
        app.logger.warning("Could not reach the Notification service")

    # Report whether the separate notification request succeeded
    result = dict(saved_feedback)
    result["notification_recorded"] = notification_recorded

    return jsonify(result), 201


if __name__ == "__main__":
    # Listen on the containers network interface on port 5003.
    app.run(host="0.0.0.0", port=5003, debug=True)
