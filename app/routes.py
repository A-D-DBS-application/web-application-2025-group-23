from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, user, Company, CompanyMember, CompanyJoinRequest, Service, BarterDeal, Contract, Review, ServiceInterest, DealProposal, ActiveDeal
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
        flash('Company created — you are admin and member', 'success')
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
                    flash('You are already a member of this company', 'warning')
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
                    flash('Request sent — wait for approval', 'success')
                    return redirect(url_for('main.join_company'))
    return render_template('join_company.html')


@main.route('/companies/my')
def my_companies():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    uid = uuid.UUID(session['user_id'])
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    admin_companies = [m.company for m in memberships if m.is_admin]
    # Show all companies (including admin ones) in member section
    member_companies = [m.company for m in memberships]
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
            flash('You do not have admin rights for this company', 'warning')
            return redirect(url_for('main.view_company', company_id=company_id))
        return 'Forbidden', 403
    company = Company.query.get(company_id)
    members = CompanyMember.query.filter_by(company_id=company_id).all()
    pending = CompanyJoinRequest.query.filter_by(company_id=company_id).all()
    
    # Get mutual interests: services where both companies have expressed interest
    my_services = Service.query.filter_by(company_id=company_id, is_active=True).all()
    mutual_interests = []
    
    for my_service in my_services:
        # Get companies interested in my service
        interests_in_my_service = ServiceInterest.query.filter_by(service_id=my_service.service_id).all()
        
        for interest in interests_in_my_service:
            other_company_id = interest.company_id
            if other_company_id == company_id:
                continue  # Skip own company
            
            # Get services from the other company
            other_services = Service.query.filter_by(company_id=other_company_id, is_active=True).all()
            
            for other_service in other_services:
                # Check if we have someone from our company interested in their service
                mutual = ServiceInterest.query.filter_by(
                    service_id=other_service.service_id,
                    company_id=company_id
                ).first()
                
                if mutual:
                    # Check if there's already an accepted or pending proposal
                    existing_proposal = DealProposal.query.filter(
                        db.or_(
                            db.and_(
                                DealProposal.from_company_id == company_id,
                                DealProposal.to_company_id == other_company_id,
                                DealProposal.from_service_id == my_service.service_id,
                                DealProposal.to_service_id == other_service.service_id,
                                DealProposal.status.in_(['pending', 'accepted'])
                            ),
                            db.and_(
                                DealProposal.from_company_id == other_company_id,
                                DealProposal.to_company_id == company_id,
                                DealProposal.from_service_id == other_service.service_id,
                                DealProposal.to_service_id == my_service.service_id,
                                DealProposal.status.in_(['pending', 'accepted'])
                            )
                        )
                    ).first()
                    
                    if not existing_proposal:
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
    
    return render_template('manage_company.html', 
                         company=company, 
                         members=members, 
                         pending=pending,
                         mutual_interests=mutual_interests,
                         incoming_proposals=incoming_proposals,
                         sent_proposals=sent_proposals)

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
    flash('The user has been added to the company', 'success')
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
    flash('Member removed', 'success')
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
    # delete members, join requests, and company
    CompanyMember.query.filter_by(company_id=company_id).delete()
    CompanyJoinRequest.query.filter_by(company_id=company_id).delete()
    Company.query.filter_by(company_id=company_id).delete()
    db.session.commit()
    flash('Company and all data deleted', 'success')
    return redirect(url_for('main.my_companies'))


@main.route('/company/<uuid:company_id>/activities')
def company_activities(company_id):
    """Show all services/activities for a company. Members only."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    # Check if user is a member of this company
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=uid).first()
    if not membership:
        flash('You are not a member of this company', 'error')
        return redirect(url_for('main.my_companies'))
    
    # Get all services for this company
    services = Service.query.filter_by(company_id=company_id).order_by(Service.created_at.desc()).all()
    
    return render_template('company_activities.html', 
                         company=company, 
                         services=services,
                         is_admin=membership.is_admin)


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
        is_offered = request.form.get('is_offered') == 'true'
        
        if not title or not description or not duration_hours:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('main.add_service', company_id=company_id))
        
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
        return redirect(url_for('main.company_activities', company_id=company_id))
    
    # GET: show form
    available_categories = ['Finance', 'Accounting', 'IT', 'Marketing', 'Legal', 
                           'Design', 'Development', 'Consulting', 'Sales', 'HR', 
                           'Operations', 'Customer Support']
    
    return render_template('service_add.html', 
                         company=company,
                         categories=available_categories)


@main.route('/deals/browse')
def browse_deals():
    """Browse all active services from all companies with filters."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    uid = uuid.UUID(session['user_id'])
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    selected_categories = request.args.getlist('category')
    
    # Base query: ALL active services from ALL companies
    query = Service.query.filter(Service.is_active == True)
    
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
                         company_ratings=company_ratings)


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
    interests = []
    if is_own_company:
        interests = ServiceInterest.query.filter_by(service_id=service_id).all()
    
    return render_template('service_detail.html',
                         service=service,
                         company=company,
                         is_own_company=is_own_company,
                         user_companies=user_companies,
                         existing_interests=existing_interests,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         total_reviews=len(reviews),
                         interests=interests)


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
        return redirect(url_for('main.service_detail', service_id=service_id))
    
    # Check if user's company owns this service
    if service.company_id == company_id:
        flash('You cannot express interest in your own service', 'error')
        return redirect(url_for('main.service_detail', service_id=service_id))
    
    # Check if interest already exists
    existing = ServiceInterest.query.filter_by(
        service_id=service_id,
        company_id=company_id
    ).first()
    
    if existing:
        flash('You have already expressed interest in this service', 'info')
        return redirect(url_for('main.service_detail', service_id=service_id))
    
    # Create interest
    interest = ServiceInterest(
        interest_id=uuid.uuid4(),
        service_id=service_id,
        user_id=uid,
        company_id=company_id,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    db.session.add(interest)
    db.session.commit()
    
    flash('Interest registered successfully!', 'success')
    return redirect(url_for('main.service_detail', service_id=service_id))


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
            deal_id=deal.proposal.from_service_id,  # Using service_id as deal_id for now
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
    
    # Check if deal is completed
    if active_deal.status != 'completed':
        flash('This deal is not yet completed', 'error')
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
        
        # Check if user already reviewed
        existing_review = Review.query.filter_by(
            deal_id=deal_id,
            reviewer_id=uid
        ).first()
        
        if existing_review:
            flash('You have already reviewed this deal', 'warning')
            return redirect(url_for('main.company_deals', company_id=my_company_id))
        
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
        return redirect(url_for('main.company_deals', company_id=my_company_id))
    
    # GET: show review form
    return render_template('review_deal.html',
                         active_deal=active_deal,
                         proposal=proposal,
                         reviewed_company=reviewed_company)
