
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this")

# Atlas connection string is supplied through MONGO_URI.
# If it is absent, use the local MongoDB server.
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = client["beginner_db"]
todos_collection = db["todos"]


@app.route("/")
def index():
    try:
        todos = list(
            todos_collection.find().sort("_id", -1)
        )
        return render_template("index.html", todos=todos)
    except PyMongoError:
        app.logger.exception("Could not retrieve tasks")
        return (
            "Could not connect to MongoDB. "
            "Check MONGO_URI and Atlas Network Access.",
            503
        )


@app.route("/add", methods=["POST"])
def add_todo():
    task = request.form.get("task", "").strip()

    if not task:
        flash("Please enter a task.", "error")
        return redirect(url_for("index"))

    try:
        todos_collection.insert_one({"task": task})
        flash("Task added successfully!", "success")
    except PyMongoError:
        app.logger.exception("Could not add task")
        flash("Could not save the task. Check your database connection.", "error")

    return redirect(url_for("index"))


@app.route("/delete/<task_id>", methods=["POST"])
def delete_todo(task_id):
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        result = todos_collection.delete_one(
            {"_id": ObjectId(task_id)}
        )
        if result.deleted_count:
            flash("Task deleted.", "success")
        else:
            flash("Task not found.", "error")
    except (InvalidId, PyMongoError):
        flash("Could not delete the task.", "error")

    return redirect(url_for("index"))


@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return {"status": "ok", "database": "connected"}, 200
    except PyMongoError:
        return {"status": "error", "database": "disconnected"}, 503


if __name__ == "__main__":
    app.run(debug=True)
