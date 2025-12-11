import datetime
import uuid

from flask import request, redirect, url_for, render_template, session, flash
from sqlalchemy import func

from ..models import db, Service, Review, TradeRequest
from .core import main
from .helpers import _marketplace_context, login_required

PAGE_LIMIT = 60  # cap result set to keep marketplace snappy


@main.route('/marketplace')
def marketplace():
    """Main marketplace page for logged-in users with company selection."""
    uid, user_companies, selected_company, resp = _marketplace_context(request.args.get('company_id'))
    if resp:
        return resp
    user_company_ids = [c.company_id for c in user_companies]

    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    try:
        page = int(request.args.get('page', 1) or 1)
    except ValueError:
        page = 1
    page = max(page, 1)

    # Base query: active services from OTHER companies
    query = Service.query.filter(
        Service.is_active == True,  # noqa: E712
        ~Service.company_id.in_(user_company_ids)
    )

    # Apply search filter (including category search)
    if search_query:
        query = query.filter(
            db.or_(
                Service.title.ilike(f'%{search_query}%'),
                Service.description.ilike(f'%{search_query}%'),
                Service.categories.ilike(f'%{search_query}%')
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
        search_query=search_query,
        category_filter=category_filter,
        service_ratings=service_ratings,
    )


@main.route('/marketplace/public')
def marketplace_public():
    """Public marketplace page for non-logged-in users."""
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    try:
        page = int(request.args.get('page', 1) or 1)
    except ValueError:
        page = 1
    page = max(page, 1)

    # Base query
    query = Service.query.filter_by(is_active=True)

    # Apply search filter
    if search_query:
        query = query.filter(
            db.or_(
                Service.title.ilike(f'%{search_query}%'),
                Service.description.ilike(f'%{search_query}%')
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
    )


@main.route('/marketplace/service/<uuid:service_id>')
def marketplace_service_view(service_id):
    """Service detail page for logged-in users."""
    if 'user_id' not in session:
        return redirect(url_for('main.marketplace_service_public', service_id=service_id))
    uid = uuid.UUID(session['user_id'])
    uid, user_companies, selected_company, resp = _marketplace_context(
        logged_in_uid=uid, redirect_missing='main.marketplace'
    )
    if resp:
        flash('Please select a company first to view service details', 'info')
        return resp
    service = Service.query.get_or_404(service_id)

    reviews = Review.query.filter_by(reviewed_service_id=service_id).order_by(Review.created_at.desc()).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

    return render_template(
        'marketplace-trade-request.html',
        service=service,
        selected_company=selected_company,
        reviews=reviews,
        avg_rating=avg_rating,
    )


@main.route('/marketplace/service/<uuid:service_id>/public')
def marketplace_service_public(service_id):
    """Service detail page for non-logged-in users."""
    service = Service.query.get_or_404(service_id)
    reviews = Review.query.filter_by(reviewed_service_id=service_id).order_by(Review.created_at.desc()).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

    return render_template(
        'marketplace-trade-request-not-logged-in.html',
        service=service,
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
        logged_in_uid=uid, redirect_missing='main.marketplace'
    )
    if resp:
        flash('Please select a company first', 'error')
        return resp
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
