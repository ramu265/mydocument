from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# DATABASE
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS documents(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
name TEXT,
filename TEXT,
password TEXT
)
""")

conn.commit()


@app.route("/", methods=["GET","POST"])
def login():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        user=cur.fetchone()

        if user:
            session["user"]=username
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        try:
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,password))
            conn.commit()
            return redirect("/")
        except:
            return "User already exists"

    return render_template("register.html")


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user" not in session:
        return redirect("/")

    if request.method=="POST":

        docname=request.form["docname"]
        docpass=request.form["docpass"]
        file=request.files["file"]

        filename=file.filename
        filepath=os.path.join(app.config["UPLOAD_FOLDER"],filename)
        file.save(filepath)

        cur.execute("INSERT INTO documents(user,name,filename,password) VALUES(?,?,?,?)",
        (session["user"],docname,filename,docpass))

        conn.commit()

    cur.execute("SELECT * FROM documents WHERE user=?",(session["user"],))
    docs=cur.fetchall()

    return render_template("dashboard.html",docs=docs)


@app.route("/check_password", methods=["POST"])
def check_password():

    docid=request.form["docid"]
    password=request.form["password"]

    cur.execute("SELECT password, filename FROM documents WHERE id=?",(docid,))
    data=cur.fetchone()

    if data and data[0]==password:
        return jsonify({"status":"success","file":data[1]})
    else:
        return jsonify({"status":"fail"})


@app.route("/view/<filename>")
def view_file(filename):

    if "user" not in session:
        return redirect("/")

    return render_template("view_file.html",file=filename)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"],filename,as_attachment=True)


@app.route("/delete/<int:id>")
def delete(id):

    cur.execute("SELECT filename FROM documents WHERE id=?",(id,))
    file=cur.fetchone()

    if file:
        path=os.path.join(app.config["UPLOAD_FOLDER"],file[0])
        if os.path.exists(path):
            os.remove(path)

    cur.execute("DELETE FROM documents WHERE id=?",(id,))
    conn.commit()

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__=="__main__":
    app.run(debug=True)