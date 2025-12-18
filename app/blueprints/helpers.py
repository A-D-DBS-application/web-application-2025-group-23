import datetime
import uuid
from functools import wraps
from flask import request, session, redirect, url_for, flash
from ..models import User, Company, CompanyMember, Service, DealProposal, ActiveDeal, TradeRequest, TradeflowView, db

def get_current_user():
    """Helper to load current user from session; returns None when invalid."""
    if 'user_id' not in session:
        return None
    try:
        user_id = uuid.UUID(session['user_id'])
        return User.query.get(user_id)
    except Exception:
        return None


def require_valid_user():
    """Redirect to login when session user is missing/invalid; returns response or None."""
    user = get_current_user()
    if not user:
        session.clear()
        flash('Your session has expired. Please log in again.', 'info')
        return redirect(url_for('main.login'))
    return None


def _require_login():
    """Redirect to login when no active session."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return None


def login_required(view):
    """Decorator to ensure the session is authenticated before continuing."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if (resp := _require_login()):
            return resp
        return view(*args, **kwargs)
    return wrapper


def _require_company_member(company_id):
    """Return (company, None) when user is member; otherwise (None, redirect)."""
    company = Company.query.get_or_404(company_id)
    user_id = session.get('user_id')
    if not user_id:
        return None, redirect(url_for('main.login'))
    member = CompanyMember.query.filter_by(company_id=company_id, user_id=uuid.UUID(user_id)).first()
    if not member:
        flash('Access denied', 'error')
        return None, redirect(url_for('main.my_companies'))
    # Store selected company in session for navigation
    session['selected_company_id'] = str(company_id)
    return company, None


def _member_or_403(company_id, require_admin=False):
    """Lightweight membership check for actions; returns (user_id, membership, response)."""
    if (resp := _require_login()):
        return None, None, resp
    user_id = uuid.UUID(session['user_id'])
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership or (require_admin and not membership.is_admin):
        return user_id, membership, ('Forbidden', 403)
    return user_id, membership, None


def company_member_required(require_admin=False, company_kw='company_id'):
    """Decorator enforcing company membership (and optional admin rights)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if company_kw not in kwargs:
                return ('Company id missing', 400)
            company_id = kwargs[company_kw]
            user_id, membership, resp = _member_or_403(company_id, require_admin=require_admin)
            if resp:
                return resp
            # Attach membership for downstream use
            kwargs['membership'] = membership
            kwargs['current_user_id'] = user_id
            return view(*args, **kwargs)
        return wrapper
    return decorator


def _ensure_request_for_company(trade_request, company_id):
    """Redirect when a trade request does not target the given company."""
    if trade_request.requested_service.company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))
    return None


def _ensure_proposal_involves_company(proposal, company_id):
    """Redirect when the proposal is unrelated to the company."""
    if proposal.from_company_id != company_id and proposal.to_company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))
    return None


def _parse_int(value, default=0):
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def _create_active_deal_from_proposal(proposal_id):
    return ActiveDeal(
        active_deal_id=uuid.uuid4(),
        proposal_id=proposal_id,
        from_company_completed=False,
        to_company_completed=False,
        status='in_progress',
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )


def _sidebar_companies(user_id, selected_company_id=None, include_counts=True):
    memberships = CompanyMember.query.filter_by(user_id=user_id).all()
    companies = []
    for m in memberships:
        comp = Company.query.get(m.company_id)
        if not comp:
            continue
        member_count = CompanyMember.query.filter_by(company_id=comp.company_id).count() if include_counts else None
        service_count = Service.query.filter_by(company_id=comp.company_id).count() if include_counts else None
        companies.append({
            'company_id': comp.company_id,
            'name': comp.name,
            'description': getattr(comp, 'description', None),
            'role': 'Admin' if m.is_admin else 'Member',
            'is_admin': m.is_admin,
            'member_count': member_count,
            'service_count': service_count,
            'is_selected': comp.company_id == selected_company_id
        })
    return companies


def _workspace_context(company_id, require_admin=False):
    """Common load for workspace pages; returns (user, membership, company, companies, member_count, service_count) or a response."""
    if (resp := _require_login()):
        return None, None, None, None, None, None, resp
    user_id = uuid.UUID(session['user_id'])
    user = User.query.get(user_id)
    membership = CompanyMember.query.filter_by(company_id=company_id, user_id=user_id).first()
    if not membership or (require_admin and not membership.is_admin):
        return None, None, None, None, None, None, ('Forbidden', 403)
    company = Company.query.get_or_404(company_id)
    companies = _sidebar_companies(user_id, company_id)
    member_count = CompanyMember.query.filter_by(company_id=company_id).count()
    service_count = Service.query.filter_by(company_id=company_id).count()
    return user, membership, company, companies, member_count, service_count, None


def _marketplace_context(selected_company_id_str=None, redirect_missing=None, logged_in_uid=None, require_company=False):
    """Load marketplace user, companies, and selected company with optional company selection."""
    if logged_in_uid is None:
        if 'user_id' not in session:
            return None, None, None, None
        try:
            logged_in_uid = uuid.UUID(session['user_id'])
        except ValueError:
            session.clear()
            return None, None, None, None

    uid = logged_in_uid
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    user_companies = [membership.company for membership in memberships]
    
    selected_company_id = None
    if selected_company_id_str:
        try:
            selected_company_id = uuid.UUID(selected_company_id_str)
            session['marketplace_company_id'] = str(selected_company_id)
            session['selected_company_id'] = str(selected_company_id)
        except ValueError:
            selected_company_id = None
    elif 'marketplace_company_id' in session:
        try:
            selected_company_id = uuid.UUID(session['marketplace_company_id'])
        except ValueError:
            selected_company_id = None

    selected_company = None
    if selected_company_id:
        selected_company = next((c for c in user_companies if c and c.company_id == selected_company_id), None)
        if not selected_company and require_company:
            flash('Select a valid company to browse the marketplace', 'warning')
            if redirect_missing:
                return uid, user_companies, None, redirect(url_for(redirect_missing))

    return uid, user_companies, selected_company, None


def marketplace_company_required(view):
    """Decorator to enforce marketplace company selection for logged-in users."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        uid = uuid.UUID(session['user_id']) if 'user_id' in session else None
        uid, companies, selected, resp = _marketplace_context(
            request.args.get('company_id'),
            logged_in_uid=uid,
        )
        if resp:
            return resp
        kwargs['marketplace_user_id'] = uid
        kwargs['marketplace_companies'] = companies
        kwargs['selected_company'] = selected
        return view(*args, **kwargs)
    return wrapper


def mark_tradeflow_section_viewed(company_id, section):
    """Mark a tradeflow section as viewed by the current user."""
    user_id = session.get('user_id')
    if not user_id:
        return
    
    try:
        user_uuid = uuid.UUID(user_id)
        company_uuid = uuid.UUID(str(company_id))
    except (ValueError, AttributeError):
        return
    
    # Find existing view record or create new one
    view = TradeflowView.query.filter_by(
        company_id=company_uuid,
        user_id=user_uuid,
        section=section
    ).first()
    
    if view:
        view.last_viewed_at = datetime.datetime.now(datetime.timezone.utc)
    else:
        view = TradeflowView(
            view_id=uuid.uuid4(),
            company_id=company_uuid,
            user_id=user_uuid,
            section=section,
            last_viewed_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(view)
    
    db.session.commit()


def get_tradeflow_unread_counts(company_id):
    """Get unread counts for all tradeflow sections."""
    user_id = session.get('user_id')
    if not user_id:
        return {}
    
    try:
        user_uuid = uuid.UUID(user_id)
        company_uuid = uuid.UUID(str(company_id))
    except (ValueError, AttributeError):
        return {}
    
    counts = {}
    
    # Get last viewed timestamps for each section
    views = TradeflowView.query.filter_by(
        company_id=company_uuid,
        user_id=user_uuid
    ).all()
    
    last_viewed = {view.section: view.last_viewed_at for view in views}
    
    # Count incoming requests created after last view
    incoming_cutoff = last_viewed.get('incoming', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['incoming'] = TradeRequest.query.filter(
        TradeRequest.requested_service.has(company_id=company_uuid),
        TradeRequest.status == 'active',
        TradeRequest.created_at > incoming_cutoff
    ).count()
    
    # Count you requested items created after last view
    you_requested_cutoff = last_viewed.get('you_requested', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['you_requested'] = TradeRequest.query.filter(
        TradeRequest.requesting_company_id == company_uuid,
        TradeRequest.status == 'active',
        TradeRequest.created_at > you_requested_cutoff
    ).count()
    
    # Count archived requests using archived_at timestamp (fallback to created_at for old records)
    archived_cutoff = last_viewed.get('archived', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    # For old records without archived_at, use created_at as a fallback
    counts['archived'] = TradeRequest.query.filter(
        ((TradeRequest.requesting_company_id == company_uuid) | 
         (TradeRequest.requested_service.has(company_id=company_uuid))),
        TradeRequest.status == 'archived',
        db.or_(
            db.and_(TradeRequest.archived_at != None, TradeRequest.archived_at > archived_cutoff),
            db.and_(TradeRequest.archived_at == None, TradeRequest.created_at > archived_cutoff)
        )
    ).count()
    
    # Count matches
    matches_cutoff = last_viewed.get('matches', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['matches'] = DealProposal.query.filter(
        DealProposal.status == 'matched',
        ((DealProposal.from_company_id == company_uuid) | 
         (DealProposal.to_company_id == company_uuid)),
        DealProposal.created_at > matches_cutoff
    ).count()
    
    # Count awaiting signature
    awaiting_signature_cutoff = last_viewed.get('awaiting_signature', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['awaiting_signature'] = DealProposal.query.filter(
        DealProposal.to_company_id == company_uuid,
        DealProposal.status == 'pending',
        DealProposal.created_at > awaiting_signature_cutoff
    ).count()
    
    # Count awaiting other party
    awaiting_other_cutoff = last_viewed.get('awaiting_other_party', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['awaiting_other_party'] = DealProposal.query.filter(
        DealProposal.from_company_id == company_uuid,
        DealProposal.status == 'pending',
        DealProposal.created_at > awaiting_other_cutoff
    ).count()
    
    # Count ongoing deals
    ongoing_cutoff = last_viewed.get('ongoing', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['ongoing'] = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_uuid) | 
         (DealProposal.to_company_id == company_uuid)),
        ActiveDeal.status == 'in_progress',
        ActiveDeal.created_at > ongoing_cutoff
    ).count()
    
    # Count completed deals
    completed_cutoff = last_viewed.get('completed', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    counts['completed'] = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_uuid) | 
         (DealProposal.to_company_id == company_uuid)),
        ActiveDeal.status == 'completed',
        ActiveDeal.created_at > completed_cutoff
    ).count()
    
    return counts

