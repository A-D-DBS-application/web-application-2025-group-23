import datetime
import uuid

from flask import request, redirect, url_for, render_template, session, flash
from sqlalchemy import func

from ..fairness import record_service_view
from ..models import db, Service, Review, TradeRequest, Company
from .core import main
from .helpers import _marketplace_context, login_required

PAGE_LIMIT = 60  # cap result set to keep marketplace snappy


@main.route('/marketplace')
def marketplace():
    """Main marketplace page with optional company selection via sidebar."""
    # Get user info and companies (no redirect if not logged in or no company)
    uid = None
    user_companies = []
    selected_company = None
    
    if 'user_id' in session:
        try:
            uid = uuid.UUID(session['user_id'])
            from ..models import CompanyMember
            memberships = CompanyMember.query.filter_by(user_id=uid).all()
            user_companies = [membership.company for membership in memberships]
            
            # Check for selected company in session or query param
            selected_company_id_str = request.args.get('company_id') or session.get('marketplace_company_id')
            if selected_company_id_str:
                try:
                    selected_company_id = uuid.UUID(selected_company_id_str)
                    selected_company = next((c for c in user_companies if c and c.company_id == selected_company_id), None)
                    if selected_company:
                        session['marketplace_company_id'] = str(selected_company_id)
                        session['selected_company_id'] = str(selected_company_id)
                except ValueError:
                    pass
        except ValueError:
            session.clear()
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    try:
        page = int(request.args.get('page', 1) or 1)
    except ValueError:
        page = 1
    page = max(page, 1)

    # Base query: active services
    query = Service.query.join(Company, Service.company_id == Company.company_id).filter(
        Service.is_active == True  # noqa: E712
    )
    
    # Exclude services from user's companies if logged in
    if user_companies:
        user_company_ids = [c.company_id for c in user_companies]
        query = query.filter(~Service.company_id.in_(user_company_ids))

    # Apply search filter (including category search and company name)
    if search_query:
        query = query.filter(
            db.or_(
                Service.title.ilike(f'%{search_query}%'),
                Service.description.ilike(f'%{search_query}%'),
                Service.categories.ilike(f'%{search_query}%'),
                Company.name.ilike(f'%{search_query}%')
            )
        )

    # Apply category filter
    if category_filter:
        query = query.filter(Service.categories.ilike(f'%{category_filter}%'))

    pagination = query.order_by(Service.created_at.desc()).paginate(
        page=page,
        per_page=PAGE_LIMIT,
        error_out=False,
    )
    services = pagination.items

    # Aggregate ratings in one query to avoid N+1 lookups
    service_ratings = {}
    if services:
        rating_rows = (
            db.session.query(
                Review.reviewed_service_id.label('service_id'),
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.review_id).label('count_rating'),
            )
            .filter(Review.reviewed_service_id.in_([s.service_id for s in services]))
            .group_by(Review.reviewed_service_id)
            .all()
        )
        for row in rating_rows:
            service_ratings[str(row.service_id)] = {
                'avg': float(row.avg_rating),
                'count': row.count_rating,
            }

    return render_template(
        'marketplace.html',
        services=services,
        pagination=pagination,
        selected_company=selected_company,
        user_companies=user_companies,
        is_logged_in=(uid is not None),
        search_query=search_query,
        category_filter=category_filter,
        service_ratings=service_ratings,
    )


@main.route('/marketplace/public')
def marketplace_public():
    """Public marketplace page for non-logged-in users and logged-in users without a company."""
    # Check if user is logged in
    is_logged_in = 'user_id' in session
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    try:
        page = int(request.args.get('page', 1) or 1)
    except ValueError:
        page = 1
    page = max(page, 1)

    # Base query
    query = Service.query.join(Company, Service.company_id == Company.company_id).filter(Service.is_active == True)  # noqa: E712

    # Apply search filter (including company name)
    if search_query:
        query = query.filter(
            db.or_(
                Service.title.ilike(f'%{search_query}%'),
                Service.description.ilike(f'%{search_query}%'),
                Company.name.ilike(f'%{search_query}%')
            )
        )

    # Apply category filter
    if category_filter:
        query = query.filter(Service.categories.ilike(f'%{category_filter}%'))

    pagination = query.order_by(Service.created_at.desc()).paginate(
        page=page,
        per_page=PAGE_LIMIT,
        error_out=False,
    )
    services = pagination.items

    # Aggregate ratings in one query to avoid N+1 lookups
    service_ratings = {}
    if services:
        rating_rows = (
            db.session.query(
                Review.reviewed_service_id.label('service_id'),
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.review_id).label('count_rating'),
            )
            .filter(Review.reviewed_service_id.in_([s.service_id for s in services]))
            .group_by(Review.reviewed_service_id)
            .all()
        )
        for row in rating_rows:
            service_ratings[str(row.service_id)] = {
                'avg': float(row.avg_rating),
                'count': row.count_rating,
            }

    return render_template(
        'marketplace-public.html',
        services=services,
        pagination=pagination,
        search_query=search_query,
        category_filter=category_filter,
        service_ratings=service_ratings,
        is_logged_in=is_logged_in,
    )


@main.route('/marketplace/service/<uuid:service_id>/trade')
def marketplace_service_view(service_id):
    """Service detail page for logged-in users with trade request form."""
    if 'user_id' not in session:
        return redirect(url_for('main.marketplace_service_detail_view', service_id=service_id))
    uid = uuid.UUID(session['user_id'])
    
    # Get company info without redirecting
    from ..models import CompanyMember
    memberships = CompanyMember.query.filter_by(user_id=uid).all()
    user_companies = [membership.company for membership in memberships]
    
    # Try to get selected company from query param or session
    selected_company = None
    company_id_param = request.args.get('company_id')
    if company_id_param:
        try:
            selected_company_id = uuid.UUID(company_id_param)
            selected_company = next((c for c in user_companies if c and c.company_id == selected_company_id), None)
            if selected_company:
                session['marketplace_company_id'] = str(selected_company_id)
        except ValueError:
            pass
    elif 'marketplace_company_id' in session:
        try:
            selected_company_id = uuid.UUID(session['marketplace_company_id'])
            selected_company = next((c for c in user_companies if c and c.company_id == selected_company_id), None)
        except ValueError:
            pass
    
    service = Service.query.get_or_404(service_id)

    record_service_view(service.service_id)

    reviews = Review.query.filter_by(reviewed_service_id=service_id).order_by(Review.created_at.desc()).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

    return render_template(
        'marketplace-trade-request.html',
        service=service,
        selected_company=selected_company,
        user_companies=user_companies,
        reviews=reviews,
        avg_rating=avg_rating,
    )


@main.route('/marketplace/service/<uuid:service_id>/request', methods=['POST'])
@login_required
def marketplace_request_service(service_id):
    """Handle trade request submission from marketplace."""
    uid = uuid.UUID(session['user_id'])
    service = Service.query.get_or_404(service_id)
    uid, user_companies, selected_company, resp = _marketplace_context(
        logged_in_uid=uid, require_company=True
    )
    if not selected_company:
        flash('Please select a company first', 'error')
        return redirect(url_for('main.marketplace'))
    company_id = selected_company.company_id

    try:
        validity_days = int(request.form.get('validity_days', 14))
        if validity_days not in [7, 14, 30, 60, 90]:
            validity_days = 14
    except Exception:
        validity_days = 14

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(days=validity_days)

    trade_request = TradeRequest(
        request_id=uuid.uuid4(),
        requesting_company_id=company_id,
        requested_service_id=service_id,
        validity_days=validity_days,
        status='active',
        created_at=now,
        expires_at=expires_at,
    )

    db.session.add(trade_request)
    db.session.commit()

    flash('Trade request sent successfully!', 'success')
    return redirect(url_for('main.marketplace'))


@main.route('/marketplace/select-company/<uuid:company_id>')
@login_required
def marketplace_select_company(company_id):
    """Select a company for marketplace browsing."""
    uid = uuid.UUID(session['user_id'])
    from ..models import CompanyMember
    
    # Verify user is member of this company
    membership = CompanyMember.query.filter_by(user_id=uid, company_id=company_id).first()
    if not membership:
        flash('You are not a member of that company', 'error')
        return redirect(url_for('main.marketplace'))
    
    # Store in session
    session['marketplace_company_id'] = str(company_id)
    session['selected_company_id'] = str(company_id)
    
    # Check for redirect_to parameter
    redirect_to = request.args.get('redirect_to')
    if redirect_to:
        return redirect(redirect_to)
    
    return redirect(url_for('main.marketplace'))


@main.route('/marketplace/clear-company')
@login_required
def marketplace_clear_company():
    """Clear company selection for marketplace."""
    session.pop('marketplace_company_id', None)
    
    # Check for redirect_to parameter
    redirect_to = request.args.get('redirect_to')
    if redirect_to:
        return redirect(redirect_to)
    
    return redirect(url_for('main.marketplace'))
