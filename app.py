from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os
import json
from datetime import datetime

app = Flask(__name__)

CSV_FILE = "workout_logs.csv"
TEMPLATE_FILE = "workout_templates.json"

# --- Utility Functions ---

def read_logs():
    logs = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if len(row) < 7:
                    continue
                try:
                    logs.append({
                        "id": i,
                        "date": row[0],
                        "day": row[1],
                        "exercise": row[2],
                        "weight": float(row[3]),
                        "reps": int(row[4]),
                        "sets": int(row[5]),
                        "notes": row[6]
                    })
                except ValueError:
                    continue
    return logs

def write_logs(logs):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        for log in logs:
            writer.writerow([
                log["date"], log["day"], log["exercise"],
                log["weight"], log["reps"], log["sets"], log["notes"]
            ])

def read_templates():
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r') as file:
            return json.load(file)
    return {}

def write_templates(templates):
    with open(TEMPLATE_FILE, 'w') as file:
        json.dump(templates, file, indent=4)

# --- Routes ---

@app.route('/')
def index():
    today_str = datetime.today().strftime('%Y-%m-%d')
    return render_template('index.html', today=today_str)

@app.route('/submit', methods=['POST'])
def submit():
    date_str = datetime.today().strftime('%Y-%m-%d')
    day = request.form.get('day')
    exercise = request.form.get('exercise')
    weight = request.form.get('weight')
    reps = request.form.get('reps')
    sets = request.form.get('sets')
    notes = request.form.get('notes', '')

    if not all([day, exercise, weight, reps, sets]):
        return "Missing required form data", 400

    try:
        new_entry = {
            "date": date_str,
            "day": day,
            "exercise": exercise,
            "weight": float(weight),
            "reps": int(reps),
            "sets": int(sets),
            "notes": notes
        }
    except ValueError:
        return "Invalid number format in form data", 400

    logs = read_logs()
    logs.append(new_entry)
    write_logs(logs)

    return redirect(url_for('history'))

@app.route('/history')
def history():
    sort_key = request.args.get('sort', 'date')
    logs = read_logs()
    valid_keys = ['date', 'day', 'exercise', 'weight', 'reps', 'sets']
    if sort_key not in valid_keys:
        sort_key = 'date'
    reverse = sort_key == 'date'
    logs.sort(key=lambda x: x[sort_key], reverse=reverse)
    return render_template('history.html', logs=logs, sort_key=sort_key)

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete(entry_id):
    logs = read_logs()
    logs = [log for log in logs if log["id"] != entry_id]
    write_logs(logs)
    return redirect(url_for('history'))

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit(entry_id):
    logs = read_logs()
    entry = next((log for log in logs if log["id"] == entry_id), None)
    if not entry:
        return "Entry not found", 404

    if request.method == 'POST':
        day = request.form.get('day')
        exercise = request.form.get('exercise')
        weight = request.form.get('weight')
        reps = request.form.get('reps')
        sets = request.form.get('sets')
        notes = request.form.get('notes', '')
        if not all([day, exercise, weight, reps, sets]):
            return "Missing required form data", 400
        try:
            entry["day"] = day
            entry["exercise"] = exercise
            entry["weight"] = float(weight)
            entry["reps"] = int(reps)
            entry["sets"] = int(sets)
            entry["notes"] = notes
        except ValueError:
            return "Invalid number format", 400
        write_logs(logs)
        return redirect(url_for('history'))

    return render_template('edit.html', entry=entry)

@app.route('/progress')
def progress():
    logs = read_logs()
    max_weight_per_exercise = {}
    weight_per_date = {}
    for log in logs:
        ex = log["exercise"]
        wt = log["weight"]
        dt = log["date"]
        if ex not in max_weight_per_exercise or wt > max_weight_per_exercise[ex]:
            max_weight_per_exercise[ex] = wt
        if dt not in weight_per_date or wt > weight_per_date[dt]:
            weight_per_date[dt] = wt
    sorted_dates = sorted(weight_per_date)
    weights = [weight_per_date[d] for d in sorted_dates]
    return render_template("progress.html", dates=sorted_dates, weights=weights, max_weight_data=max_weight_per_exercise)

@app.route('/one_rm/<exercise>')
def one_rm(exercise):
    logs = read_logs()
    relevant = [log for log in logs if log["exercise"].lower() == exercise.lower()]
    if not relevant:
        return jsonify({"one_rm": 0})
    max_1rm = max(w * (1 + r / 30) if r != 1 else w for w, r in [(log["weight"], log["reps"]) for log in relevant])
    return jsonify({"one_rm": round(max_1rm, 2)})

# --- Template Features ---

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        template_name = request.form.get('template_name')
        exercises = request.form.get('exercises')  # Raw JSON input
        if not template_name or not exercises:
            return "Missing name or exercises", 400
        try:
            parsed = json.loads(exercises)
            if not isinstance(parsed, list):
                return "Exercises must be a JSON list", 400
            templates = read_templates()
            templates[template_name] = parsed
            write_templates(templates)
            return redirect(url_for('use_template'))
        except json.JSONDecodeError:
            return "Invalid JSON format", 400
    return render_template('create_template.html')

@app.route('/use_template')
def use_template():
    templates = read_templates()
    return render_template('use_template.html', templates=templates)

@app.route('/load_template/<template_name>')
def load_template(template_name):
    templates = read_templates()
    data = templates.get(template_name)
    if not data:
        return "Template not found", 404
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
