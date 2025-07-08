from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'd1ea965f774a33c9bf37c1533dd9ebbe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)


with app.app_context():
    print("Creating all tables if not exist...")
    db.create_all()

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/sign-in', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.", "error")
            return render_template('sign-in.html')
    return render_template('sign-in.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful. Please sign in.", "success")
        return redirect(url_for('signin'))

    return render_template('sign-up.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/home2')
def home2():
    return render_template('home.html')
    

@app.route('/home')
def home():
    if 'username' not in session:
        flash("Please sign in to access the assistant.", "error")
        return redirect(url_for('signin'))
    return render_template('home.html')

@app.route("/biology")
def run_biology():
    try:
        username = session.get("username", "guest")
        subprocess.Popen(["python", "modules/biology.py"])
        return redirect(f"http://127.0.0.1:5002?username={username}")
    except Exception as e:
        return f"Error starting Biology module: {str(e)}"

@app.route('/more-details')
def more_details():
    return render_template('more-details.html')

@app.route('/view-demo')
def view_demo():
    video_path = r"D:\VoiceAssistantProjectFinal\static\demo.mp4"
    if os.path.exists(video_path):
        return send_from_directory(os.path.dirname(video_path), os.path.basename(video_path), mimetype='video/mp4')
    else:
        return "Video not found", 404

@app.route('/math')
def run_math():
    try:
        username = session.get("username", "guest")
        result = subprocess.Popen(["python", "modules/math.py"])
        print("Math module launched:", result)
        return redirect(f"http://127.0.0.1:5003?username={username}")
    except Exception as e:
        print("Launch failed:", str(e))
        return f"Error starting math module: {str(e)}"


@app.route('/physics')
def run_physics():
    try:
        username = session.get("username", "guest")
        subprocess.Popen(["python", "modules/physics.py"])
        return redirect(f"http://127.0.0.1:5005?username={username}")
    except Exception as e:
        return f"Error starting physics module: {str(e)}"

@app.route('/chemistry')
def run_chemistry():
    try:
        username = session.get("username", "guest")
        subprocess.Popen(["python", "modules/chemistry.py"])
        return redirect(f"http://127.0.0.1:5004?username={username}")
    except Exception as e:
        return f"Error starting chemistry module: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
