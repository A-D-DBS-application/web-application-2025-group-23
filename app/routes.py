"""
Core routes - authentication, company management, services, deals, and utility pages.
"""
import uuid
import datetime
from flask import request, redirect, url_for, render_template, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .blueprints.core import main
from .models import db, User, Company, CompanyMember, Service, DealProposal, ActiveDeal, ServiceInterest, Review, CompanyJoinRequest


def _workspace_context(company_id: uuid.UUID, uid: uuid.UUID):
    """Build sidebar + counts context for workspace pages."""
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        return None

    member_count = CompanyMember.query.filter_by(company_id=company_id).count()
    service_count = Service.query.filter_by(company_id=company_id).count()

    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    sidebar_companies = []
    for mem in memberships:
        comp = Company.query.get(mem.company_id)
        if not comp:
            continue
        sidebar_companies.append({
            'company_id': comp.company_id,
            'name': comp.name,
            'member_count': CompanyMember.query.filter_by(company_id=comp.company_id).count(),
            'service_count': Service.query.filter_by(company_id=comp.company_id).count(),
            'role': 'Admin' if mem.is_admin else 'Member',
            'is_selected': comp.company_id == company_id,
        })

    return {
        'company': company,
        'membership': membership,
        'member_count': member_count,
        'service_count': service_count,
        'companies': sidebar_companies,
    }


# ==================== UTILITY ROUTES ====================

@main.route("/")
def index():
    """Serve the public start page for anonymous users, redirect logged-in users to my_companies."""
    if "user_id" in session:
        return redirect(url_for("main.my_companies"))
    return render_template("start.html")


@main.route("/start")
def start():
    """Start page route (alias for index)."""
    return index()


@main.route("/support")
def support():
    """Support page."""
    return render_template("support.html")


@main.route("/about-us")
def about_us():
    """About Us page."""
    return render_template("about_us.html")


@main.route("/company-choice")
def company_choice():
    """Page to choose between creating or joining a company."""
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return render_template("company_choice.html")


@main.route("/select-company-marketplace")
def select_company_for_marketplace():
    """Let the user pick which company to use for the marketplace."""
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    uid = uuid.UUID(session["user_id"])
    memberships = CompanyMember.query.filter_by(user_id=uid).all()

    # If user is in only 1 company, automatically select it and go to marketplace
    if len(memberships) == 1:
        company = Company.query.get(memberships[0].company_id)
        if company:
            return redirect(url_for('main.marketplace', company_id=company.company_id))

    companies = []
    for membership in memberships:
        comp = Company.query.get(membership.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                "company_id": comp.company_id,
                "name": comp.name,
                "description": comp.description,
                "member_count": member_count,
                "service_count": service_count,
                "is_admin": membership.is_admin
            })

    return render_template("select_company_marketplace.html", companies=companies)


# ==================== AUTHENTICATION ROUTES ====================

@main.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        if User.query.filter_by(username=username).first() is None:
            new_user = User(
                user_id=uuid.uuid4(),
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = str(new_user.user_id)
            return redirect(url_for('main.my_companies'))
        flash('Username already registered', 'error')
        return render_template('register.html')
    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usr = User.query.filter_by(username=username).first()
        if usr and check_password_hash(usr.password_hash, password):
            session['user_id'] = str(usr.user_id)
            
            # Check how many companies the user is in
            memberships = CompanyMember.query.filter_by(user_id=usr.user_id).all()
            
            if len(memberships) == 0:
                # No companies, redirect to my_companies to create/join one
                return redirect(url_for('main.my_companies'))
            elif len(memberships) == 1:
                # Only one company, auto-select it and go to marketplace
                company = Company.query.get(memberships[0].company_id)
                return redirect(url_for('main.marketplace', company_id=company.company_id))
            else:
                # Multiple companies, go to select company screen
                return redirect(url_for('main.select_company_for_marketplace'))
        
        flash('Invalid username or password', 'error')
        return render_template('login.html')
    return render_template('login.html')


@main.route('/logout', methods=['GET', 'POST'])
def logout():
    """User logout."""
    session.pop('user_id', None)
    return redirect(url_for('main.index'))


@main.route('/profile', methods=['GET', 'POST'])
def profile_settings():
    """User profile settings."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    usr = User.query.get(session['user_id'])
    if request.method == 'POST':
        usr.email = request.form.get('email', usr.email)
        usr.location = request.form.get('location', usr.location)
        usr.job_description = request.form.get('jobdescription', usr.job_description)
        db.session.commit()
        return redirect(url_for('main.profile_settings'))
    return render_template('profile.html', user=usr)


@main.route('/user/<uuid:user_id>')
def view_user_profile(user_id):
    """View public profile of another user."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    viewed_user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=viewed_user)


# ==================== COMPANY MANAGEMENT ROUTES ====================

@main.route('/my-companies')
def my_companies():
    """Show all companies the user belongs to."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    usr = User.query.get(uid)
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    user_companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            user_companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'description': comp.description,
                'member_count': member_count,
                'service_count': service_count,
                'is_admin': m.is_admin
            })
    return render_template(
        'my_companies.html',
        current_user=usr,
        username=usr.username if usr else '',
        companies=user_companies,
    )


@main.route('/company/create', methods=['GET', 'POST'])
def create_company():
    """Create a new company."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            flash('Company name is required', 'error')
            return render_template('create_company.html')
        new_company = Company(
            company_id=uuid.uuid4(),
            name=name,
            description=description or '',
            barter_coins=0,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(new_company)
        db.session.flush()
        creator = CompanyMember(
            member_id=uuid.uuid4(),
            company_id=new_company.company_id,
            user_id=uid,
            is_admin=True,
            member_role='founder',
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(creator)
        db.session.commit()
        flash('Company created successfully', 'success')
        return redirect(url_for('main.my_companies'))
    return render_template('create_company.html')


@main.route('/company/join', methods=['GET', 'POST'])
def join_company():
    """Join an existing company via join code."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    if request.method == 'POST':
        join_code = request.form.get('join_code')
        company = Company.query.filter_by(join_code=join_code).first()
        if not company:
            flash('Invalid join code', 'error')
            return render_template('join_company.html')
        existing = CompanyMember.query.filter_by(company_id=company.company_id, user_id=uid).first()
        if existing:
            flash('You are already a member of this company', 'info')
            return redirect(url_for('main.my_companies'))
        member = CompanyMember(
            company_member_id=uuid.uuid4(),
            company_id=company.company_id,
            user_id=uid,
            is_admin=False,
            joined_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(member)
        db.session.commit()
        flash('Successfully joined company', 'success')
        return redirect(url_for('main.my_companies'))
    return render_template('join_company.html')


@main.route('/company/<uuid:company_id>')
def view_company(company_id):
    """View company details."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    return render_template('company_view.html', company=company, is_admin=membership.is_admin)


@main.route('/company/<uuid:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    """Edit company details. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to edit this company', 'error')
        return redirect(url_for('main.view_company', company_id=company_id))
    if request.method == 'POST':
        company.name = request.form.get('name', company.name)
        company.description = request.form.get('description', company.description)
        db.session.commit()
        flash('Company updated successfully', 'success')
        return redirect(url_for('main.view_company', company_id=company_id))
    return render_template('edit_company.html', company=company)


@main.route('/company/<uuid:company_id>/leave', methods=['POST'])
def leave_company(company_id):
    """Leave a company."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    db.session.delete(membership)
    db.session.commit()
    flash('You have left the company', 'success')
    return redirect(url_for('main.my_companies'))


@main.route('/company/<uuid:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    """Delete a company. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to delete this company', 'error')
        return redirect(url_for('main.view_company', company_id=company_id))
    db.session.delete(company)
    db.session.commit()
    flash('Company and all data deleted', 'success')
    return redirect(url_for('main.index'))


@main.route('/onboarding')
def onboarding():
    """Onboarding page."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('onboarding_get_started.html')


# ==================== WORKSPACE ROUTES ====================

@main.route('/workspace/<uuid:company_id>/overview')
@main.route('/workspace/<uuid:company_id>')
def workspace_overview(company_id):
    """Workspace overview page."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    context = _workspace_context(company_id, uid)
    if not context:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    company = context['company']
    membership = context['membership']
    member_count = context['member_count']
    service_count = context['service_count']
    companies = context['companies']
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    return render_template(
        'company_workspace_overview.html',
        company=company,
        members=members,
        is_admin=membership.is_admin,
        username=User.query.get(uid).username if User.query.get(uid) else '',
        companies=companies,
        member_count=member_count,
        service_count=service_count,
    )


@main.route('/workspace/<uuid:company_id>/members')
def workspace_members(company_id):
    """Workspace members page."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    context = _workspace_context(company_id, uid)
    if not context:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    company = context['company']
    membership = context['membership']
    member_count = context['member_count']
    service_count = context['service_count']
    companies = context['companies']
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    join_requests = CompanyJoinRequest.query.filter_by(company_id=company_id).all()
    return render_template(
        'company_workspace_members.html',
        company=company,
        members=members,
        join_requests=join_requests,
        is_admin=membership.is_admin,
        current_user_id=uid,
        username=User.query.get(uid).username if User.query.get(uid) else '',
        companies=companies,
        member_count=member_count,
        service_count=service_count,
    )


@main.route('/company/<uuid:company_id>/accept/<uuid:request_id>', methods=['POST'])
def accept_join_request(company_id, request_id):
    """Accept a join request. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    join_req = CompanyJoinRequest.query.get_or_404(request_id)
    member = CompanyMember(
        company_member_id=uuid.uuid4(),
        company_id=company_id,
        user_id=join_req.user_id,
        is_admin=False,
        joined_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.session.add(member)
    db.session.delete(join_req)
    db.session.commit()
    flash('Join request accepted', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/remove/<uuid:member_id>', methods=['POST'])
def remove_member(company_id, member_id):
    """Remove a member from company. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    member = CompanyMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member removed', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/transfer/<uuid:member_id>', methods=['POST'])
def transfer_admin(company_id, member_id):
    """Transfer admin role to another member. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    my_membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not my_membership or not my_membership.is_admin:
        flash('You do not have permission', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    member = CompanyMember.query.get_or_404(member_id)
    my_membership.is_admin = False
    member.is_admin = True
    db.session.commit()
    flash('Admin role transferred', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/demote/<uuid:member_id>', methods=['POST'])
def demote_admin(company_id, member_id):
    """Demote an admin. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    member = CompanyMember.query.get_or_404(member_id)
    member.is_admin = False
    db.session.commit()
    flash('Member demoted', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/workspace/<uuid:company_id>/services')
@main.route('/company/<uuid:company_id>/services')
def workspace_services(company_id):
    """List services for workspace."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    context = _workspace_context(company_id, uid)
    if not context:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    company = context['company']
    membership = context['membership']
    member_count = context['member_count']
    service_count = context['service_count']
    companies = context['companies']
    services = Service.query.filter_by(company_id=company_id).all()
    return render_template(
        'company_workspace_services.html',
        company=company,
        services=services,
        is_admin=membership.is_admin,
        username=User.query.get(uid).username if User.query.get(uid) else '',
        companies=companies,
        member_count=member_count,
        service_count=service_count,
    )


@main.route('/workspace/<uuid:company_id>/services/<uuid:service_id>')
def workspace_service_view(company_id, service_id):
    """Service detail inside a workspace (members only)."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    context = _workspace_context(company_id, uid)
    if not context:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    company = context['company']
    membership = context['membership']
    companies = context['companies']

    service = Service.query.get_or_404(service_id)
    if service.company_id != company_id:
        flash('Service does not belong to this company', 'error')
        return redirect(url_for('main.workspace_services', company_id=company_id))

    return render_template(
        'workspace_service_public_view.html',
        company=company,
        service=service,
        is_admin=membership.is_admin,
        username=User.query.get(uid).username if User.query.get(uid) else '',
        companies=companies,
    )


@main.route('/company/<uuid:company_id>/service', methods=['GET'])
def company_services(company_id):
    """List services for company view (public/private)."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    services = Service.query.filter_by(company_id=company_id).all()
    return render_template('company_services.html', company=company, services=services)


# ==================== SERVICE ROUTES ====================

@main.route('/company/<uuid:company_id>/service/add', methods=['GET', 'POST'])
def add_service(company_id):
    """Add a new service to a company. Members only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        duration_hours = request.form.get('duration_hours')
        categories = request.form.getlist('categories')
        custom_category = request.form.get('custom_category')
        is_offered = request.form.get('is_offered') == 'true'
        
        usr = User.query.get(uid)
        memberships = CompanyMember.query.filter_by(user_id=uid).all()
        user_companies = []
        for m in memberships:
            comp = Company.query.get(m.company_id)
            if comp:
                member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
                user_companies.append({
                    'company_id': comp.company_id,
                    'name': comp.name,
                    'member_count': member_count,
                    'is_admin': m.is_admin
                })
        
        if not title or not description or not duration_hours:
            flash('Vul dit veld in.', 'error')
            return render_template('service_add.html',
                                 company=company,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_duration=duration_hours,
                                 form_categories=categories,
                                 current_user=usr,
                                 user_companies=user_companies)
        
        if 'Other' in categories and not custom_category:
            flash('Vul dit veld in.', 'error')
            return render_template('service_add.html',
                                 company=company,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_duration=duration_hours,
                                 form_categories=categories,
                                 current_user=usr,
                                 user_companies=user_companies)
        
        if 'Other' in categories and custom_category:
            categories.remove('Other')
            categories.append(custom_category.strip())
        
        try:
            duration = float(duration_hours)
        except ValueError:
            flash('Invalid duration', 'error')
            return redirect(url_for('main.add_service', company_id=company_id))
        
        new_service = Service(
            service_id=uuid.uuid4(),
            company_id=company_id,
            title=title,
            description=description,
            duration_hours=duration,
            barter_coins_cost=0,
            categories=','.join(categories) if categories else None,
            is_offered=is_offered,
            is_active=True,
            status='active',
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        flash('Service added successfully', 'success')
        return redirect(url_for('main.workspace_services', company_id=company_id))
    
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    usr = User.query.get(uid)
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    user_companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            user_companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'member_count': member_count,
                'is_admin': m.is_admin
            })
    
    return render_template('service_add.html', 
                         company=company,
                         categories=available_categories,
                         current_user=usr,
                         user_companies=user_companies)


@main.route('/service/<uuid:service_id>/edit', methods=['GET', 'POST'])
def edit_service(service_id):
    """Edit an existing service. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    usr = User.query.get(uid)
    service = Service.query.get_or_404(service_id)
    company = Company.query.get(service.company_id)
    
    membership = CompanyMember.query.filter_by(company_id=service.company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to edit this service', 'error')
        return redirect(url_for('main.workspace_services', company_id=service.company_id))
    
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    companies = []
    for mem in memberships:
        comp = Company.query.get(mem.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'member_count': member_count,
                'service_count': service_count,
                'role': 'Admin' if mem.is_admin else 'Member',
                'is_selected': comp.company_id == service.company_id
            })
    
    pending_proposals = DealProposal.query.filter(
        DealProposal.status == 'pending',
        ((DealProposal.from_service_id == service_id) | (DealProposal.to_service_id == service_id))
    ).first()
    
    if pending_proposals:
        flash('Cannot edit service while it is part of a pending negotiation', 'warning')
        return redirect(url_for('main.workspace_services', company_id=service.company_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('categories')
        
        if not title or not description or not category:
            flash('Vul alle velden in', 'error')
            return render_template('service_edit.html',
                                 username=usr.username,
                                 companies=companies,
                                 company=company,
                                 service=service,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_categories=[category] if category else [])
        
        service.title = title
        service.description = description
        service.categories = category
        service.updated_at = datetime.datetime.now(datetime.timezone.utc)
        
        db.session.commit()
        
        flash('Service updated successfully', 'success')
        return redirect(url_for('main.workspace_services', company_id=service.company_id))
    
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    form_categories = service.categories.split(',') if service.categories else []
    
    return render_template('service_edit.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         service=service,
                         categories=available_categories,
                         form_title=service.title,
                         form_description=service.description,
                         form_duration=service.duration_hours,
                         form_categories=form_categories)


@main.route('/service/<uuid:service_id>/delete', methods=['GET', 'POST'])
def delete_service(service_id):
    """Delete a service. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    service = Service.query.get_or_404(service_id)
    company_id = service.company_id
    
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to delete this service', 'error')
        return redirect(url_for('main.company_services', company_id=company_id))
    
    pending_proposals = DealProposal.query.filter(
        DealProposal.status == 'pending',
        ((DealProposal.from_service_id == service_id) | (DealProposal.to_service_id == service_id))
    ).first()
    
    if pending_proposals:
        flash('Cannot delete service while it is part of a pending negotiation', 'warning')
        return redirect(url_for('main.company_services', company_id=company_id))
    
    db.session.delete(service)
    db.session.commit()
    
    flash('Service deleted successfully', 'success')
    return redirect(url_for('main.company_services', company_id=company_id))


# ==================== DEAL ROUTES ====================

@main.route('/proposal/send', methods=['POST'])
def send_proposal():
    """Send a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    
    from_company_id = uuid.UUID(request.form.get('from_company_id'))
    to_company_id = uuid.UUID(request.form.get('to_company_id'))
    from_service_id = uuid.UUID(request.form.get('from_service_id'))
    to_service_id = uuid.UUID(request.form.get('to_service_id'))
    barter_coins = int(request.form.get('barter_coins', 0))
    message = request.form.get('message', '').strip()
    
    membership = CompanyMember.query.filter_by(
        company_id=from_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.workspace_overview', company_id=from_company_id))
    
    company = Company.query.get(from_company_id)
    if barter_coins > 0 and company.barter_coins < barter_coins:
        flash('Insufficient barter coins', 'error')
        return redirect(url_for('main.workspace_overview', company_id=from_company_id))
    
    proposal = DealProposal(
        proposal_id=uuid.uuid4(),
        from_company_id=from_company_id,
        to_company_id=to_company_id,
        from_service_id=from_service_id,
        to_service_id=to_service_id,
        barter_coins_offered=barter_coins,
        message=message,
        status='pending',
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(proposal)
    db.session.commit()
    
    flash('Proposal sent successfully!', 'success')
    return redirect(url_for('main.workspace_overview', company_id=from_company_id))


@main.route('/proposal/<uuid:proposal_id>/accept', methods=['POST'])
def accept_proposal(proposal_id):
    """Accept a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get_or_404(proposal_id)
    
    membership = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))
    
    if proposal.status != 'pending':
        flash('This proposal has already been processed', 'warning')
        return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))
    
    if proposal.barter_coins_offered > 0:
        from_company = Company.query.get(proposal.from_company_id)
        to_company = Company.query.get(proposal.to_company_id)
        
        from_company.barter_coins -= proposal.barter_coins_offered
        to_company.barter_coins += proposal.barter_coins_offered
    
    proposal.status = 'accepted'
    
    active_deal = ActiveDeal(
        active_deal_id=uuid.uuid4(),
        proposal_id=proposal_id,
        from_company_completed=False,
        to_company_completed=False,
        status='in_progress',
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(active_deal)
    db.session.commit()
    
    flash('Proposal accepted! The deal is now active.', 'success')
    return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))


@main.route('/proposal/<uuid:proposal_id>/reject', methods=['POST'])
def reject_proposal(proposal_id):
    """Reject a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get_or_404(proposal_id)
    
    membership = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))
    
    if proposal.status != 'pending':
        flash('This proposal has already been processed', 'warning')
        return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))
    
    proposal.status = 'rejected'
    db.session.commit()
    
    flash('Proposal rejected', 'info')
    return redirect(url_for('main.workspace_overview', company_id=proposal.to_company_id))


@main.route('/company/<uuid:company_id>/deals')
def company_deals(company_id):
    """Show all active deals for a company."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    
    active_deals = ActiveDeal.query.join(DealProposal).filter(
        db.or_(
            DealProposal.from_company_id == company_id,
            DealProposal.to_company_id == company_id
        )
    ).order_by(ActiveDeal.created_at.desc()).all()
    
    in_progress_deals = [d for d in active_deals if d.status == 'in_progress']
    completed_deals = [d for d in active_deals if d.status == 'completed']
    
    can_review = {}
    for deal in completed_deals:
        existing_review = Review.query.filter_by(
            deal_id=deal.active_deal_id,
            reviewer_id=uid
        ).first()
        can_review[deal.active_deal_id] = not existing_review
    
    return render_template('company_deals.html',
                         company=company,
                         in_progress_deals=in_progress_deals,
                         completed_deals=completed_deals,
                         is_admin=membership.is_admin,
                         can_review=can_review)


@main.route('/deal/<uuid:deal_id>/complete', methods=['POST'])
def complete_deal(deal_id):
    """Mark a deal as complete from one company's side. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    active_deal = ActiveDeal.query.get_or_404(deal_id)
    proposal = active_deal.proposal
    
    from_admin = CompanyMember.query.filter_by(
        company_id=proposal.from_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    to_admin = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not from_admin and not to_admin:
        flash('You are not an admin of one of the involved companies', 'error')
        return redirect(url_for('main.index'))
    
    if from_admin:
        active_deal.from_company_completed = True
        company_id = proposal.from_company_id
    else:
        active_deal.to_company_completed = True
        company_id = proposal.to_company_id
    
    if active_deal.from_company_completed and active_deal.to_company_completed:
        active_deal.status = 'completed'
        active_deal.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        ServiceInterest.query.filter_by(
            service_id=proposal.from_service_id,
            company_id=proposal.to_company_id
        ).delete()
        
        ServiceInterest.query.filter_by(
            service_id=proposal.to_service_id,
            company_id=proposal.from_company_id
        ).delete()
        
        flash('Deal completed! Both parties can now leave a review.', 'success')
    else:
        flash('Deal marked as completed on your side.', 'success')
    
    db.session.commit()
    
    return redirect(url_for('main.company_deals', company_id=company_id))


@main.route('/deal/<uuid:deal_id>/review', methods=['GET', 'POST'])
def review_deal(deal_id):
    """Submit a review for a completed deal."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    active_deal = ActiveDeal.query.get_or_404(deal_id)
    proposal = active_deal.proposal
    
    existing_review = Review.query.filter_by(
        deal_id=deal_id,
        reviewer_id=uid
    ).first()
    
    if existing_review:
        flash('You have already reviewed this deal', 'warning')
        if 'company_id' in session:
            return redirect(url_for('main.workspace_overview', company_id=session['company_id']))
        return redirect(url_for('main.index'))
    
    if active_deal.status != 'completed':
        flash('This deal is not yet completed', 'error')
        if 'company_id' in session:
            return redirect(url_for('main.workspace_overview', company_id=session['company_id']))
        return redirect(url_for('main.index'))
    
    from_member = CompanyMember.query.filter_by(
        company_id=proposal.from_company_id,
        user_id=uid
    ).first()
    
    to_member = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid
    ).first()
    
    if not from_member and not to_member:
        flash('You are not a member of one of the involved companies', 'error')
        return redirect(url_for('main.index'))
    
    if from_member:
        reviewed_company_id = proposal.to_company_id
        my_company_id = proposal.from_company_id
    else:
        reviewed_company_id = proposal.from_company_id
        my_company_id = proposal.to_company_id
    
    reviewed_company = Company.query.get(reviewed_company_id)
    
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('main.review_deal', deal_id=deal_id))
        
        review = Review(
            review_id=uuid.uuid4(),
            deal_id=deal_id,
            reviewer_id=uid,
            rating=rating,
            comment=comment,
            reviewed_company_id=reviewed_company_id,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review added successfully!', 'success')
        return redirect(url_for('main.workspace_overview', company_id=my_company_id))
    
    return render_template('review_deal.html',
                         active_deal=active_deal,
                         proposal=proposal,
                         reviewed_company=reviewed_company)


@main.route('/deal/<deal_id>/sign-contract', methods=['GET', 'POST'])
def sign_contract(deal_id):
    """Sign a contract for a barter deal."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    parts = deal_id.split('_')
    if len(parts) != 2:
        return 'Invalid deal ID', 400
    
    interest1 = ServiceInterest.query.get(parts[0])
    interest2 = ServiceInterest.query.get(parts[1])
    
    if not interest1 or not interest2:
        return 'Interests not found', 404
    
    service_a = Service.query.get(interest1.offering_service_id)
    service_b = Service.query.get(interest2.offering_service_id)
    
    if not service_a or not service_b:
        return 'Services not found', 404
    
    if request.method == 'GET':
        company_a = Company.query.get(service_a.company_id)
        company_b = Company.query.get(service_b.company_id)
        return render_template('sign_contract.html',
                             deal_id=deal_id,
                             service_a=service_a,
                             service_b=service_b,
                             company_a=company_a,
                             company_b=company_b)
    
    barter_coins = request.form.get('barter_coins', 0, type=int)
    message = request.form.get('message', '')
    
    user_id = uuid.UUID(session['user_id'])
    
    membership_a = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=service_a.company_id
    ).first()
    
    membership_b = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=service_b.company_id
    ).first()
    
    if membership_a:
        from_service = service_a
        to_service = service_b
        from_company_id = service_a.company_id
        to_company_id = service_b.company_id
    elif membership_b:
        from_service = service_b
        to_service = service_a
        from_company_id = service_b.company_id
        to_company_id = service_a.company_id
    else:
        flash('You are not a member of either company', 'error')
        return redirect(url_for('main.index'))
    
    proposal = DealProposal(
        proposal_id=uuid.uuid4(),
        from_service_id=from_service.service_id,
        to_service_id=to_service.service_id,
        from_company_id=from_company_id,
        to_company_id=to_company_id,
        barter_coins_offered=barter_coins,
        message=message,
        status='pending',
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.session.add(proposal)
    
    db.session.delete(interest1)
    db.session.delete(interest2)
    
    db.session.commit()
    
    flash('Proposal sent successfully!', 'success')
    return redirect(url_for('main.workspace_overview', company_id=from_company_id))


@main.route('/contract/<contract_id>/mark-delivered', methods=['POST'])
def mark_service_delivered(contract_id):
    """Mark your service as delivered in an active deal."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    active_deal = ActiveDeal.query.get(contract_id)
    
    if not active_deal:
        return 'Active deal not found', 404
    
    proposal = DealProposal.query.get(active_deal.proposal_id)
    if not proposal:
        return 'Proposal not found', 404
    
    membership_from = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=proposal.from_company_id
    ).first()
    membership_to = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=proposal.to_company_id
    ).first()
    
    if not (membership_from or membership_to):
        return 'Access denied', 403
    
    if membership_from:
        active_deal.from_company_completed = True
    else:
        active_deal.to_company_completed = True
    
    if active_deal.from_company_completed and active_deal.to_company_completed:
        active_deal.status = 'completed'
        active_deal.completed_at = datetime.datetime.now(datetime.timezone.utc)
    
    db.session.commit()
    flash('Service marked as delivered', 'success')
    
    return redirect(request.referrer or url_for('main.index'))


@main.route('/proposal/<proposal_id>/message', methods=['POST'])
def send_proposal_message(proposal_id):
    """Send a message on a proposal for negotiation."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get(proposal_id)
    
    if not proposal:
        flash('Proposal not found', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    membership_from = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=proposal.from_company_id
    ).first()
    membership_to = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=proposal.to_company_id
    ).first()
    
    if not (membership_from or membership_to):
        flash('You are not part of either company in this proposal', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    if not (membership_from and membership_from.is_admin) and not (membership_to and membership_to.is_admin):
        flash('Only company admins can send messages', 'error')
        return redirect(request.referrer or url_for('main.index'))
