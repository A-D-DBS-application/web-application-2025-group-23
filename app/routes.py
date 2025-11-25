from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, user, Company, CompanyMember, Service, BarterDeal, Contract, Review
import uuid
import datetime

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
        is_admin = request.form.get('is_admin', 'no') == 'yes'
        if username is None:
            return 'Missing required fields', 400
        if user.query.filter_by(username=username).first() is None:
            new_user = user(
                user_id=uuid.uuid4(),
                username=username
            )
            db.session.add(new_user)
            db.session.flush()

            example_company_id = "00000000-0000-0000-0000-000000000001"  # Placeholder
            new_member = CompanyMember(
                member_id=uuid.uuid4(),
                company_id=example_company_id,
                user_id=new_user.user_id,
                member_role='member',
                is_admin=is_admin,
                created_at=datetime.datetime.now(),
                # job_description belongs on `user` (if you want it saved there) —
                # don't pass unknown columns here.
            )
            db.session.add(new_member)
            db.session.commit()

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
        usr.job_description = request.form.get('jobdescription', usr.job_description)
        # `company_name` is not a column on the `user` model — keep only supported fields
        admin_val = request.form.get('is_admin', 'no') == 'yes'
        company_member = CompanyMember.query.filter_by(user_id=usr.user_id).first()
        if company_member:
            company_member.is_admin = admin_val
        db.session.commit()
        return redirect(url_for('main.profile_settings'))
    return render_template('profile.html', user=usr)
