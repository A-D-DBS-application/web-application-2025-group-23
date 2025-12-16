import datetime
import uuid

from flask import request, redirect, url_for, render_template, session, flash

from ..fairness import compute_fairness
from ..models import db, Service, TradeRequest, DealProposal, ActiveDeal, Review
from .core import main
from .helpers import (
    _create_active_deal_from_proposal,
    _ensure_proposal_involves_company,
    _ensure_request_for_company,
    _parse_int,
    _require_company_member,
    _require_login,
    mark_tradeflow_section_viewed,
    get_tradeflow_unread_counts,
    _sidebar_companies,
)


@main.route('/tradeflow/<uuid:company_id>/incoming-requests', methods=['GET'])
def tradeflow_incoming_requests(company_id):
    """View incoming trade requests for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    # Mark section as viewed
    mark_tradeflow_section_viewed(company_id, 'incoming')
    
    # Get unread counts for sidebar
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    incoming_requests = TradeRequest.query.join(Service).filter(
        Service.company_id == company_id,
        TradeRequest.status == 'active'
    ).all()

    return render_template('tradeflow_incoming_requests.html', company=company, incoming_requests=incoming_requests, unread_counts=unread_counts, user_companies=user_companies)


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
        incoming_request.archived_at = datetime.datetime.now(datetime.timezone.utc)
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
    trade_request.archived_at = datetime.datetime.now(datetime.timezone.utc)
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
        status='matched',
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    db.session.add(proposal)
    trade_request.status = 'archived'
    trade_request.archived_at = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()

    flash('Match created! You can now create an offer.', 'success')
    return redirect(url_for('main.tradeflow_match_made', company_id=company_id))


@main.route('/tradeflow/<uuid:company_id>/you-requested', methods=['GET'])
def tradeflow_you_requested(company_id):
    """View trade requests that this company has sent"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    mark_tradeflow_section_viewed(company_id, 'you_requested')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    your_requests = TradeRequest.query.filter_by(
        requesting_company_id=company_id,
        status='active'
    ).all()

    return render_template('tradeflow_you_requested.html', company=company, your_requests=your_requests, unread_counts=unread_counts, user_companies=user_companies)


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

    mark_tradeflow_section_viewed(company_id, 'archived')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    # Get archived requests both sent by and received by this company
    archived_requests = TradeRequest.query.filter(
        ((TradeRequest.requesting_company_id == company_id) | 
         (TradeRequest.requested_service.has(company_id=company_id))),
        TradeRequest.status == 'archived'
    ).order_by(TradeRequest.archived_at.desc().nullsfirst()).all()

    return render_template('tradeflow_archived_requests.html', company=company, archived_requests=archived_requests, unread_counts=unread_counts, user_companies=user_companies)


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

    # Mark section as viewed
    mark_tradeflow_section_viewed(company_id, 'matches')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    expired = DealProposal.query.filter(
        DealProposal.status == 'matched',
        DealProposal.created_at < cutoff_date
    ).all()
    for proposal in expired:
        db.session.delete(proposal)
    db.session.commit()

    matched_proposals = DealProposal.query.filter(
        DealProposal.status == 'matched',
        (
            (DealProposal.from_company_id == company_id) |
            (DealProposal.to_company_id == company_id)
        )
    ).all()

    # For each match, check if there's a pending proposal
    matches_with_status = []
    for match in matched_proposals:
        # Check if there's a pending proposal for this service pair (not rejected)
        pending_proposal = DealProposal.query.filter(
            DealProposal.status == 'pending',
            (
                (
                    (DealProposal.from_company_id == match.from_company_id) &
                    (DealProposal.to_company_id == match.to_company_id) &
                    (DealProposal.from_service_id == match.from_service_id) &
                    (DealProposal.to_service_id == match.to_service_id)
                ) |
                (
                    (DealProposal.from_company_id == match.to_company_id) &
                    (DealProposal.to_company_id == match.from_company_id) &
                    (DealProposal.from_service_id == match.to_service_id) &
                    (DealProposal.to_service_id == match.from_service_id)
                )
            )
        ).first()
        
        match_info = {
            'proposal': match,
            'has_pending': pending_proposal is not None,
            'pending_sent_by_you': False
        }
        
        if pending_proposal:
            # Determine if the current company sent the pending proposal
            match_info['pending_sent_by_you'] = (pending_proposal.from_company_id == company_id)
        
        matches_with_status.append(match_info)

    return render_template(
        'tradeflow_match_made.html',
        company=company,
        matches=matches_with_status,
        unread_counts=unread_counts,
        user_companies=user_companies
    )


@main.route('/tradeflow/<uuid:company_id>/match/<uuid:proposal_id>', methods=['GET', 'POST'])
def tradeflow_match_detail(company_id, proposal_id):
    """Detail page for a match, to send an offer"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    proposal = DealProposal.query.get_or_404(proposal_id)
    if proposal.from_company_id != company_id and proposal.to_company_id != company_id:
        flash('Not authorized to view this proposal.', 'danger')
        return redirect(url_for('main.tradeflow_match_made', company_id=company_id))

    fairness_data = compute_fairness(proposal.from_service, proposal.to_service)

    fairness_data = compute_fairness(proposal.from_service, proposal.to_service)

    if request.method == 'POST':
        message = request.form.get('message', '')
        money_amount = _parse_int(request.form.get('money_amount'), 0)
        money_type = request.form.get('money_type') if request.form.get('money_type') in ('receive', 'give') else None

        # Compute orientation for the NEW proposal based on current company sending
        if proposal.from_company_id == company_id:
            new_from_company_id = proposal.from_company_id
            new_to_company_id = proposal.to_company_id
            new_from_service_id = proposal.from_service_id
            new_to_service_id = proposal.to_service_id
        else:
            new_from_company_id = proposal.to_company_id
            new_to_company_id = proposal.from_company_id
            new_from_service_id = proposal.to_service_id
            new_to_service_id = proposal.from_service_id

        # Persist money info inside message (no DB fields). Prefix with a simple tag.
        money_prefix = ''
        if money_type and money_amount and money_amount > 0:
            money_prefix = f"[MONEY:{money_type}:{money_amount}] "

        full_message = (money_prefix + message).strip()

        # Create a new DealProposal so both sides' offers remain visible
        new_proposal = DealProposal(
            proposal_id=uuid.uuid4(),
            from_company_id=new_from_company_id,
            to_company_id=new_to_company_id,
            from_service_id=new_from_service_id,
            to_service_id=new_to_service_id,
            status='pending',
            message=full_message if full_message else None,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(new_proposal)
        db.session.commit()

        flash('Offer sent! Waiting for the other party to respond.', 'success')
        return redirect(url_for('main.tradeflow_awaiting_other_party', company_id=company_id))

    return render_template('tradeflow_match_detail.html', company=company, proposal=proposal, fairness_data=fairness_data)


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
        message = request.form.get('message', '')

        proposal.message = message if message.strip() else None
        proposal.status = 'accepted'

        db.session.add(_create_active_deal_from_proposal(proposal_id))
        # Remove related pending/matched proposals for the same pair (both directions)
        related = DealProposal.query.filter(
            DealProposal.proposal_id != proposal_id,
            DealProposal.status.in_(['matched', 'pending']),
            (
                (
                    (DealProposal.from_company_id == proposal.from_company_id) &
                    (DealProposal.to_company_id == proposal.to_company_id) &
                    (DealProposal.from_service_id == proposal.from_service_id) &
                    (DealProposal.to_service_id == proposal.to_service_id)
                ) |
                (
                    (DealProposal.from_company_id == proposal.to_company_id) &
                    (DealProposal.to_company_id == proposal.from_company_id) &
                    (DealProposal.from_service_id == proposal.to_service_id) &
                    (DealProposal.to_service_id == proposal.from_service_id)
                )
            )
        ).all()
        for p in related:
            db.session.delete(p)
        db.session.commit()

        flash('Offer accepted! Deal is now active.', 'success')
        return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

    return render_template('tradeflow_create_offer.html', company=company, proposal=proposal, fairness_data=fairness_data)


@main.route('/tradeflow/<uuid:company_id>/awaiting-signature', methods=['GET', 'POST'])
def tradeflow_awaiting_signature(company_id):
    """View offers from other parties awaiting this company's signature"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    mark_tradeflow_section_viewed(company_id, 'awaiting_signature')
    unread_counts = get_tradeflow_unread_counts(company_id)

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
            
            # First remove proposals for the exact same service pair (both orientations)
            related = DealProposal.query.filter(
                DealProposal.proposal_id != proposal_id,
                DealProposal.status.in_(['matched', 'pending']),
                (
                    (
                        (DealProposal.from_company_id == proposal.from_company_id) &
                        (DealProposal.to_company_id == proposal.to_company_id) &
                        (DealProposal.from_service_id == proposal.from_service_id) &
                        (DealProposal.to_service_id == proposal.to_service_id)
                    ) |
                    (
                        (DealProposal.from_company_id == proposal.to_company_id) &
                        (DealProposal.to_company_id == proposal.from_company_id) &
                        (DealProposal.from_service_id == proposal.to_service_id) &
                        (DealProposal.to_service_id == proposal.from_service_id)
                    )
                )
            ).all()
            for p in related:
                db.session.delete(p)
            
            # Additionally remove any other matched/pending proposals between the same companies (any services)
            related_company = DealProposal.query.filter(
                DealProposal.status.in_(['matched', 'pending']),
                DealProposal.proposal_id != proposal_id,
                (
                    (
                        (DealProposal.from_company_id == proposal.from_company_id) &
                        (DealProposal.to_company_id == proposal.to_company_id)
                    ) |
                    (
                        (DealProposal.from_company_id == proposal.to_company_id) &
                        (DealProposal.to_company_id == proposal.from_company_id)
                    )
                )
            ).all()
            for p in related_company:
                db.session.delete(p)
            
            db.session.commit()

            flash('Deal accepted! Now active.', 'success')
            return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

        elif action == 'decline':
            proposal.status = 'rejected'
            db.session.commit()

            flash('Offer declined.', 'info')
            return redirect(url_for('main.tradeflow_awaiting_signature', company_id=company_id))

    mark_tradeflow_section_viewed(company_id, 'awaiting_signature')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    awaiting_signature = DealProposal.query.filter_by(
        to_company_id=company_id,
        status='pending'
    ).all()

    # Parse money tags for overview cards
    for offer in awaiting_signature:
        offer.money_type = None
        offer.money_amount = None
        try:
            if offer.message and offer.message.startswith('[MONEY:'):
                end_idx = offer.message.find(']')
                if end_idx != -1:
                    tag = offer.message[7:end_idx]
                    parts = tag.split(':')
                    if len(parts) == 2 and parts[0] in ('receive', 'give'):
                        offer.money_type = parts[0]
                        offer.money_amount = _parse_int(parts[1], 0)
        except Exception:
            pass

    return render_template('tradeflow_awaiting_signature.html', company=company, awaiting_signature=awaiting_signature, unread_counts=unread_counts, user_companies=user_companies)


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
            
            # First remove proposals for the exact same service pair (both orientations)
            related = DealProposal.query.filter(
                DealProposal.proposal_id != proposal_id,
                DealProposal.status.in_(['matched', 'pending']),
                (
                    (
                        (DealProposal.from_company_id == proposal.from_company_id) &
                        (DealProposal.to_company_id == proposal.to_company_id) &
                        (DealProposal.from_service_id == proposal.from_service_id) &
                        (DealProposal.to_service_id == proposal.to_service_id)
                    ) |
                    (
                        (DealProposal.from_company_id == proposal.to_company_id) &
                        (DealProposal.to_company_id == proposal.from_company_id) &
                        (DealProposal.from_service_id == proposal.to_service_id) &
                        (DealProposal.to_service_id == proposal.from_service_id)
                    )
                )
            ).all()
            for p in related:
                db.session.delete(p)
            
            # Additionally remove any other matched/pending proposals between the same companies (any services)
            related_company = DealProposal.query.filter(
                DealProposal.status.in_(['matched', 'pending']),
                DealProposal.proposal_id != proposal_id,
                (
                    (
                        (DealProposal.from_company_id == proposal.from_company_id) &
                        (DealProposal.to_company_id == proposal.to_company_id)
                    ) |
                    (
                        (DealProposal.from_company_id == proposal.to_company_id) &
                        (DealProposal.to_company_id == proposal.from_company_id)
                    )
                )
            ).all()
            for p in related_company:
                db.session.delete(p)
            
            db.session.commit()

            flash('Deal accepted! Now active.', 'success')
            return redirect(url_for('main.tradeflow_ongoing_deals', company_id=company_id))

        elif action == 'decline':
            proposal.status = 'rejected'
            db.session.commit()

            flash('Offer declined.', 'info')
            return redirect(url_for('main.tradeflow_awaiting_signature', company_id=company_id))

    # Parse optional money info from message prefix like [MONEY:receive:100]
    proposal.money_type = None
    proposal.money_amount = None
    try:
        if proposal.message and proposal.message.startswith('[MONEY:'):
            end_idx = proposal.message.find(']')
            if end_idx != -1:
                tag = proposal.message[7:end_idx]  # inside MONEY:
                parts = tag.split(':')
                if len(parts) == 2 and parts[0] in ('receive', 'give'):
                    proposal.money_type = parts[0]
                    proposal.money_amount = _parse_int(parts[1], 0)
                    # Strip the tag from the visible message
                    proposal.message = proposal.message[end_idx+1:].strip()
    except Exception:
        pass

    fairness_data = compute_fairness(proposal.from_service, proposal.to_service)

    return render_template('tradeflow_awaiting_signature_detail.html', company=company, proposal=proposal, fairness_data=fairness_data)


@main.route('/tradeflow/<uuid:company_id>/awaiting-other-party', methods=['GET'])
def tradeflow_awaiting_other_party(company_id):
    """View offers sent by this company awaiting other party's response"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    mark_tradeflow_section_viewed(company_id, 'awaiting_other_party')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    awaiting_other_party = DealProposal.query.filter_by(
        from_company_id=company_id,
        status='pending'
    ).all()

    # Parse money tags for overview cards
    for offer in awaiting_other_party:
        offer.money_type = None
        offer.money_amount = None
        try:
            if offer.message and offer.message.startswith('[MONEY:'):
                end_idx = offer.message.find(']')
                if end_idx != -1:
                    tag = offer.message[7:end_idx]
                    parts = tag.split(':')
                    if len(parts) == 2 and parts[0] in ('receive', 'give'):
                        offer.money_type = parts[0]
                        offer.money_amount = _parse_int(parts[1], 0)
        except Exception:
            pass

    return render_template('tradeflow_awaiting_other_party.html', company=company, awaiting_other_party=awaiting_other_party, unread_counts=unread_counts, user_companies=user_companies)


@main.route('/tradeflow/<uuid:company_id>/awaiting-other-party/<uuid:proposal_id>', methods=['GET'])
def tradeflow_awaiting_other_party_detail(company_id, proposal_id):
    """Read-only detail view for offers you sent, awaiting other party"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp
    proposal = DealProposal.query.get_or_404(proposal_id)

    # Only allow viewing if this company sent the offer
    if proposal.from_company_id != company_id:
        flash('Access denied', 'error')
        return redirect(url_for('main.my_companies'))

    # Parse optional money info from message prefix like [MONEY:receive:100]
    proposal.money_type = None
    proposal.money_amount = None
    try:
        if proposal.message and proposal.message.startswith('[MONEY:'):
            end_idx = proposal.message.find(']')
            if end_idx != -1:
                tag = proposal.message[7:end_idx]
                parts = tag.split(':')
                if len(parts) == 2 and parts[0] in ('receive', 'give'):
                    proposal.money_type = parts[0]
                    proposal.money_amount = _parse_int(parts[1], 0)
                    proposal.message = proposal.message[end_idx+1:].strip()
    except Exception:
        pass

    # Swap services for FROM company perspective: you offer from_service and want to_service
    fairness_data = compute_fairness(proposal.to_service, proposal.from_service)

    return render_template('tradeflow_awaiting_other_party_detail.html', company=company, proposal=proposal, fairness_data=fairness_data)


@main.route('/tradeflow/<uuid:company_id>/ongoing-deals', methods=['GET'])
def tradeflow_ongoing_deals(company_id):
    """View ongoing deals for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    mark_tradeflow_section_viewed(company_id, 'ongoing')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    ongoing_deals = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_id) | (DealProposal.to_company_id == company_id)),
        ActiveDeal.status == 'in_progress'
    ).all()

    return render_template('tradeflow_ongoing_deals.html', company=company, ongoing_deals=ongoing_deals, unread_counts=unread_counts, user_companies=user_companies)


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


@main.route('/tradeflow/switch-company/<uuid:new_company_id>', methods=['GET'])
def tradeflow_switch_company(new_company_id):
    """Switch to a different company in tradeflow - redirects to same page type with new company"""
    if (resp := _require_login()):
        return resp
    
    # Verify user is member of new company
    company, resp = _require_company_member(new_company_id)
    if resp:
        return resp
    
    # Get referer to determine which page to redirect to
    referer = request.referrer or ''
    
    # Try to extract the current route pattern from referer
    # Default to incoming requests if we can't determine
    if '/incoming-requests' in referer:
        return redirect(url_for('main.tradeflow_incoming_requests', company_id=new_company_id))
    elif '/you-requested' in referer:
        return redirect(url_for('main.tradeflow_you_requested', company_id=new_company_id))
    elif '/archived-requests' in referer:
        return redirect(url_for('main.tradeflow_archived_requests', company_id=new_company_id))
    elif '/match-made' in referer or '/trade-matches' in referer:
        return redirect(url_for('main.tradeflow_match_made', company_id=new_company_id))
    elif '/awaiting-signature' in referer:
        return redirect(url_for('main.tradeflow_awaiting_signature', company_id=new_company_id))
    elif '/awaiting-other-party' in referer:
        return redirect(url_for('main.tradeflow_awaiting_other_party', company_id=new_company_id))
    elif '/ongoing-deals' in referer:
        return redirect(url_for('main.tradeflow_ongoing_deals', company_id=new_company_id))
    elif '/completed-deals' in referer:
        return redirect(url_for('main.tradeflow_completed_deals', company_id=new_company_id))
    else:
        # Default to incoming requests
        return redirect(url_for('main.tradeflow_incoming_requests', company_id=new_company_id))


@main.route('/tradeflow/<uuid:company_id>/completed-deals', methods=['GET'])
def tradeflow_completed_deals(company_id):
    """View completed deals for this company"""
    if (resp := _require_login()):
        return resp
    company, resp = _require_company_member(company_id)
    if resp:
        return resp

    mark_tradeflow_section_viewed(company_id, 'completed')
    unread_counts = get_tradeflow_unread_counts(company_id)
    
    # Get user companies for sidebar dropdown
    user_id = uuid.UUID(session['user_id'])
    user_companies = _sidebar_companies(user_id, company_id)

    completed_deals = ActiveDeal.query.join(DealProposal).filter(
        ((DealProposal.from_company_id == company_id) | (DealProposal.to_company_id == company_id)),
        ActiveDeal.status == 'completed'
    ).all()

    return render_template('tradeflow_completed_deals.html', company=company, completed_deals=completed_deals, unread_counts=unread_counts, user_companies=user_companies)


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

    # Review should target the service received from the counterparty
    if proposal.from_company_id == company_id:
        reviewed_company_id = proposal.to_company_id
        reviewed_service_id = proposal.from_service_id
    else:
        reviewed_company_id = proposal.from_company_id
        reviewed_service_id = proposal.to_service_id

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
