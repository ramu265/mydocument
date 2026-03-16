from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
import os

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# CLOUDINARY CONFIGURATION
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# MODELS (Database Tables)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), nullable=False)
    doc_name = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(300), nullable=False)
    public_id = db.Column(db.String(100), nullable=False)
    doc_password = db.Column(db.String(80), nullable=False)

# --- ఈ సెక్షన్ నీ టేబుల్స్ ని ఆటోమేటిక్ గా క్రియేట్ చేస్తుంది ---
with app.app_context():
    # పాత 'documents' టేబుల్ లో user_id ఎర్రర్ ఉంది కాబట్టి దాన్ని తీసేసి కొత్తది క్రియేట్ చేస్తున్నాం
    db.session.execute(db.text('DROP TABLE IF EXISTS documents CASCADE;'))
    db.session.execute(db.text('DROP TABLE IF EXISTS "user" CASCADE;'))
    db.session.commit()
    
    # ఇప్పుడు పర్ఫెక్ట్ గా కొత్త టేబుల్స్ క్రియేట్ అవుతాయి
    db.create_all() 

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = username
            return redirect("/dashboard")
        return "Invalid Login"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        except:
            return "User already exists"
    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        docname = request.form["docname"]
        docpass = request.form["docpass"]
        file = request.files["file"]

        if file:
            upload_result = cloudinary.uploader.upload(file)
            new_doc = Document(
                user_name=session["user"],
                doc_name=docname,
                file_url=upload_result['secure_url'],
                public_id=upload_result['public_id'],
                doc_password=docpass
            )
            db.session.add(new_doc)
            db.session.commit()

    docs = Document.query.filter_by(user_name=session["user"]).all()
    return render_template("dashboard.html", docs=docs)

@app.route("/check_password", methods=["POST"])
def check_password():
    docid = request.form["docid"]
    entered_password = request.form["password"]
    doc = Document.query.get(docid)

    if doc and doc.doc_password == entered_password:
        return jsonify({"status": "success", "file": doc.file_url})
    return jsonify({"status": "fail"})

@app.route("/delete/<int:id>")
def delete(id):
    doc = Document.query.get(id)
    if doc:
        cloudinary.uploader.destroy(doc.public_id)
        db.session.delete(doc)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
