from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, user, Company, CompanyMember, CompanyJoinRequest, Service, BarterDeal, Contract, Review, ServiceInterest, DealProposal, ActiveDeal, Message, Deliverable
import uuid
import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    Serve the public start page for anonymous users, redirect logged-in users to my_companies
    """
    if 'user_id' in session:
        # Logged-in users should go to my_companies page
        return redirect(url_for('main.my_companies'))
    # Anonymous users see the start page
    return render_template('start.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        if user.query.filter_by(username=username).first() is None:
            new_user = user(
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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usr = user.query.filter_by(username=username).first()
        if usr and check_password_hash(usr.password_hash, password):
            # UUID als string in session
            session['user_id'] = str(usr.user_id)
            return redirect(url_for('main.my_companies'))
        flash('Invalid username or password', 'error')
        return render_template('login.html')
    return render_template('login.html')

@main.route('/logout', methods=['GET', 'POST'])
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
        usr.location = request.form.get('location', usr.location)
        usr.job_description = request.form.get('jobdescription', usr.job_description)
        # `company_name` is not a column on the `user` model — keep only supported fields
        # Do not modify CompanyMember.is_admin from the profile page; admin status
        # is controlled when creating companies and via manage pages.
        db.session.commit()
        return redirect(url_for('main.profile_settings'))
    return render_template('profile.html', user=usr)


@main.route('/user/<uuid:user_id>')
def view_user_profile(user_id):
    """View public profile of another user."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    viewed_user = user.query.get_or_404(user_id)
    
    return render_template('user_profile.html', user=viewed_user)


@main.route('/my-companies')
def my_companies():
    """Landing page after login showing user's companies."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    
    # Get all companies for this user
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for membership in memberships:
        company = Company.query.get(membership.company_id)
        if company:
            # Count members and services
            member_count = CompanyMember.query.filter_by(company_id=company.company_id).count()
            service_count = Service.query.filter_by(company_id=company.company_id).count()
            
            companies.append({
                'company_id': company.company_id,
                'name': company.name,
                'description': getattr(company, 'description', None),
                'role': 'Admin' if membership.is_admin else 'Member',
                'is_admin': membership.is_admin,
                'member_count': member_count,
                'service_count': service_count
            })
    
    return render_template('my_companies.html', 
                         username=usr.username,
                         companies=companies)


@main.route('/onboarding')
def onboarding():
    """Onboarding page to create or join a company."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for membership in memberships:
        company = Company.query.get(membership.company_id)
        if company:
            member_count = CompanyMember.query.filter_by(company_id=company.company_id).count()
            service_count = Service.query.filter_by(company_id=company.company_id).count()
            
            companies.append({
                'company_id': company.company_id,
                'name': company.name,
                'role': 'Admin' if membership.is_admin else 'Member',
                'member_count': member_count,
                'service_count': service_count
            })
    
    return render_template('onboarding_get_started.html', 
                         username=usr.username,
                         companies=companies)


@main.route('/company/create', methods=['GET', 'POST'])
def create_company():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for membership in memberships:
        comp = Company.query.get(membership.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if membership.is_admin else 'Member',
                'member_count': member_count,
                'service_count': service_count
            })
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        website = request.form.get('website')
        
        if not name:
            flash('Company name is required', 'error')
            return render_template('create_company.html', username=usr.username, companies=companies)
        
        company = Company(
            company_id=uuid.uuid4(),
            name=name,
            description=description,
            created_at=datetime.datetime.now(),
            join_code=uuid.uuid4().hex[:8]
        )
        db.session.add(company)
        db.session.flush()

        # Make creator an admin
        member = CompanyMember(
            member_id=uuid.uuid4(),
            company_id=company.company_id,
            user_id=user_id,
            member_role='founder',
            is_admin=True,
            created_at=datetime.datetime.now(),
        )
        db.session.add(member)
        db.session.commit()
        flash('Company created — you are admin and member', 'success')
        return redirect(url_for('main.workspace_overview', company_id=company.company_id))
    
    return render_template('create_company.html', username=usr.username, companies=companies)


@main.route('/company/join', methods=['GET', 'POST'])
def join_company():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for membership in memberships:
        comp = Company.query.get(membership.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if membership.is_admin else 'Member',
                'member_count': member_count,
                'service_count': service_count
            })
    
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
                existing = CompanyMember.query.filter_by(company_id=company.company_id, user_id=user_id).first()
                if existing:
                    flash('You are already a member of this company', 'warning')
                    return redirect(url_for('main.join_company'))
                else:
                    # create a join request
                    req = CompanyJoinRequest(
                        request_id=uuid.uuid4(),
                        company_id=company.company_id,
                        user_id=user_id,
                        created_at=datetime.datetime.now(),
                    )
                    db.session.add(req)
                    db.session.commit()
                    flash('Request sent — wait for approval', 'success')
                    return redirect(url_for('main.my_companies'))
    
    return render_template('join_company.html', username=usr.username, companies=companies)


@main.route('/workspace/<uuid:company_id>')
@main.route('/workspace/<uuid:company_id>/overview')
def workspace_overview(company_id):
    """Company workspace - Overview tab."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership:
        return 'Forbidden', 403
    
    company = Company.query.get_or_404(company_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if m.is_admin else 'Member',
                'is_admin': m.is_admin,
                'member_count': member_count,
                'service_count': service_count,
                'is_selected': (comp.company_id == company_id)
            })
    
    # Company stats
    member_count = CompanyMember.query.filter_by(company_id=company_id).count()
    service_count = Service.query.filter_by(company_id=company_id).count()
    
    return render_template('company_workspace_overview.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         is_admin=membership.is_admin,
                         member_count=member_count,
                         service_count=service_count)


@main.route('/workspace/<uuid:company_id>/members')
def workspace_members(company_id):
    """Company workspace - Members tab."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership:
        return 'Forbidden', 403
    
    company = Company.query.get_or_404(company_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if m.is_admin else 'Member',
                'is_admin': m.is_admin,
                'member_count': member_count,
                'service_count': service_count,
                'is_selected': (comp.company_id == company_id)
            })
    
    # Get members
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    from .models import user as User
    for m in members:
        m.user_obj = User.query.get(m.user_id)
    
    # Get pending join requests (if admin)
    pending = []
    if membership.is_admin:
        pending = CompanyJoinRequest.query.filter_by(company_id=company_id).all()
        for req in pending:
            req.user_obj = User.query.get(req.user_id)
    
    # Company stats
    member_count = CompanyMember.query.filter_by(company_id=company_id).count()
    service_count = Service.query.filter_by(company_id=company_id).count()
    
    return render_template('company_workspace_members.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         is_admin=membership.is_admin,
                         current_user_id=user_id,
                         members=members,
                         pending=pending,
                         member_count=member_count,
                         service_count=service_count)


@main.route('/workspace/<uuid:company_id>/services')
def workspace_services(company_id):
    """Company workspace - Services tab."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership:
        return 'Forbidden', 403
    
    company = Company.query.get_or_404(company_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if m.is_admin else 'Member',
                'is_admin': m.is_admin,
                'member_count': member_count,
                'service_count': service_count,
                'is_selected': (comp.company_id == company_id)
            })
    
    # Get services
    services = Service.query.filter_by(company_id=company_id).all()
    
    # Company stats
    member_count = CompanyMember.query.filter_by(company_id=company_id).count()
    service_count = Service.query.filter_by(company_id=company_id).count()
    
    return render_template('company_workspace_services.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         is_admin=membership.is_admin,
                         services=services,
                         member_count=member_count,
                         service_count=service_count)


@main.route('/workspace/<uuid:company_id>/service/<uuid:service_id>/view')
def workspace_service_view(company_id, service_id):
    """Public view of a service within workspace context."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership:
        return 'Forbidden', 403
    
    service = Service.query.get_or_404(service_id)
    company = Company.query.get_or_404(company_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'member_count': member_count,
                'is_admin': m.is_admin,
                'is_selected': (comp.company_id == company_id)
            })
    
    return render_template('workspace_service_public_view.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         service=service,
                         is_admin=membership.is_admin)


@main.route('/company/<uuid:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    """Edit company details - admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    usr = user.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id, is_admin=True).first()
    if not membership:
        return 'Forbidden - Admin only', 403
    
    company = Company.query.get_or_404(company_id)
    
    # Get all companies for sidebar
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if comp:
            member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count()
            service_count = Service.query.filter_by(company_id=comp.company_id).count()
            companies.append({
                'company_id': comp.company_id,
                'name': comp.name,
                'role': 'Admin' if m.is_admin else 'Member',
                'is_admin': m.is_admin,
                'member_count': member_count,
                'service_count': service_count,
                'is_selected': (comp.company_id == company_id)
            })
    
    if request.method == 'POST':
        company.name = request.form.get('name', company.name)
        company.description = request.form.get('description', company.description)
        # TODO: Add category and website fields to Company model if needed
        
        db.session.commit()
        flash('Company updated successfully', 'success')
        return redirect(url_for('main.workspace_overview', company_id=company_id))
    
    return render_template('edit_company.html',
                         username=usr.username,
                         companies=companies,
                         company=company,
                         is_admin=True)


@main.route('/company/<uuid:company_id>')
def view_company(company_id):
    """Company view with management features for admins."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        return 'Forbidden', 403
    
    company = Company.query.get(company_id)
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    from .models import user as User
    for m in members:
        m.user_obj = User.query.get(m.user_id)
    
    # If admin, get additional management data
    pending = []
    mutual_interests = []
    incoming_proposals = []
    sent_proposals = []
    
    if membership.is_admin:
        pending = CompanyJoinRequest.query.filter_by(company_id=company_id).all()
        
        # Get mutual interests
        my_services = Service.query.filter_by(company_id=company_id, is_active=True).all()
        for my_service in my_services:
            interests_in_my_service = ServiceInterest.query.filter_by(service_id=my_service.service_id).all()
            
            for interest in interests_in_my_service:
                other_company_id = interest.company_id
                if other_company_id == company_id:
                    continue
                
                other_services = Service.query.filter_by(company_id=other_company_id, is_active=True).all()
                
                for other_service in other_services:
                    mutual = ServiceInterest.query.filter_by(
                        service_id=other_service.service_id,
                        company_id=company_id
                    ).first()
                    
                    if mutual:
                        existing_proposal = DealProposal.query.filter(
                            db.or_(
                                db.and_(
                                    DealProposal.from_company_id == company_id,
                                    DealProposal.to_company_id == other_company_id,
                                    DealProposal.from_service_id == my_service.service_id,
                                    DealProposal.to_service_id == other_service.service_id,
                                    DealProposal.status == 'pending'
                                ),
                                db.and_(
                                    DealProposal.from_company_id == other_company_id,
                                    DealProposal.to_company_id == company_id,
                                    DealProposal.from_service_id == other_service.service_id,
                                    DealProposal.to_service_id == my_service.service_id,
                                    DealProposal.status == 'pending'
                                )
                            )
                        ).first()
                        
                        if not existing_proposal:
                            active_deal_check = db.session.query(ActiveDeal).join(DealProposal).filter(
                                db.or_(
                                    db.and_(
                                        DealProposal.from_company_id == company_id,
                                        DealProposal.to_company_id == other_company_id,
                                        DealProposal.from_service_id == my_service.service_id,
                                        DealProposal.to_service_id == other_service.service_id,
                                        ActiveDeal.status == 'in_progress'
                                    ),
                                    db.and_(
                                        DealProposal.from_company_id == other_company_id,
                                        DealProposal.to_company_id == company_id,
                                        DealProposal.from_service_id == other_service.service_id,
                                        DealProposal.to_service_id == my_service.service_id,
                                        ActiveDeal.status == 'in_progress'
                                    )
                                )
                            ).first()
                            
                            if not active_deal_check:
                                mutual_interests.append({
                                    'my_service': my_service,
                                    'other_service': other_service,
                                    'other_company': Company.query.get(other_company_id)
                                })
        
        # Get incoming proposals
        incoming_proposals = DealProposal.query.filter_by(
            to_company_id=company_id,
            status='pending'
        ).all()
        
        # Get sent proposals
        sent_proposals = DealProposal.query.filter_by(
            from_company_id=company_id
        ).all()
    
    return render_template('company_view.html', 
                         company=company, 
                         members=members, 
                         is_admin=membership.is_admin,
                         pending=pending,
                         mutual_interests=mutual_interests,
                         incoming_proposals=incoming_proposals,
                         sent_proposals=sent_proposals)

# Alias for backward compatibility
company_view = view_company


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
    flash('The user has been added to the company', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/transfer/<uuid:member_id>', methods=['POST'])
def transfer_admin(company_id, member_id):
    """Promote a member to admin. Admins can promote others."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    # Ensure caller is admin
    current_admin = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not current_admin:
        return 'Forbidden', 403
    
    target = CompanyMember.query.get(member_id)
    if not target or target.company_id != company_id:
        return 'Not found', 404
    
    if target.is_admin:
        flash('This user is already an admin', 'warning')
        return redirect(url_for('main.manage_company', company_id=company_id))
    
    # Promote target to admin
    target.is_admin = True
    # Demote current admin
    current_admin.is_admin = False
    db.session.commit()
    flash(f'{target.user_obj.username if hasattr(target, "user_obj") and target.user_obj else "User"} is now an admin. You are now a regular member.', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/demote/<uuid:member_id>', methods=['POST'])
def demote_admin(company_id, member_id):
    """Demote an admin to regular member. Any admin can demote other admins."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    # Ensure caller is admin
    current_admin = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not current_admin:
        return 'Forbidden', 403
    
    target = CompanyMember.query.get(member_id)
    if not target or target.company_id != company_id:
        return 'Not found', 404
    
    if not target.is_admin:
        flash('This user is not an admin', 'warning')
        return redirect(url_for('main.manage_company', company_id=company_id))
    
    # Check if this is the last admin
    admin_count = CompanyMember.query.filter_by(company_id=company_id, is_admin=True).count()
    if admin_count <= 1:
        flash('Cannot demote the last admin. Promote someone else first.', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    
    # Demote target to regular member
    target.is_admin = False
    db.session.commit()
    flash(f'{target.user_obj.username if hasattr(target, "user_obj") and target.user_obj else "User"} is now a regular member', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


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
    # disallow removing admins - they must be demoted first
    if member.is_admin:
        flash('Cannot remove admin users. Demote them first.', 'error')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    # do not allow removing yourself (use leave company instead)
    if str(member.user_id) == session.get('user_id'):
        flash("Use 'Leave Company' to remove yourself", 'warning')
        return redirect(url_for('main.workspace_members', company_id=company_id))
    db.session.delete(member)
    db.session.commit()
    flash('Member removed', 'success')
    return redirect(url_for('main.workspace_members', company_id=company_id))


@main.route('/company/<uuid:company_id>/leave', methods=['POST'])
def leave_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        return 'Not a member', 400
    
    # Check if user is admin
    if membership.is_admin:
        # Check if there are other admins
        other_admins = CompanyMember.query.filter_by(company_id=company_id, is_admin=True).filter(CompanyMember.user_id != uid).count()
        if other_admins == 0:
            flash('You are the only admin. Please promote another member to admin before leaving, or delete the company.', 'error')
            return redirect(url_for('main.workspace_members', company_id=company_id))
    
    db.session.delete(membership)
    db.session.commit()
    flash('You have left the company', 'success')
    return redirect(url_for('main.my_companies'))


@main.route('/company/<uuid:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    admin_membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid, is_admin=True).first()
    if not admin_membership:
        return 'Forbidden', 403
    
    # Delete all related data
    # Delete service interests related to this company's services
    company_services = Service.query.filter_by(company_id=company_id).all()
    for service in company_services:
        ServiceInterest.query.filter_by(service_id=service.service_id).delete()
        ServiceInterest.query.filter_by(offering_service_id=service.service_id).delete()
    
    # Delete services
    Service.query.filter_by(company_id=company_id).delete()
    
    # Delete deal proposals
    DealProposal.query.filter(
        db.or_(
            DealProposal.from_company_id == company_id,
            DealProposal.to_company_id == company_id
        )
    ).delete()
    
    # Delete members and join requests
    CompanyMember.query.filter_by(company_id=company_id).delete()
    CompanyJoinRequest.query.filter_by(company_id=company_id).delete()
    
    # Delete company
    Company.query.filter_by(company_id=company_id).delete()
    
    db.session.commit()
    flash('Company and all data deleted', 'success')
    return redirect(url_for('main.index'))


@main.route('/company/<uuid:company_id>/service/add', methods=['GET', 'POST'])
def add_service(company_id):
    """Add a new service to a company. Members only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    # Check if user is a member of this company
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        duration_hours = request.form.get('duration_hours')
        categories = request.form.getlist('categories')  # Multiple checkboxes
        custom_category = request.form.get('custom_category')  # Custom category input
        is_offered = request.form.get('is_offered') == 'true'
        
        # Get user info for error responses
        usr = user.query.get(uid)
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
        
        # Validation: check all required fields first
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
        
        # If "Other" is selected but custom_category is empty, show error
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
        
        # Replace "Other" with the custom category value
        if 'Other' in categories and custom_category:
            categories.remove('Other')
            categories.append(custom_category.strip())
        
        try:
            duration = float(duration_hours)
        except ValueError:
            flash('Invalid duration', 'error')
            return redirect(url_for('main.add_service', company_id=company_id))
        
        # Create new service
        new_service = Service(
            service_id=uuid.uuid4(),
            company_id=company_id,
            title=title,
            description=description,
            duration_hours=duration,
            barter_coins_cost=0,  # Default to 0, can be edited later
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
    
    # GET: show form
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    # Get user info and companies for sidebar
    usr = user.query.get(uid)
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
    service = Service.query.get_or_404(service_id)
    company = Company.query.get(service.company_id)
    
    # Check if user is admin of this company
    membership = CompanyMember.query.filter_by(company_id=service.company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to edit this service', 'error')
        return redirect(url_for('main.workspace_services', company_id=service.company_id))
    
    # Check if service is in a pending proposal (locked)
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
        duration_hours = request.form.get('duration_hours')
        categories = request.form.getlist('categories')
        custom_category = request.form.get('custom_category')
        
        # Validation: check all required fields
        if not title or not description or not duration_hours:
            flash('Vul dit veld in.', 'error')
            return render_template('service_edit.html',
                                 company=company,
                                 service=service,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_duration=duration_hours,
                                 form_categories=categories)
        
        # If "Other" is selected but custom_category is empty, show error
        if 'Other' in categories and not custom_category:
            flash('Vul dit veld in.', 'error')
            return render_template('service_edit.html',
                                 company=company,
                                 service=service,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_duration=duration_hours,
                                 form_categories=categories)
        
        # Replace "Other" with the custom category value
        if 'Other' in categories and custom_category:
            categories.remove('Other')
            categories.append(custom_category.strip())
        
        try:
            duration = float(duration_hours)
        except ValueError:
            flash('Invalid duration', 'error')
            return render_template('service_edit.html',
                                 company=company,
                                 service=service,
                                 categories=['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 'Design', 'Development', 'Consulting', 'Sales', 'HR', 'Operations', 'Customer Support'],
                                 form_title=title,
                                 form_description=description,
                                 form_duration=duration_hours,
                                 form_categories=categories)
        
        # Update service
        service.title = title
        service.description = description
        service.duration_hours = duration
        service.categories = ','.join(categories) if categories else None
        service.updated_at = datetime.datetime.now(datetime.timezone.utc)
        
        db.session.commit()
        
        flash('Service updated successfully', 'success')
        return redirect(url_for('main.workspace_services', company_id=service.company_id))
    
    # GET: show form with current values
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    # Parse existing categories
    form_categories = service.categories.split(',') if service.categories else []
    
    return render_template('service_edit.html',
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
    
    # Check if user is admin of this company
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership or not membership.is_admin:
        flash('You do not have permission to delete this service', 'error')
        return redirect(url_for('main.company_services', company_id=company_id))
    
    # Check if service is in a pending proposal (locked)
    pending_proposals = DealProposal.query.filter(
        DealProposal.status == 'pending',
        ((DealProposal.from_service_id == service_id) | (DealProposal.to_service_id == service_id))
    ).first()
    
    if pending_proposals:
        flash('Cannot delete service while it is part of a pending negotiation', 'warning')
        return redirect(url_for('main.company_services', company_id=company_id))
    
    # Delete the service
    db.session.delete(service)
    db.session.commit()
    
    flash('Service deleted successfully', 'success')
    return redirect(url_for('main.company_services', company_id=company_id))


@main.route('/deals/browse')
@main.route('/deals/browse/<uuid:company_id>')
def browse_deals(company_id=None):
    """Browse all active services from OTHER companies only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    
    # Save company_id to session if provided
    if company_id:
        session['last_marketplace_company'] = str(company_id)
    
    # Get all company IDs where the user is a member
    user_company_ids = db.session.query(CompanyMember.company_id).filter_by(user_id=uid).all()
    user_company_ids = [cid[0] for cid in user_company_ids]  # Extract UUID from tuples
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    selected_categories = request.args.getlist('category')
    
    # Base query: active services from OTHER companies (NOT the user's own companies)
    query = Service.query.filter(
        Service.is_active == True,
        ~Service.company_id.in_(user_company_ids)  # Exclude user's companies
    )
    
    # Apply search filter
    if search_query:
        query = query.filter(
            db.or_(
                Service.title.ilike(f'%{search_query}%'),
                Service.description.ilike(f'%{search_query}%')
            )
        )
    
    # Apply category filter
    if selected_categories:
        # Services can have multiple categories, check if any match
        category_filters = []
        for cat in selected_categories:
            category_filters.append(Service.categories.ilike(f'%{cat}%'))
        query = query.filter(db.or_(*category_filters))
    
    services = query.order_by(Service.created_at.desc()).all()
    
    # Calculate average ratings for companies
    company_ratings = {}
    for service in services:
        if service.company_id not in company_ratings:
            # Get all reviews for this company
            reviews = db.session.query(Review).filter_by(reviewed_company_id=service.company_id).all()
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)
                company_ratings[service.company_id] = round(avg_rating, 1)
            else:
                company_ratings[service.company_id] = None
    
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    return render_template('browse_deals.html',
                         services=services,
                         categories=available_categories,
                         selected_categories=selected_categories,
                         search_query=search_query,
                         company_ratings=company_ratings,
                         selected_company_id=company_id)


@main.route('/service/<uuid:service_id>')
def service_detail(service_id):
    """View full details of a service."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    service = Service.query.get_or_404(service_id)
    company = service.company
    
    # Check if user is member of this company
    is_own_company = CompanyMember.query.filter_by(company_id=company.company_id, user_id=uid).first() is not None
    
    # Get user's companies for interest button
    user_companies = CompanyMember.query.filter_by(user_id=uid).all()
    
    # Get the selected company from query parameter (from marketplace) or session
    selected_company_id = request.args.get('company_id')
    selected_company = None
    if selected_company_id:
        try:
            selected_company = uuid.UUID(selected_company_id)
        except:
            selected_company = None
    elif 'last_marketplace_company' in session:
        # Use last company from session if no company_id in URL
        try:
            selected_company = uuid.UUID(session['last_marketplace_company'])
        except:
            selected_company = None
    
    # Check if user has already expressed interest from any of their companies
    existing_interests = {}
    for membership in user_companies:
        interest = ServiceInterest.query.filter_by(
            service_id=service_id,
            company_id=membership.company_id
        ).first()
        if interest:
            existing_interests[membership.company_id] = True
    
    # Get all reviews for this company
    reviews = Review.query.filter_by(reviewed_company_id=company.company_id).all()
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
    
    # Get interested companies (for service owner to see)
    # Only show interests that don't have a completed deal
    interests = []
    if is_own_company:
        all_interests = ServiceInterest.query.filter_by(service_id=service_id).all()
        
        for interest in all_interests:
            # Check if there's a completed deal with this interest
            completed_deal = db.session.query(ActiveDeal).join(DealProposal).filter(
                db.or_(
                    db.and_(
                        DealProposal.from_company_id == interest.company_id,
                        DealProposal.from_service_id == service_id,
                        ActiveDeal.status == 'completed'
                    ),
                    db.and_(
                        DealProposal.to_company_id == interest.company_id,
                        DealProposal.to_service_id == service_id,
                        ActiveDeal.status == 'completed'
                    )
                )
            ).first()
            
            # Only add interest if there's no completed deal
            if not completed_deal:
                interests.append(interest)
    
    # Get user's services from their selected company (for offering in exchange)
    my_services = []
    if selected_company:
        my_services = Service.query.filter_by(company_id=selected_company, is_active=True).all()
    
    # Get referrer information (where user came from)
    referrer = request.args.get('referrer')
    back_link = None
    if referrer == 'requests' and selected_company_id:
        back_link = url_for('main.company_requests', company_id=selected_company_id)
    
    return render_template('service_detail.html',
                         service=service,
                         company=company,
                         is_own_company=is_own_company,
                         user_companies=user_companies,
                         existing_interests=existing_interests,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         total_reviews=len(reviews),
                         interests=interests,
                         selected_company_id=selected_company,
                         my_services=my_services,
                         back_link=back_link)


@main.route('/service/<uuid:service_id>/interest', methods=['POST'])
def express_interest(service_id):
    """Express interest in a service from one of user's companies."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    service = Service.query.get_or_404(service_id)
    company_id_str = request.form.get('company_id')
    
    if not company_id_str:
        flash('Please select a company', 'error')
        return redirect(url_for('main.service_detail', service_id=service_id))
    
    company_id = uuid.UUID(company_id_str)
    
    # Verify user is member of selected company
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.service_detail', service_id=service_id, company_id=company_id))
    
    # Check if user's company owns this service
    if service.company_id == company_id:
        flash('You cannot express interest in your own service', 'error')
        return redirect(url_for('main.service_detail', service_id=service_id, company_id=company_id))
    
    # Check if interest already exists AND there's an active deal
    existing = ServiceInterest.query.filter_by(
        service_id=service_id,
        company_id=company_id
    ).first()
    
    if existing:
        # Check if there's an active (in_progress) deal involving this interest
        active_deal_exists = db.session.query(ActiveDeal).join(DealProposal).filter(
            db.or_(
                db.and_(
                    DealProposal.from_company_id == company_id,
                    DealProposal.from_service_id == service_id,
                    ActiveDeal.status == 'in_progress'
                ),
                db.and_(
                    DealProposal.to_company_id == company_id,
                    DealProposal.to_service_id == service_id,
                    ActiveDeal.status == 'in_progress'
                )
            )
        ).first()
        
        # Only block if there's an active deal
        if active_deal_exists:
            flash('You have already expressed interest in this service', 'info')
            return redirect(url_for('main.service_detail', service_id=service_id, company_id=company_id))
        else:
            # Interest exists but no active deal, delete old interest and allow new one
            db.session.delete(existing)
    
    # Get a service from this company to offer (use first active service)
    my_services = Service.query.filter_by(company_id=company_id, is_active=True).all()
    if not my_services:
        flash('Your company needs to have at least one active service to express interest', 'error')
        return redirect(url_for('main.service_detail', service_id=service_id, company_id=company_id))
    
    # Use the first service as the offering
    offering_service = my_services[0]
    
    # Create interest
    interest = ServiceInterest(
        interest_id=uuid.uuid4(),
        service_id=service_id,
        company_id=company_id,
        offering_service_id=offering_service.service_id,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(interest)
    db.session.commit()
    
    # Remember this company in session for future visits
    session['last_marketplace_company'] = str(company_id)
    
    flash('Interest registered successfully!', 'success')
    return redirect(url_for('main.service_detail', service_id=service_id, company_id=company_id))


@main.route('/proposal/send', methods=['POST'])
def send_proposal():
    """Send a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    
    # Get form data
    from_company_id = uuid.UUID(request.form.get('from_company_id'))
    to_company_id = uuid.UUID(request.form.get('to_company_id'))
    from_service_id = uuid.UUID(request.form.get('from_service_id'))
    to_service_id = uuid.UUID(request.form.get('to_service_id'))
    barter_coins = int(request.form.get('barter_coins', 0))
    message = request.form.get('message', '').strip()
    
    # Verify user is admin of from_company
    membership = CompanyMember.query.filter_by(
        company_id=from_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.manage_company', company_id=from_company_id))
    
    # Verify company has enough barter coins
    company = Company.query.get(from_company_id)
    if barter_coins > 0 and company.barter_coins < barter_coins:
        flash('Insufficient barter coins', 'error')
        return redirect(url_for('main.manage_company', company_id=from_company_id))
    
    # Create proposal
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
    return redirect(url_for('main.manage_company', company_id=from_company_id))


@main.route('/proposal/<uuid:proposal_id>/accept', methods=['POST'])
def accept_proposal(proposal_id):
    """Accept a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get_or_404(proposal_id)
    
    # Verify user is admin of the receiving company
    membership = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))
    
    if proposal.status != 'pending':
        flash('This proposal has already been processed', 'warning')
        return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))
    
    # Transfer barter coins if applicable
    if proposal.barter_coins_offered > 0:
        from_company = Company.query.get(proposal.from_company_id)
        to_company = Company.query.get(proposal.to_company_id)
        
        from_company.barter_coins -= proposal.barter_coins_offered
        to_company.barter_coins += proposal.barter_coins_offered
    
    # Update proposal status
    proposal.status = 'accepted'
    
    # Create active deal
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
    return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))


@main.route('/proposal/<uuid:proposal_id>/reject', methods=['POST'])
def reject_proposal(proposal_id):
    """Reject a deal proposal. Admin only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get_or_404(proposal_id)
    
    # Verify user is admin of the receiving company
    membership = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))
    
    if proposal.status != 'pending':
        flash('This proposal has already been processed', 'warning')
        return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))
    
    proposal.status = 'rejected'
    db.session.commit()
    
    flash('Proposal rejected', 'info')
    return redirect(url_for('main.manage_company', company_id=proposal.to_company_id))


@main.route('/company/<uuid:company_id>/deals')
def company_deals(company_id):
    """Show all active deals for a company. Members can view, admins can mark complete."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    # Check if user is a member of this company
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    
    # Get all active deals where this company is involved
    active_deals = ActiveDeal.query.join(DealProposal).filter(
        db.or_(
            DealProposal.from_company_id == company_id,
            DealProposal.to_company_id == company_id
        )
    ).order_by(ActiveDeal.created_at.desc()).all()
    
    # Separate in-progress and completed deals
    in_progress_deals = [d for d in active_deals if d.status == 'in_progress']
    completed_deals = [d for d in active_deals if d.status == 'completed']
    
    # Check which deals can be reviewed
    can_review = {}
    for deal in completed_deals:
        # Check if user has already reviewed this deal
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
    
    # Determine which company the user is admin of
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
    
    # Mark as completed from the appropriate side
    if from_admin:
        active_deal.from_company_completed = True
        company_id = proposal.from_company_id
    else:
        active_deal.to_company_completed = True
        company_id = proposal.to_company_id
    
    # Check if both sides have marked as complete
    if active_deal.from_company_completed and active_deal.to_company_completed:
        active_deal.status = 'completed'
        active_deal.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        # Reset interests for both services to allow future deals
        # Delete interests from both companies in these services
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
    
    # Check if user already reviewed
    existing_review = Review.query.filter_by(
        deal_id=deal_id,
        reviewer_id=uid
    ).first()
    
    if existing_review:
        flash('You have already reviewed this deal', 'warning')
        if 'company_id' in session:
            return redirect(url_for('main.company_requests', company_id=session['company_id']))
        return redirect(url_for('main.index'))
    
    # Check if deal is completed
    if active_deal.status != 'completed':
        flash('This deal is not yet completed', 'error')
        if 'company_id' in session:
            return redirect(url_for('main.company_requests', company_id=session['company_id']))
        return redirect(url_for('main.index'))
    
    # Determine which company the user is reviewing
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
    
    # Determine which company to review (the other one)
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
        
        # Create review
        review = Review(
            review_id=uuid.uuid4(),
            deal_id=deal_id,  # Using active_deal_id as deal_id
            reviewer_id=uid,
            rating=rating,
            comment=comment,
            reviewed_company_id=reviewed_company_id,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review added successfully!', 'success')
        return redirect(url_for('main.company_requests', company_id=my_company_id))
    
    # GET: show review form
    return render_template('review_deal.html',
                         active_deal=active_deal,
                         proposal=proposal,
                         reviewed_company=reviewed_company)


@main.route('/support')
def support():
    """
    Support page
    """
    return render_template('support.html')


@main.route('/about-us')
def about_us():
    """
    About Us page
    """
    return render_template('about_us.html')


@main.route('/company-choice')
def company_choice():
    """
    Page to choose between creating or joining a company
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('company_choice.html')


@main.route('/select-company-marketplace')
def select_company_for_marketplace():
    """
    Select which company to use for browsing marketplace
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    
    # Get all companies where user is a member
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for membership in memberships:
        company = Company.query.get(membership.company_id)
        if company:
            companies.append({
                'company_id': company.company_id,
                'name': company.name,
                'description': getattr(company, 'description', None)
            })
    
    return render_template('select_company_marketplace.html', companies=companies)


@main.route('/company/<uuid:company_id>/services')
def company_services(company_id):
    """
    View services for a company
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    company = Company.query.get(company_id)
    if not company:
        return 'Company not found', 404
    
    # Check if user is member
    user_id = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=company_id
    ).first()
    
    if not membership:
        return 'Access denied', 403
    
    services = Service.query.filter_by(company_id=company_id).all()
    
    return render_template('company_services.html', 
                         company=company, 
                         services=services,
                         is_admin=membership.is_admin)


@main.route('/company/<uuid:company_id>/requests')
def company_requests(company_id):
    """
    View all requests for a company (4 tabs)
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    company = Company.query.get(company_id)
    if not company:
        return 'Company not found', 404
    
    user_id = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=company_id
    ).first()
    
    if not membership or not membership.is_admin:
        return 'Access denied - Admin only', 403
    
    # Outgoing requests (You Requested) - only show pending requests
    outgoing = []
    my_services = Service.query.filter_by(company_id=company_id).all()
    for service in my_services:
        proposals = DealProposal.query.filter_by(
            from_service_id=service.service_id,
            status='pending'  # Only show pending requests
        ).all()
        for prop in proposals:
            from_service = Service.query.get(prop.from_service_id)
            to_service = Service.query.get(prop.to_service_id)
            target_company = Company.query.get(to_service.company_id) if to_service else None
            
            # Get all messages for this proposal, including initial message if it exists
            messages = Message.query.filter_by(proposal_id=prop.proposal_id).order_by(Message.created_at).all()
            message_list = []
            
            # Add initial message first if it exists
            if prop.message:
                my_company = Company.query.get(prop.from_company_id)
                message_list.append({
                    'content': prop.message,
                    'company_name': my_company.name if my_company else 'Unknown',
                    'timestamp': prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else 'Unknown'
                })
            
            # Then add all follow-up messages
            for msg in messages:
                msg_company = Company.query.get(msg.from_company_id)
                message_list.append({
                    'content': msg.content,
                    'company_name': msg_company.name if msg_company else 'Unknown',
                    'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else 'Unknown'
                })
            
            outgoing.append({
                'proposal_id': prop.proposal_id,
                'my_service_id': from_service.service_id if from_service else None,
                'my_service_name': from_service.title if from_service else 'Unknown',
                'my_service_description': from_service.description if from_service else '',
                'their_service_id': to_service.service_id if to_service else None,
                'their_service_name': to_service.title if to_service else 'Unknown',
                'their_service_description': to_service.description if to_service else '',
                'company_name': target_company.name if target_company else 'Unknown',
                'status': prop.status,
                'status_display': prop.status.title(),
                'messages': message_list
            })
    
    # Incoming requests - only show pending requests
    incoming = []
    for service in my_services:
        proposals = DealProposal.query.filter_by(
            to_service_id=service.service_id,
            status='pending'  # Only show pending requests
        ).all()
        for prop in proposals:
            from_service = Service.query.get(prop.from_service_id)
            to_service = Service.query.get(prop.to_service_id)
            offering_company = Company.query.get(from_service.company_id) if from_service else None
            
            # Get all messages for this proposal, including initial message if it exists
            messages = Message.query.filter_by(proposal_id=prop.proposal_id).order_by(Message.created_at).all()
            message_list = []
            
            # Add initial message first if it exists
            if prop.message:
                message_list.append({
                    'content': prop.message,
                    'company_name': offering_company.name if offering_company else 'Unknown',
                    'timestamp': prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else 'Unknown'
                })
            
            # Then add all follow-up messages
            for msg in messages:
                msg_company = Company.query.get(msg.from_company_id)
                message_list.append({
                    'content': msg.content,
                    'company_name': msg_company.name if msg_company else 'Unknown',
                    'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else 'Unknown'
                })
            
            incoming.append({
                'proposal_id': prop.proposal_id,
                'their_service_id': from_service.service_id if from_service else None,
                'their_service_name': from_service.title if from_service else 'Unknown',
                'their_service_description': from_service.description if from_service else '',
                'my_service_id': to_service.service_id if to_service else None,
                'my_service_name': to_service.title if to_service else 'Unknown',
                'my_service_description': to_service.description if to_service else '',
                'from_company': offering_company.name if offering_company else 'Unknown',
                'from_company_id': offering_company.company_id if offering_company else None,
                'status': prop.status,
                'status_display': prop.status.title(),
                'barter_coins_offered': prop.barter_coins_offered,
                'message': prop.message,
                'messages': message_list
            })
    
    # Barterdeal Overview (mutual interests)
    # Logic: Find all interests where:
    # 1. Another company is interested in my service (offering their service)
    # 2. I am interested in one of their services (offering my service)
    barter_deals = []
    seen_pairs = set()  # To avoid duplicates
    
    # Get all interests where someone is interested in my services
    all_interests_in_my_services = ServiceInterest.query.join(
        Service, ServiceInterest.service_id == Service.service_id
    ).filter(Service.company_id == company_id).all()
    
    for their_interest in all_interests_in_my_services:
        # their_interest: They want my service (service_id), offering their service (offering_service_id)
        their_company_id = their_interest.company_id
        my_service_they_want = Service.query.get(their_interest.service_id)
        their_service_they_offer = Service.query.get(their_interest.offering_service_id)
        
        if not their_service_they_offer:
            continue
        
        # Now check: Do I have an interest in any of their services?
        my_interests_in_their_services = ServiceInterest.query.join(
            Service, ServiceInterest.service_id == Service.service_id
        ).filter(
            ServiceInterest.company_id == company_id,
            Service.company_id == their_company_id
        ).all()
        
        for my_interest in my_interests_in_their_services:
            # Check if this creates a mutual deal
            pair_id = tuple(sorted([str(their_interest.interest_id), str(my_interest.interest_id)]))
            if pair_id in seen_pairs:
                continue
            seen_pairs.add(pair_id)
            
            their_service_i_want = Service.query.get(my_interest.service_id)
            my_service_i_offer = Service.query.get(my_interest.offering_service_id)
            their_company = Company.query.get(their_company_id)
            
            if their_service_they_offer and my_service_i_offer:
                barter_deals.append({
                    'deal_id': f"{their_interest.interest_id}_{my_interest.interest_id}",
                    'service1_name': my_service_i_offer.title,
                    'service1_description': my_service_i_offer.description,
                    'company1_name': company.name,
                    'service2_name': their_service_they_offer.title,
                    'service2_description': their_service_they_offer.description,
                    'company2_name': their_company.name if their_company else 'Unknown',
                    'interest1_id': their_interest.interest_id,
                    'interest2_id': my_interest.interest_id
                })
    
    # My Contracts - using ActiveDeal system
    # Show contracts that are in_progress OR completed but not yet reviewed by current user
    contracts = []
    active_deals = ActiveDeal.query.filter(
        ActiveDeal.status.in_(['in_progress', 'completed'])
    ).all()
    
    for active_deal in active_deals:
        proposal = DealProposal.query.get(active_deal.proposal_id)
        if not proposal:
            continue
            
        # Check if this company is involved in this deal
        if proposal.from_company_id != company_id and proposal.to_company_id != company_id:
            continue
        
        # Get services and companies
        from_service = Service.query.get(proposal.from_service_id)
        to_service = Service.query.get(proposal.to_service_id)
        from_company = Company.query.get(proposal.from_company_id)
        to_company = Company.query.get(proposal.to_company_id)
        
        # Determine which is "my" service and which is "their" service
        is_from_company = (proposal.from_company_id == company_id)
        my_service = from_service if is_from_company else to_service
        their_service = to_service if is_from_company else from_service
        other_company = to_company if is_from_company else from_company
        
        # Check if current user has reviewed this deal
        user_reviewed = Review.query.filter_by(
            deal_id=active_deal.active_deal_id,
            reviewer_id=uuid.UUID(session['user_id'])
        ).first() is not None
        
        # If completed and user has reviewed, don't show this contract
        if active_deal.status == 'completed' and user_reviewed:
            continue
        
        contracts.append({
            'contract_id': active_deal.active_deal_id,
            'service1_name': my_service.title if my_service else 'Unknown',
            'service2_name': their_service.title if their_service else 'Unknown',
            'other_company': other_company.name if other_company else 'Unknown',
            'status': active_deal.status,
            'status_display': active_deal.status.title().replace('_', ' '),
            'signed_date': active_deal.created_at.strftime('%Y-%m-%d') if active_deal.created_at else 'Unknown',
            'your_service_delivered': active_deal.from_company_completed if is_from_company else active_deal.to_company_completed,
            'their_service_delivered': active_deal.to_company_completed if is_from_company else active_deal.from_company_completed,
            'reviewed': user_reviewed,
            'proposal_id': proposal.proposal_id
        })
    
    return render_template('company_requests.html',
                         company=company,
                         outgoing_requests=outgoing,
                         incoming_requests=incoming,
                         barter_deals=barter_deals,
                         contracts=contracts)


@main.route('/request/<proposal_id>/cancel', methods=['POST'])
def cancel_request(proposal_id):
    """
    Cancel an outgoing request
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    proposal = DealProposal.query.get(proposal_id)
    if proposal:
        db.session.delete(proposal)
        db.session.commit()
        flash('Request cancelled', 'success')
    
    return redirect(request.referrer or url_for('main.index'))


@main.route('/request/<proposal_id>/accept', methods=['POST'])
def accept_request(proposal_id):
    """
    Accept an incoming request - creates an ActiveDeal
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    proposal = DealProposal.query.get(proposal_id)
    if not proposal:
        flash('Proposal not found', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Verify user is admin of the receiving company
    uid = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(
        company_id=proposal.to_company_id,
        user_id=uid,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You are not an admin of this company', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    if proposal.status != 'pending':
        flash('This proposal has already been processed', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    # Transfer barter coins if applicable
    if proposal.barter_coins_offered > 0:
        from_company = Company.query.get(proposal.from_company_id)
        to_company = Company.query.get(proposal.to_company_id)
        
        if from_company and to_company:
            from_company.barter_coins -= proposal.barter_coins_offered
            to_company.barter_coins += proposal.barter_coins_offered
    
    # Update proposal status
    proposal.status = 'accepted'
    
    # Create active deal
    active_deal = ActiveDeal(
        active_deal_id=uuid.uuid4(),
        proposal_id=uuid.UUID(proposal_id),
        from_company_completed=False,
        to_company_completed=False,
        status='in_progress',
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(active_deal)
    db.session.commit()
    
    flash('Request accepted! The deal is now active in My Contracts.', 'success')
    return redirect(request.referrer or url_for('main.index'))


@main.route('/request/<proposal_id>/decline', methods=['POST'])
def decline_request(proposal_id):
    """
    Decline an incoming request
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    proposal = DealProposal.query.get(proposal_id)
    if proposal:
        proposal.status = 'declined'
        db.session.commit()
        flash('Request declined', 'success')
    
    return redirect(request.referrer or url_for('main.index'))


@main.route('/deal/<deal_id>/sign-contract', methods=['GET', 'POST'])
def sign_contract(deal_id):
    """
    Sign a contract for a barter deal - shows form to add barter coins and message
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # Parse deal_id (format: interest1_id_interest2_id)
    parts = deal_id.split('_')
    if len(parts) != 2:
        return 'Invalid deal ID', 400
    
    interest1 = ServiceInterest.query.get(parts[0])
    interest2 = ServiceInterest.query.get(parts[1])
    
    if not interest1 or not interest2:
        return 'Interests not found', 404
    
    # Get services from the interests
    service_a = Service.query.get(interest1.offering_service_id)
    service_b = Service.query.get(interest2.offering_service_id)
    
    if not service_a or not service_b:
        return 'Services not found', 404
    
    # If GET request, show the contract signing form
    if request.method == 'GET':
        company_a = Company.query.get(service_a.company_id)
        company_b = Company.query.get(service_b.company_id)
        return render_template('sign_contract.html',
                             deal_id=deal_id,
                             service_a=service_a,
                             service_b=service_b,
                             company_a=company_a,
                             company_b=company_b)
    
    # POST request - process the contract signing
    barter_coins = request.form.get('barter_coins', 0, type=int)
    message = request.form.get('message', '')
    
    # Get current user's company
    user_id = uuid.UUID(session['user_id'])
    
    # Determine which company the user belongs to
    membership_a = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=service_a.company_id
    ).first()
    
    membership_b = CompanyMember.query.filter_by(
        user_id=user_id,
        company_id=service_b.company_id
    ).first()
    
    # Determine from/to based on which company user is from
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
    
    # Create DealProposal with PENDING status (goes to "You Requested" and "Incoming Requests")
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
    
    # Remove the interests since they're now converted to a proposal
    db.session.delete(interest1)
    db.session.delete(interest2)
    
    db.session.commit()
    
    flash('Proposal sent successfully!', 'success')
    return redirect(url_for('main.company_requests', company_id=from_company_id))


@main.route('/contract/<contract_id>/mark-delivered', methods=['POST'])
def mark_service_delivered(contract_id):
    """
    Mark your service as delivered in an active deal
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    active_deal = ActiveDeal.query.get(contract_id)
    
    if not active_deal:
        return 'Active deal not found', 404
    
    proposal = DealProposal.query.get(active_deal.proposal_id)
    if not proposal:
        return 'Proposal not found', 404
    
    # Find which company the user belongs to
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
    
    # Mark appropriate service as delivered
    if membership_from:
        active_deal.from_company_completed = True
    else:
        active_deal.to_company_completed = True
    
    # Check if both delivered
    if active_deal.from_company_completed and active_deal.to_company_completed:
        active_deal.status = 'completed'
        active_deal.completed_at = datetime.datetime.now(datetime.timezone.utc)
    
    db.session.commit()
    flash('Service marked as delivered', 'success')
    
    return redirect(request.referrer or url_for('main.index'))


@main.route('/proposal/<proposal_id>/message', methods=['POST'])
def send_proposal_message(proposal_id):
    """
    Send a message on a proposal for negotiation
    """
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_id = uuid.UUID(session['user_id'])
    proposal = DealProposal.query.get(proposal_id)
    
    if not proposal:
        flash('Proposal not found', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Find which company the user belongs to
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
    
    # Only allow admins to send messages
    if not (membership_from and membership_from.is_admin) and not (membership_to and membership_to.is_admin):
        flash('Only company admins can send messages', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    message_content = request.form.get('message_content', '').strip()
    if not message_content:
        flash('Message cannot be empty', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    # Determine which company is sending the message
    from_company_id = proposal.from_company_id if membership_from else proposal.to_company_id
    
    # Create and save message
    message = Message(
        message_id=uuid.uuid4(),
        proposal_id=uuid.UUID(proposal_id),
        from_company_id=from_company_id,
        content=message_content,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(message)
    db.session.commit()
    
    flash('Message sent', 'success')
    return redirect(request.referrer or url_for('main.index'))


@main.route('/contract/<contract_id>/write-review', methods=['GET', 'POST'])
def write_review(contract_id):
    """Removed - use review_deal route instead"""
    return redirect(url_for('main.index'))


