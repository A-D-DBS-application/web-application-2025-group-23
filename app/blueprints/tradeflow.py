import datetime
import uuid

from flask import request, redirect, url_for, render_template, session, flash

from ..models import db, Service, TradeRequest, DealProposal, ActiveDeal, Review
from .core import main
from .helpers import (
    _create_active_deal_from_proposal,
    _ensure_proposal_involves_company,
    _ensure_request_for_company,
    _parse_int,
    _require_company_member,
    _require_login,
)


@main.route('/tradeflow/<uuid:company_id>/incoming-requests', methods=['GET'])
def tradeflow_incoming_requests(company_id):
    """View incoming trade requests for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    incoming_requests = TradeRequest.query.join(Service).filter(
        Service.company_id == company_id,
        TradeRequest.status == 'active'
    ).all()

    return render_template('tradeflow_incoming_requests.html', company=company, incoming_requests=incoming_requests)


@main.route('/tradeflow/<uuid:company_id>/incoming-requests/<uuid:request_id>/select-return', methods=['GET', 'POST'])
def tradeflow_select_return(company_id, request_id):
    """Select a return service for an incoming trade request"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    incoming_request = TradeRequest.query.get_or_404(request_id)

    if (resp := _ensure_request_for_company(incoming_request, company_id)):
        return resp

    if request.method == 'POST':
        selected_service_id = request.form.get('selected_service_id')
        if not selected_service_id:
            flash('Please select a service', 'error')
            return redirect(url_for('main.tradeflow_select_return', company_id=company_id, request_id=request_id))

        return_service = Service.query.get_or_404(selected_service_id)

        proposal = DealProposal(
            proposal_id=uuid.uuid4(),
            from_company_id=incoming_request.requesting_company_id,
            to_company_id=company_id,
            from_service_id=incoming_request.requested_service_id,
            to_service_id=selected_service_id,
            status='matched',
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        db.session.add(proposal)
        incoming_request.status = 'archived'
        db.session.commit()

        flash('Match created! You can now make an offer.', 'success')
        return redirect(url_for('main.tradeflow_match_made', company_id=company_id))

    services = Service.query.filter_by(company_id=incoming_request.requesting_company_id).all()

    return render_template(
        'tradeflow_select_return.html',
        company=company,
        incoming_request=incoming_request,
        services=services,
        request_id=request_id,
    )


@main.route('/tradeflow/<uuid:company_id>/incoming-requests/<uuid:request_id>/select-return/<uuid:service_id>', methods=['GET'])
def tradeflow_select_return_detail(company_id, request_id, service_id):
    """View details of a service to select as return"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    incoming_request = TradeRequest.query.get_or_404(request_id)
    service = Service.query.get_or_404(service_id)

    if incoming_request.requested_service.company_id != company_id or service.company_id != incoming_request.requesting_company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))

    return render_template(
        'tradeflow_select_return_detail.html',
        company=company,
        incoming_request=incoming_request,
        service=service,
        request_id=request_id,
    )


@main.route('/tradeflow/<uuid:company_id>/decline-request/<uuid:request_id>', methods=['POST'])
def tradeflow_decline_request(company_id, request_id):
    """Decline an incoming trade request"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    trade_request = TradeRequest.query.get_or_404(request_id)

    if (resp := _ensure_request_for_company(trade_request, company_id)):
        return resp

    trade_request.status = 'archived'
    db.session.commit()

    flash('Request declined', 'info')
    return redirect(url_for('main.tradeflow_incoming_requests', company_id=company_id))


@main.route('/tradeflow/<uuid:company_id>/create-match', methods=['POST'])
def tradeflow_create_match(company_id):
    """Create a match when returning company selects a service"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    request_id = request.form.get('request_id')
    service_id = request.form.get('service_id')

    trade_request = TradeRequest.query.get_or_404(request_id)
    Service.query.get_or_404(service_id)

    proposal = DealProposal(
        proposal_id=uuid.uuid4(),
        from_company_id=trade_request.requesting_company_id,
        to_company_id=company_id,
        from_service_id=trade_request.requested_service_id,
        to_service_id=service_id,
        status='pending',
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    db.session.add(proposal)
    trade_request.status = 'archived'
    db.session.commit()

    flash('Match created! You can now create an offer.', 'success')
    return redirect(url_for('main.tradeflow_match_made', company_id=company_id))


@main.route('/tradeflow/<uuid:company_id>/you-requested', methods=['GET'])
def tradeflow_you_requested(company_id):
    """View trade requests sent by this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    your_requests = TradeRequest.query.filter_by(
        requesting_company_id=company_id,
        status='active'
    ).all()

    return render_template('tradeflow_you_requested.html', company=company, your_requests=your_requests)


@main.route('/tradeflow/<uuid:company_id>/you-requested/<uuid:request_id>', methods=['GET'])
def tradeflow_you_requested_detail(company_id, request_id):
    """View detail of one trade request sent by this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    trade_request = TradeRequest.query.get_or_404(request_id)

    if trade_request.requesting_company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))

    return render_template(
        'tradeflow_you_requested_detail.html',
        company=company,
        trade_request=trade_request,
        service=trade_request.requested_service,
    )


@main.route('/tradeflow/<uuid:company_id>/archived-requests', methods=['GET'])
def tradeflow_archived_requests(company_id):
    """View archived trade requests"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    archived_requests = TradeRequest.query.filter_by(
        requesting_company_id=company_id,
        status='archived'
    ).all()

    return render_template('tradeflow_archived_requests.html', company=company, archived_requests=archived_requests)


@main.route('/tradeflow/<uuid:company_id>/archived-requests/<uuid:request_id>', methods=['GET'])
def tradeflow_archived_request_detail(company_id, request_id):
    """View detail of an archived trade request"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    trade_request = TradeRequest.query.get_or_404(request_id)

    if trade_request.requesting_company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))

    return render_template(
        'tradeflow_archived_request_detail.html',
        company=company,
        trade_request=trade_request,
        service=trade_request.requested_service,
    )


@main.route('/tradeflow/<uuid:company_id>/match-made', methods=['GET'])
def tradeflow_match_made(company_id):
    """View all matches (where trade request was sent AND return service was selected)"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    expired = DealProposal.query.filter(
        DealProposal.status == 'matched',
        DealProposal.created_at < cutoff_date
    ).all()
    for proposal in expired:
        db.session.delete(proposal)
    db.session.commit()

    matches = DealProposal.query.filter(
        ((DealProposal.from_company_id == company_id) | (DealProposal.to_company_id == company_id)),
        DealProposal.status.in_(['matched', 'pending'])
    ).all()

    return render_template('tradeflow_match_made.html', company=company, matches=matches)


@main.route('/tradeflow/<uuid:company_id>/match/<uuid:proposal_id>', methods=['GET', 'POST'])
def tradeflow_match_detail(company_id, proposal_id):
    """View detail of one match or create offer"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    proposal = DealProposal.query.get_or_404(proposal_id)
    if (resp := _ensure_proposal_involves_company(proposal, company_id)):
        return resp

    if request.method == 'POST':
        barter_coins = _parse_int(request.form.get('barter_coins'), 0)
        message = request.form.get('message', '')

        # Normalize orientation so the company sending the offer becomes from_company.
        # This makes filters work: "Awaiting Them" shows proposals where current company is sender.
        if proposal.to_company_id == company_id:
            proposal.from_company_id, proposal.to_company_id = proposal.to_company_id, proposal.from_company_id
            proposal.from_service_id, proposal.to_service_id = proposal.to_service_id, proposal.from_service_id

        proposal.barter_coins_offered = barter_coins
        proposal.message = message if message.strip() else None
        proposal.status = 'pending'

        db.session.commit()

        flash('Offer sent! Waiting for the other party to respond.', 'success')
        return redirect(url_for('main.tradeflow_awaiting_other_party', company_id=company_id))

    return render_template('tradeflow_match_detail.html', company=company, proposal=proposal)


@main.route('/tradeflow/<uuid:company_id>/match/<uuid:proposal_id>/create-offer', methods=['GET', 'POST'])
def tradeflow_create_offer(company_id, proposal_id):
    """Create an offer/signature for a matched proposal"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    proposal = DealProposal.query.get_or_404(proposal_id)
    if (resp := _ensure_proposal_involves_company(proposal, company_id)):
        return resp

    if request.method == 'POST':
        barter_coins = _parse_int(request.form.get('barter_coins'), 0)
        message = request.form.get('message', '')

        proposal.barter_coins_offered = barter_coins
        proposal.message = message if message.strip() else None
        proposal.status = 'accepted'

        db.session.add(_create_active_deal_from_proposal(proposal_id))
        db.session.commit()

        flash('Offer accepted! Deal is now active.', 'success')
        return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

    return render_template('tradeflow_create_offer.html', company=company, proposal=proposal)


@main.route('/tradeflow/<uuid:company_id>/awaiting-signature', methods=['GET', 'POST'])
def tradeflow_awaiting_signature(company_id):
    """View offers from other parties awaiting this company's signature"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    if request.method == 'POST':
        proposal_id = request.form.get('proposal_id')
        action = request.form.get('action')

        proposal = DealProposal.query.get_or_404(proposal_id)

        if proposal.to_company_id != company_id:
            flash('Access denied', 'error')
            return redirect(url_for('main.my_companies'))

        if action == 'accept':
            proposal.status = 'accepted'
            db.session.add(_create_active_deal_from_proposal(proposal_id))
            db.session.commit()

            flash('Deal accepted! Now active.', 'success')
            return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

        elif action == 'decline':
            proposal.status = 'rejected'
            db.session.commit()

            flash('Offer declined.', 'info')
            return redirect(url_for('main.tradeflow_awaiting_signature', company_id=company_id))

    awaiting_signature = DealProposal.query.filter_by(
        to_company_id=company_id,
        status='pending'
    ).all()

    return render_template('tradeflow_awaiting_signature.html', company=company, awaiting_signature=awaiting_signature)


@main.route('/tradeflow/<uuid:company_id>/awaiting-signature/<uuid:proposal_id>', methods=['GET', 'POST'])
def tradeflow_awaiting_signature_detail(company_id, proposal_id):
    """View detail of offer awaiting signature with accept/decline options"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    proposal = DealProposal.query.get_or_404(proposal_id)

    if proposal.to_company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'accept':
            proposal.status = 'accepted'
            db.session.add(_create_active_deal_from_proposal(proposal_id))
            db.session.commit()

            flash('Deal accepted! Now active.', 'success')
            return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

        elif action == 'decline':
            proposal.status = 'rejected'
            db.session.commit()

            flash('Offer declined.', 'info')
            return redirect(url_for('main.tradeflow_awaiting_signature', company_id=company_id))

    return render_template('tradeflow_awaiting_signature_detail.html', company=company, proposal=proposal)


@main.route('/tradeflow/<uuid:company_id>/awaiting-other-party', methods=['GET'])
def tradeflow_awaiting_other_party(company_id):
    """View offers sent by this company awaiting other party's response"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    awaiting_other_party = DealProposal.query.filter_by(
        from_company_id=company_id,
        status='pending'
    ).all()

    return render_template('tradeflow_awaiting_other_party.html', company=company, awaiting_other_party=awaiting_other_party)


@main.route('/tradeflow/<uuid:company_id>/ongoing-deals', methods=['GET'])
def tradeflow_ongoing_deals(company_id):
    """View ongoing deals for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    ongoing_deals = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_id) | (DealProposal.to_company_id == company_id)),
        ActiveDeal.status == 'in_progress'
    ).all()

    return render_template('tradeflow_ongoing_deals.html', company=company, ongoing_deals=ongoing_deals)


@main.route('/tradeflow/<uuid:company_id>/ongoing-deals/<uuid:deal_id>', methods=['GET', 'POST'])
def tradeflow_ongoing_deal_detail(company_id, deal_id):
    """View and manage an ongoing deal"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    active_deal = ActiveDeal.query.get_or_404(deal_id)
    proposal = active_deal.proposal

    if (resp := _ensure_proposal_involves_company(proposal, company_id)):
        return resp

    if request.method == 'POST':
        if proposal.from_company_id == company_id:
            active_deal.to_company_completed = True
        else:
            active_deal.from_company_completed = True

        if active_deal.from_company_completed and active_deal.to_company_completed:
            active_deal.status = 'completed'
            active_deal.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
            flash('Deal completed! Both parties have confirmed delivery.', 'success')
            return redirect(url_for('main.tradeflow_completed_deals', company_id=company_id))
        else:
            db.session.commit()
            flash('Confirmed! Waiting for the other party to confirm delivery.', 'success')
            return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

    return render_template(
        'tradeflow_ongoing_deal_detail.html',
        company=company,
        active_deal=active_deal,
        proposal=proposal,
    )


@main.route('/tradeflow/<uuid:company_id>/completed-deals', methods=['GET'])
def tradeflow_completed_deals(company_id):
    """View completed deals for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    completed_deals = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_id) | (DealProposal.to_company_id == company_id)),
        ActiveDeal.status == 'completed'
    ).all()

    return render_template('tradeflow_completed_deals.html', company=company, completed_deals=completed_deals)


@main.route('/tradeflow/<uuid:company_id>/completed-deals/<uuid:deal_id>', methods=['GET'])
def tradeflow_completed_deal_detail(company_id, deal_id):
    """View detail of a completed deal with reviews"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    active_deal = ActiveDeal.query.get_or_404(deal_id)
    proposal = active_deal.proposal

    if (resp := _ensure_proposal_involves_company(proposal, company_id)):
        return resp

    reviews = active_deal.reviews.all()

    return render_template(
        'tradeflow_completed_deal_detail.html',
        company=company,
        active_deal=active_deal,
        proposal=proposal,
        reviews=reviews,
    )


@main.route('/tradeflow/<uuid:company_id>/completed-deals/<uuid:deal_id>/write-review', methods=['GET', 'POST'])
def tradeflow_write_review(company_id, deal_id):
    """Write a review for a completed deal"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    active_deal = ActiveDeal.query.get_or_404(deal_id)
    proposal = active_deal.proposal

    if (resp := _ensure_proposal_involves_company(proposal, company_id)):
        return resp

    if proposal.from_company_id == company_id:
        reviewed_company_id = proposal.to_company_id
        reviewed_service_id = proposal.to_service_id
    else:
        reviewed_company_id = proposal.from_company_id
        reviewed_service_id = proposal.from_service_id

    existing_review = Review.query.filter_by(
        deal_id=deal_id,
        reviewer_id=session['user_id'],
        reviewed_service_id=reviewed_service_id
    ).first()

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '')

        review = Review(
            review_id=uuid.uuid4(),
            deal_id=deal_id,
            reviewer_id=session['user_id'],
            rating=rating,
            comment=comment,
            reviewed_company_id=reviewed_company_id,
            reviewed_service_id=reviewed_service_id,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )

        db.session.add(review)
        db.session.commit()

        flash('Review submitted!', 'success')
        return redirect(url_for('main.tradeflow_completed_deal_detail', company_id=company_id, deal_id=deal_id))

    reviewed_service = Service.query.get(reviewed_service_id)

    return render_template(
        'tradeflow_write_review.html',
        company=company,
        active_deal=active_deal,
        proposal=proposal,
        reviewed_service=reviewed_service,
        existing_review=existing_review,
    )
