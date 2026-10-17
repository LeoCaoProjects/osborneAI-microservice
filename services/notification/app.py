import os

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_connection():
    # database settings from docker compose
    return psycopg2.connect(os.environ["DATABASE_URL"])


@app.route("/notifications", methods=["GET"])
def get_notifications():
    # Get all saved notifications from the database
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, feedback_id, recipient, message, created_at
            FROM notifications
            ORDER BY id
            """
        )
        notifications = cursor.fetchall()

        return jsonify(notifications), 200

    except psycopg2.Error:
        # Return a error if the database cannot be read
        app.logger.exception("Could not get notifications")
        return jsonify({"error": "Could not get notifications"}), 503

    finally:
        # Close the database resources after the request
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.route("/notifications", methods=["POST"])
def create_notification():
    # Read the notification details from the JSON request
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    if "feedback_id" not in data or "recipient" not in data or "message" not in data:
        return jsonify(
            {"error": "feedback_id, recipient, and message are required"}
        ), 400

    # Check that the feedback ID is a number
    try:
        if isinstance(data["feedback_id"], float) and not data["feedback_id"].is_integer():
            return jsonify({"error": "feedback_id must be an integer"}), 400
        feedback_id = int(data["feedback_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "feedback_id must be a number"}), 400

    if feedback_id < 1:
        return jsonify({"error": "feedback_id must be greater than zero"}), 400

    recipient = data["recipient"]
    message = data["message"]

    # Make sure the recipient and message contain text
    if not isinstance(recipient, str) or not recipient.strip():
        return jsonify({"error": "recipient must contain text"}), 400

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "message must contain text"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Save the notification and get the new database record
        cursor.execute(
            """
            INSERT INTO notifications (feedback_id, recipient, message)
            VALUES (%s, %s, %s)
            RETURNING id, feedback_id, recipient, message, created_at
            """,
            (feedback_id, recipient.strip(), message.strip()),
        )
        notification = cursor.fetchone()
        connection.commit()

        return jsonify(notification), 201

    except psycopg2.Error:
        # Return an error if the database cannot save the notification
        app.logger.exception("Could not save notification")
        return jsonify({"error": "Could not save notification"}), 503

    finally:
        # Close the database resources after the request
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    # Listen on the containers network on port 5004
    app.run(host="0.0.0.0", port=5004, debug=True)
