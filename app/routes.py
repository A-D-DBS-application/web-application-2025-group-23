from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, user, Company, Service, BarterDeal, Contract, Review  # Gebruik het nieuwe user model

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        usr = user.query.get(session['user_id'])
        return render_template('index.html', username=usr.username if usr else None)
    return render_template('index.html', username=None)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if username is None:
            return 'Missing required fields', 400
        if user.query.filter_by(username=username).first() is None:
            import uuid
            new_user = user(
                user_id=str(uuid.uuid4()),
                username=username,
                verified=False
            )
            db.session.add(new_user)
            db.session.commit()

            # UUID als string in session
            session['user_id'] = str(new_user.user_id)

            return redirect(url_for('main.index'))
        return 'Username already registered'
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        usr = user.query.filter_by(username=username).first()
        if usr:

            # UUID als string in session
            session['user_id'] = str(usr.user_id)

            return redirect(url_for('main.index'))
        return 'User not found'
    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

@main.route('/profile', methods=['GET', 'POST'])
def profile_settings():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    usr = user.query.get(session['user_id'])

    if request.method == 'POST':
        usr.email = request.form.get('email', usr.email)
        usr.role = request.form.get('role', usr.role)
        usr.location = request.form.get('location', usr.location)
        usr.job_description = request.form.get('job_description', usr.job_description)
        usr.company_name = request.form.get('company_name', usr.company_name)
        db.session.commit()
        return redirect(url_for('main.profile_settings'))

    return render_template(
        'profile.html',
        user=usr
    )
