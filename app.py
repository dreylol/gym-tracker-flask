from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Workout exercises dictionary
workout_days = {
    "Push": ["Bench Press", "Overhead Press", "Incline DB Bench", "DB Flys", "Lat Raises", "Tricep Dips", "Tricep Pushdowns"],
    "Pull": ["Deadlift", "Pull-Ups", "Barbell Rows", "T-Bar Row", "Hammer Curls", "Barbell Curls", "Static Plate Holds"],
    "Legs": ["Front Squat", "Leg Press", "Leg Curls", "Hack Squat", "Leg Extensions", "Calf Raises"],
    "Upper": ["Bench Press", "Pull-Ups", "Cable Rows", "Rear Delt Flyes", "Overhead Press", "Barbell Curls", "Tricep Pushdowns"],
    "Lower": ["Front Squat", "Leg Press", "Leg Curls", "Calf Raises", "Hanging Leg Raises", "Farmer's Walk"]
}

@app.route('/')
def index():
    return render_template("index.html", workout_days=workout_days)

@app.route('/log', methods=['POST'])
def log():
    day = request.form.get("day")
    exercise = request.form.get("exercise")
    weight = request.form.get("weight")
    reps = request.form.get("reps")
    sets = request.form.get("sets")
    notes = request.form.get("notes") or ""  # Optional, default empty string
    date = datetime.now().strftime("%Y-%m-%d")

    # Basic validation to ensure required fields (except notes) are present
    if day and exercise and weight and reps and sets:
        try:
            weight_float = float(weight)
            reps_int = int(reps)
            sets_int = int(sets)
        except ValueError:
            # Invalid input, redirect back without logging
            return redirect(url_for('index'))

        # Append to CSV file with new fields sets and notes
        with open("workout_log.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([date, day, exercise, weight_float, reps_int, sets_int, notes])

    return redirect(url_for('index'))

@app.route('/history')
def history():
    logs = []
    if os.path.exists("workout_log.csv"):
        with open("workout_log.csv", newline="") as file:
            reader = csv.reader(file)
            logs = list(reader)
    return render_template("history.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
