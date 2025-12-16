import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import func

from .models import (
    ActiveDeal,
    DealProposal,
    Review,
    Service,
    ServiceViewEvent,
    TradeRequest,
    db,
)


def _min_max_norm(value: float, min_val: Optional[float], max_val: Optional[float], default: float = 0.0) -> float:
    if min_val is None or max_val is None or max_val == min_val:
        return float(default)
    return float((value - min_val) / (max_val - min_val))


def _review_component(service_reviews: Dict[UUID, Dict[str, float]], service_id: UUID, smoothing_k: int) -> float:
    stats = service_reviews.get(service_id)
    if not stats:
        # No reviews → neutral after normalization
        return 0.5

    avg_rating = stats.get("avg_rating", 0) or 0
    review_count = stats.get("count", 0) or 0

    # Map 1-5 stars to [-1, 1]
    mapped_avg = (float(avg_rating) - 3.0) / 2.0
    smoothed = (review_count * mapped_avg) / (review_count + smoothing_k) if (review_count + smoothing_k) > 0 else mapped_avg
    return (smoothed + 1) / 2


def _trust_component(
    company_id: UUID,
    company_completed: Dict[UUID, int],
    company_avg_review_mapped: Dict[UUID, float],
    completed_min: Optional[int],
    completed_max: Optional[int],
) -> float:
    completed_norm = _min_max_norm(company_completed.get(company_id, 0), completed_min, completed_max, 0.0)
    avg_mapped = company_avg_review_mapped.get(company_id)
    avg_review_norm = (avg_mapped + 1) / 2 if avg_mapped is not None else 0.5
    return 0.5 * completed_norm + 0.3 * avg_review_norm


def compute_fairness(requested_service: Service, return_service: Service, smoothing_k: int = 3) -> Optional[Dict[str, object]]:
    """Compute Service Value Index for two services and return the fairness ratio."""
    if not requested_service or not return_service:
        return None

    # Base service data (duration + company)
    service_rows = db.session.query(Service.service_id, Service.duration_hours, Service.company_id).all()
    service_meta = {row.service_id: {"duration": float(row.duration_hours or 0), "company_id": row.company_id} for row in service_rows}

    if not service_rows:
        return None

    # Interaction counts
    view_counts = {
        row.service_id: row.count
        for row in db.session.query(ServiceViewEvent.service_id, func.count(ServiceViewEvent.view_id).label("count")).group_by(ServiceViewEvent.service_id).all()
    }
    request_counts = {
        row.requested_service_id: row.count
        for row in db.session.query(TradeRequest.requested_service_id, func.count(TradeRequest.request_id).label("count")).group_by(TradeRequest.requested_service_id).all()
    }
    chosen_return_counts = {
        row.to_service_id: row.count
        for row in db.session.query(DealProposal.to_service_id, func.count(DealProposal.proposal_id).label("count"))
        .filter(DealProposal.status == "matched")
        .group_by(DealProposal.to_service_id)
        .all()
    }

    # Demand raw per service + min/max
    demand_raw: Dict[UUID, float] = {}
    demand_min: Optional[float] = None
    demand_max: Optional[float] = None

    effort_min: Optional[float] = None
    effort_max: Optional[float] = None

    for row in service_rows:
        duration = float(row.duration_hours or 0)
        effort_min = duration if effort_min is None else min(effort_min, duration)
        effort_max = duration if effort_max is None else max(effort_max, duration)

        views = view_counts.get(row.service_id, 0)
        requests = request_counts.get(row.service_id, 0)
        chosen_return = chosen_return_counts.get(row.service_id, 0)
        raw_value = views + (3 * requests) + (2 * chosen_return)
        demand_raw[row.service_id] = raw_value
        demand_min = raw_value if demand_min is None else min(demand_min, raw_value)
        demand_max = raw_value if demand_max is None else max(demand_max, raw_value)

    # Service review stats
    service_reviews = {
        row.reviewed_service_id: {"avg_rating": float(row.avg_rating), "count": row.count_rating}
        for row in db.session.query(
            Review.reviewed_service_id,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.review_id).label("count_rating"),
        )
        .group_by(Review.reviewed_service_id)
        .all()
    }

    # Company-level trust inputs
    company_completed: Dict[UUID, int] = {}
    completed_rows = (
        db.session.query(DealProposal.from_company_id.label("company_id"), func.count(ActiveDeal.active_deal_id).label("count"))
        .join(ActiveDeal, ActiveDeal.proposal_id == DealProposal.proposal_id)
        .filter(ActiveDeal.status == "completed")
        .group_by(DealProposal.from_company_id)
        .all()
    )
    for row in completed_rows:
        company_completed[row.company_id] = company_completed.get(row.company_id, 0) + row.count

    completed_rows_to = (
        db.session.query(DealProposal.to_company_id.label("company_id"), func.count(ActiveDeal.active_deal_id).label("count"))
        .join(ActiveDeal, ActiveDeal.proposal_id == DealProposal.proposal_id)
        .filter(ActiveDeal.status == "completed")
        .group_by(DealProposal.to_company_id)
        .all()
    )
    for row in completed_rows_to:
        company_completed[row.company_id] = company_completed.get(row.company_id, 0) + row.count

    completed_min = min(company_completed.values()) if company_completed else 0
    completed_max = max(company_completed.values()) if company_completed else 0

    company_avg_review_mapped: Dict[UUID, float] = {}
    company_review_rows = (
        db.session.query(Service.company_id, func.avg(Review.rating).label("avg_rating"))
        .join(Review, Review.reviewed_service_id == Service.service_id)
        .group_by(Service.company_id)
        .all()
    )
    for row in company_review_rows:
        mapped = (float(row.avg_rating) - 3.0) / 2.0
        company_avg_review_mapped[row.company_id] = mapped

    def _service_svi(service_obj: Service) -> Dict[str, float]:
        meta = service_meta.get(service_obj.service_id, {"duration": 0.0, "company_id": service_obj.company_id})
        effort_norm = _min_max_norm(meta["duration"], effort_min, effort_max, 0.0)
        demand_norm = _min_max_norm(demand_raw.get(service_obj.service_id, 0.0), demand_min, demand_max, 0.0)
        review_norm = _review_component(service_reviews, service_obj.service_id, smoothing_k)
        trust = _trust_component(
            meta["company_id"],
            company_completed,
            company_avg_review_mapped,
            completed_min,
            completed_max,
        )

        svi = (0.45 * effort_norm) + (0.30 * demand_norm) + (0.15 * review_norm) + (0.10 * trust)
        return {
            "svi": svi,
            "components": {
                "effort": effort_norm,
                "demand": demand_norm,
                "review": review_norm,
                "trust": trust,
            },
            "raw": {
                "duration_hours": meta["duration"],
                "demand_raw": demand_raw.get(service_obj.service_id, 0.0),
            },
        }

    requested_metrics = _service_svi(requested_service)
    return_metrics = _service_svi(return_service)

    requested_svi = requested_metrics["svi"]
    return_svi = return_metrics["svi"]
    fairness_ratio = None
    if requested_svi:
        fairness_ratio = return_svi / requested_svi

    label = "balanced"
    if fairness_ratio is not None:
        if fairness_ratio < 0.9:
            label = "return lower"
        elif fairness_ratio > 1.1:
            label = "return higher"

    return {
        "requested": requested_metrics,
        "return": return_metrics,
        "fairness_ratio": fairness_ratio,
        "label": label,
    }


def record_service_view(service_id: UUID) -> None:
    """Store a view event for a service detail page."""
    try:
        event = ServiceViewEvent(
            view_id=uuid4(),
            service_id=service_id,
            viewed_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        db.session.rollback()
