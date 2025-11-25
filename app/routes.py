from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, user, Company, CompanyMember, CompanyJoinRequest, Service, BarterDeal, Contract, Review
import uuid
import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    Serve the public start page for anonymous users, and the old home/dashboard
    (index.html) for logged-in users.
    """
    if 'user_id' in session:
        usr = user.query.get(session['user_id'])
        return render_template('index.html', username=usr.username if usr else None)
    # anonymous users see the new start/landing page
    return render_template('start.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if username is None:
            return 'Missing required fields', 400
        if user.query.filter_by(username=username).first() is None:
            new_user = user(
                user_id=uuid.uuid4(),
                username=username
            )
            db.session.add(new_user)
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
        # Do not modify CompanyMember.is_admin from the profile page; admin status
        # is controlled when creating companies and via manage pages.
        db.session.commit()
        return redirect(url_for('main.profile_settings'))
    return render_template('profile.html', user=usr)


@main.route('/company/create', methods=['GET', 'POST'])
def create_company():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            return 'Name required', 400
        company = Company(
            company_id=uuid.uuid4(),
            name=name,
            created_at=datetime.datetime.now(),
            join_code=uuid.uuid4().hex[:8]
        )
        db.session.add(company)
        db.session.flush()

        # Make creator an admin
        member = CompanyMember(
            member_id=uuid.uuid4(),
            company_id=company.company_id,
            user_id=uuid.UUID(session['user_id']),
            member_role='founder',
            is_admin=True,
            created_at=datetime.datetime.now(),
        )
        db.session.add(member)
        db.session.commit()
        flash('Bedrijf aangemaakt — je bent admin en member', 'success')
        return redirect(url_for('main.my_companies'))
    return render_template('create_company.html')


@main.route('/company/join', methods=['GET', 'POST'])
def join_company():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    msg = None
    if request.method == 'POST':
        code = request.form.get('code')
        if not code:
            msg = 'Enter a code'
        else:
            company = Company.query.filter_by(join_code=code).first()
            if not company:
                msg = 'Invalid code'
            else:
                # check if already member
                existing = CompanyMember.query.filter_by(company_id=company.company_id, user_id=uuid.UUID(session['user_id'])).first()
                if existing:
                    flash('Je bent al lid van dit bedrijf', 'warning')
                    return redirect(url_for('main.join_company'))
                else:
                    # create a join request
                    req = CompanyJoinRequest(
                        request_id=uuid.uuid4(),
                        company_id=company.company_id,
                        user_id=uuid.UUID(session['user_id']),
                        created_at=datetime.datetime.now(),
                    )
                    db.session.add(req)
                    db.session.commit()
                    flash('Aanvraag verstuurd — wacht op goedkeuring', 'success')
                    return redirect(url_for('main.join_company'))
    return render_template('join_company.html')


@main.route('/companies/my')
def my_companies():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    admin_companies = [m.company for m in memberships if m.is_admin]
    member_companies = [m.company for m in memberships if not m.is_admin]
    return render_template('my_companies.html', admin_companies=admin_companies, member_companies=member_companies)


@main.route('/company/<uuid:company_id>/manage')
def manage_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    # check if caller is admin
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not membership:
        # non-admin members get redirected to the member view of the company
        member_check = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
        if member_check:
            flash('Je hebt geen admin rechten voor dit bedrijf', 'warning')
            return redirect(url_for('main.view_company', company_id=company_id))
        return 'Forbidden', 403
    company = Company.query.get(company_id)
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    pending = CompanyJoinRequest.query.filter_by(company_id=company_id).all()
    return render_template('manage_company.html', company=company, members=members, pending=pending)

@main.route('/company/<uuid:company_id>')
def view_company(company_id):
    """Member-facing read-only company view (no management actions)."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        return 'Forbidden', 403
    company = Company.query.get(company_id)
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    return render_template('company_view.html', company=company, members=members, is_admin=membership.is_admin)


@main.route('/company/<uuid:company_id>/accept/<uuid:request_id>', methods=['POST'])
def accept_join_request(company_id, request_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not membership:
        return 'Forbidden', 403
    req = CompanyJoinRequest.query.get(request_id)
    if not req or req.company_id != company_id:
        return 'Not found', 404
    # create member
    new_member = CompanyMember(
        member_id=uuid.uuid4(),
        company_id=company_id,
        user_id=req.user_id,
        member_role='member',
        is_admin=False,
        created_at=datetime.datetime.now(),
    )
    db.session.add(new_member)
    db.session.delete(req)
    db.session.commit()
    flash('De gebruiker is toegevoegd aan het bedrijf', 'success')
    return redirect(url_for('main.manage_company', company_id=company_id))


@main.route('/company/<uuid:company_id>/transfer/<uuid:member_id>', methods=['POST'])
def transfer_admin(company_id, member_id):
    """Transfer admin role to a non-admin member. Only the current admin can do this."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    # find the current admin for the company and ensure caller is that admin
    current_admin = CompanyMember.query.filter_by(company_id=company_id, is_admin=True).first()
    if not current_admin or str(current_admin.user_id) != session.get('user_id'):
        return 'Forbidden', 403
    target = CompanyMember.query.get(member_id)
    if not target or target.company_id != company_id:
        return 'Not found', 404
    if target.is_admin:
        flash('Deze gebruiker is al admin', 'warning')
        return redirect(url_for('main.manage_company', company_id=company_id))
    # Perform transfer: target becomes admin, current_admin loses admin
    target.is_admin = True
    current_admin.is_admin = False
    db.session.commit()
    flash('Admin-rechten overgedragen. Je bent nu gewone member.', 'success')
    # Redirect to overall companies overview so user sees updated member/admin sections
    return redirect(url_for('main.my_companies'))


@main.route('/company/<uuid:company_id>/remove/<uuid:member_id>', methods=['POST'])
def remove_member(company_id, member_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    # only admin can remove members
    admin_membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not admin_membership:
        return 'Forbidden', 403
    member = CompanyMember.query.get(member_id)
    if not member or member.company_id != company_id:
        return 'Not found', 404
    # disallow removing admins completely (we only support 1 admin per company)
    if member.is_admin:
        return 'Cannot remove admin users', 400
    # do not allow removing yourself (admins can't remove themselves)
    if str(member.user_id) == session.get('user_id'):
        return "Can't remove yourself", 400
    db.session.delete(member)
    db.session.commit()
    flash('Member verwijderd', 'success')
    return redirect(url_for('main.manage_company', company_id=company_id))


@main.route('/company/<uuid:company_id>/leave', methods=['POST'])
def leave_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        return 'Not a member', 400
    # Admins are not allowed to leave a company — they must delete the company instead.
    if membership.is_admin:
        return 'Admins cannot leave the company. Delete the company instead.', 400
    db.session.delete(membership)
    db.session.commit()
    flash('Je bent uit het bedrijf gestapt', 'success')
    return redirect(url_for('main.my_companies'))


@main.route('/company/<uuid:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    admin_membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not admin_membership:
        return 'Forbidden', 403
    # delete members, join requests, and company
    CompanyMember.query.filter_by(company_id=company_id).delete()
    CompanyJoinRequest.query.filter_by(company_id=company_id).delete()
    Company.query.filter_by(company_id=company_id).delete()
    db.session.commit()
    flash('Bedrijf en alle data verwijderd', 'success')
    return redirect(url_for('main.my_companies'))
