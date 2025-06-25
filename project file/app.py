from flask import Flask, render_template, request, redirect, session
import MySQLdb

app = Flask(__name__)
app.secret_key = 'freelance_secret'

# DB Connection
def get_db_connection():
    return MySQLdb.connect(host="localhost", user="root", password="", database="freelance_finder")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)", (name, email, password, role))
            conn.commit()
        except MySQLdb.IntegrityError:
            return "Email already exists!"
        cur.close()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            return "Invalid login"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if session['role'] == 'client':
        cur.execute("SELECT * FROM projects WHERE client_id = %s", (session['user_id'],))
        jobs = cur.fetchall()

        # Fetch applications with freelancer details for each job
        applications = {}
        for job in jobs:
            cur.execute("""
                SELECT users.name, users.email, applications.project_id
                FROM applications
                JOIN users ON applications.freelancer_id = users.id
                WHERE applications.project_id = %s
            """, (job[0],))
            applicants = cur.fetchall()
            applications[job[0]] = applicants

        cur.close()
        conn.close()
        return render_template('client_dashboard.html', username=session['username'], jobs=jobs, applications=applications)

    elif session['role'] == 'freelancer':
        cur.execute("SELECT * FROM projects")
        jobs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('freelancer_dashboard.html', username=session['username'], jobs=jobs)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['role'] != 'client':
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO projects (client_id, title, description) VALUES (%s, %s, %s)", (session['user_id'], title, description))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/dashboard')
    return render_template('post_job.html')

@app.route('/apply/<int:project_id>')
def apply(project_id):
    if 'user_id' not in session or session['role'] != 'freelancer':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications WHERE project_id = %s AND freelancer_id = %s", (project_id, session['user_id']))
    existing = cur.fetchone()
    if not existing:
        cur.execute("INSERT INTO applications (project_id, freelancer_id) VALUES (%s, %s)", (project_id, session['user_id']))
        conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)
