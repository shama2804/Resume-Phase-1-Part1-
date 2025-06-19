from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from utils.resume_parser import parse_resume
from pymongo import MongoClient
from backend.db_handler import save_to_db
from backend.extract_resume import extract_full_resume


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

client = MongoClient("mongodb://localhost:27017")
db = client["resume_app"]
collection = db["applications"]

@app.route('/')
def index():
    return render_template('form.html', prefill={}, resume_filename="")

@app.route('/upload', methods=['POST'])
def upload_resume():
    file = request.files['resume']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    parsed_data = parse_resume(filepath)
    return render_template('form.html', prefill=parsed_data, resume_filename=filename)

@app.route("/submit", methods=["POST"])
def submit():
    # Get filename from hidden input
    filename = request.form.get("resume_filename")
    filepath = f"uploads/{filename}" if filename else None

    # Extract again if needed
    extracted_info = extract_full_resume(filepath) if filepath else {}

    # Get final form data
    final_data = {
        "personal_details": {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
        },
        "education": [{
            "degree": request.form.get("degree"),
            "college": request.form.get("college"),
            "graduation": request.form.get("graduation"),
            "cgpa": request.form.get("cgpa"),
        }],
        "experience": [{
            "job_title": request.form.get("experience[0][job_title]"),
            "current_company": request.form.get("experience[0][current_company]"),
            "employment_duration": request.form.get("experience[0][employment_duration]"),
            "job_responsibilities": request.form.get("experience[0][job_responsibilities]"),
        }],
        "skills": request.form.getlist("skills[]"),
        "projects": [],
        "links": {
            "linkedin": request.form.get("linkedin"),
            "website": request.form.get("website")
        }
    }

    # Projects: dynamically collect all project blocks
    i = 0
    while True:
        if f"projects[{i}][title]" not in request.form:
            break
        final_data["projects"].append({
            "title": request.form.get(f"projects[{i}][title]"),
            "tech_stack": request.form.get(f"projects[{i}][tech_stack]"),
            "description": request.form.get(f"projects[{i}][description]"),
            "duration": request.form.get(f"projects[{i}][duration]"),
        })
        i += 1
    # Save to MongoDB
    from backend.db_handler import save_to_db
    doc_id = save_to_db(final_data)

    return jsonify({"message": "✅ Application stored", "doc_id": str(doc_id)})
if __name__ == "__main__":
    app.run(debug=True)
