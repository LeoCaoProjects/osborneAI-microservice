import os

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_connection():
    # Read the database address from the environment setting in Compose
    return psycopg2.connect(os.environ["DATABASE_URL"])


def course_from_row(row):
    # Turn one database row into a named JSON object
    return {
        "id": row[0],
        "code": row[1],
        "title": row[2],
        "description": row[3],
    }


@app.route("/courses", methods=["POST"])
def add_course():
    # Read the course details sent in the request
    data = request.get_json(silent=True)

    # The request must contain a JSON object
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    # Get the fields, removing spaces from the start and end
    code = data.get("code", "").strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    # A course needs both a code and a title
    if not code or not title:
        return jsonify({"error": "code and title are required"}), 400

    # Keep values within the limits set in init.sql
    if len(code) > 20 or len(title) > 200:
        return jsonify({"error": "code or title is too long"}), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # safely insert the values as data
            cursor.execute(
                """
                INSERT INTO courses (code, title, description)
                VALUES (%s, %s, %s)
                RETURNING id, code, title, description
                """,
                (code, title, description),
            )

            # returns the new course so we can send it back
            course = course_from_row(cursor.fetchone())

        # Save the new course in the database
        connection.commit()
        return jsonify(course), 201

    except psycopg2.errors.UniqueViolation:
        # Course codes must be unique
        connection.rollback()
        return jsonify({"error": "A course with that code already exists"}), 409

    finally:
        # Close the database connection, even if something went wrong
        connection.close()


@app.route("/courses", methods=["GET"])
def get_courses():
    # Open the Catalogue database
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Get every course, in ID order
            cursor.execute(
                "SELECT id, code, title, description FROM courses ORDER BY id"
            )
            rows = cursor.fetchall()

        # Convert each database row into a JSON object
        courses = [course_from_row(row) for row in rows]
        return jsonify(courses), 200

    finally:
        connection.close()


@app.route("/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, code, title, description
                FROM courses
                WHERE id = %s
                """,
                (course_id,),
            )
            row = cursor.fetchone()

        # No matching row means that course does not exist
        if row is None:
            return jsonify({"error": "Course not found"}), 404

        return jsonify(course_from_row(row)), 200

    finally:
        connection.close()


if __name__ == "__main__":
    # Listen on port 5002 so Docker can expose this API
    app.run(host="0.0.0.0", port=5002, debug=True)