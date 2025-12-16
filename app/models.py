#Belangrijk, skip deze uitleg pls ff niet: 
# Migration zorgt ervoor dat als je de database wil aanpassen, dit via hier in models.py kan in plaats van in supabase
# Dit is handiger want anders kunnen er verschillen zijn tussen de code en supabase en dan runt hij niet en blabla.
# Na elke wijziging in dit bestand (models.py) (EERST SAVEN), voer je volgende commando's uit in terminal (zorg dat je in de venv zit):
#   source .venv/bin/activate
#   # gebruik de venv python ("python") — vermijd twijfel met system python3
#   python -m flask --app run db migrate -m "{wat je deed} - {je naam}"
#   python -m flask --app run db upgrade
#   
#   voor mac:
#   python3 -m flask --app run db migrate -m "{wat je deed} - {je naam}"
#   python3 -m flask --app run db upgrade

# Gebruik expliciet de venv python of activeer de venv; vermijd system python3 verwarring
# Voorbeeld:
#   source .venv/bin/activate
#   python -m flask --app run db migrate -m "{wat je deed} - {je naam}"
#   python -m flask --app run db upgrade
# Alleen uitvoeren bij echte DB-wijzigingen (nieuwe kolom, tabel, typewijziging).
# Doe GEEN aanpassingen in Supabase zelf vanaf nu, dit gebeurt automatisch via de migrations nadat je die 2 commando's hebt uitgevoerd.
# Migrations zijn zoals Git voor de database → altijd in volgorde houden.

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime

db = SQLAlchemy()


# ==========================
# USER
# ==========================
class User(db.Model):
    """
    Profielgegevens van een gebruiker.
    Komt overeen met de 'user' tabel in Supabase.
    """
    __tablename__ = "user"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text)
    password_hash = db.Column(db.Text, nullable=False)

    # Korte beschrijving/omschrijving van iemands job / functie
    job_description = db.Column(db.Text)

    location = db.Column(db.Text)

    verified = db.Column(db.Boolean)         # mag NULL zijn in Supabase

    created_at = db.Column(DateTime(timezone=True))
    updated_at = db.Column(DateTime(timezone=True))

    role = db.Column(db.Text)                

    def __repr__(self) -> str:
        return f"<User {self.username}>"


# ==========================
# COMPANY
# ==========================
class Company(db.Model):
    """
    Een bedrijf/organisatie waar services aan gekoppeld zijn.
    """
    __tablename__ = "company"

    company_id = db.Column(UUID(as_uuid=True), primary_key=True)
    name = db.Column(db.Text)  # in Supabase nullable = allowed
    description = db.Column(db.Text, nullable=True)  # Company description
    created_at = db.Column(DateTime(timezone=True))
    # Code users can submit to request joining the company
    join_code = db.Column(db.Text, nullable=True, unique=True)

    # Relaties:
    # - members: lijst van CompanyMember records
    # - services: lijst van Service records
    members = db.relationship(
        "CompanyMember",
        back_populates="company",
        lazy="dynamic",
    )
    services = db.relationship(
        "Service",
        back_populates="company",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


class CompanyJoinRequest(db.Model):
    """
    Represents a user's request to join a company. Admins can accept or reject.
    """
    __tablename__ = "company_join_request"

    request_id = db.Column(UUID(as_uuid=True), primary_key=True)
    company_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("company.company_id"), nullable=False
    )
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"), nullable=False)
    created_at = db.Column(DateTime(timezone=True))

    company = db.relationship("Company", backref=db.backref("join_requests", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("join_requests", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<CompanyJoinRequest {self.request_id} company={self.company_id} user={self.user_id}>"


# ==========================
# COMPANY_MEMBER
# ==========================
class CompanyMember(db.Model):
    """
    Koppelt users aan companies met een rol (bv. 'founder').
    """
    __tablename__ = "company_member"

    member_id = db.Column(UUID(as_uuid=True), primary_key=True)
    company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False,
    )
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id"),
        nullable=False,
    )
    member_role = db.Column(db.Text)  # bv. 'founder', 'employee'
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # <-- voeg deze toe
    created_at = db.Column(DateTime(timezone=True))

    # Relaties
    company = db.relationship("Company", back_populates="members")
    user_obj = db.relationship(
        "User",
        backref=db.backref("company_memberships", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyMember user_id={self.user_id} company_id={self.company_id} is_admin={self.is_admin}>"
        )


# ==========================
# SERVICE
# ==========================
class Service(db.Model):
    """
    Een service die door een company aangeboden of gevraagd wordt.
    Updated to support duration, multiple categories, and active status.
    """
    __tablename__ = "service"

    service_id = db.Column(UUID(as_uuid=True), primary_key=True)
    company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False,
    )

    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    # Duration in hours (can be decimal, e.g. 1.5 hours)
    duration_hours = db.Column(db.Numeric, nullable=False)
    
    # Many-to-many relationship with categories (stored as text tags)
    # Categories: Finance, Accounting, IT, Marketing, Legal, Design, HR, Consulting, etc.
    categories = db.Column(db.Text)  # Comma-separated for simplicity, e.g. "Finance,Accounting"

    is_offered = db.Column(db.Boolean, nullable=False, default=True)  # True = offering service
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Can be deactivated

    value_estimate = db.Column(db.Numeric)              # numeric, mag NULL
    availability = db.Column(JSONB)                     # jsonb, bv. {"mon": ["evening"]}

    # In Supabase: ENUM 'service_status' → hier gewoon Text
    status = db.Column(db.Text, nullable=False, default='active')

    created_at = db.Column(DateTime(timezone=True))
    updated_at = db.Column(DateTime(timezone=True))

    company = db.relationship("Company", back_populates="services")

    def __repr__(self) -> str:
        return f"<Service {self.title} ({self.service_id})>"


# ==========================
# SERVICE VIEW EVENT
# ==========================
class ServiceViewEvent(db.Model):
    """
    Track each time a service detail page is opened on the marketplace (public or logged-in).
    """
    __tablename__ = "service_view_event"

    view_id = db.Column(UUID(as_uuid=True), primary_key=True)
    service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False,
    )
    viewed_at = db.Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<ServiceViewEvent service={self.service_id} at={self.viewed_at}>"


# ==========================
# TRADE REQUEST
# ==========================
class TradeRequest(db.Model):
    """
    A trade request sent by one company expressing interest in another company's service.
    Includes validity in days (7/14/30/60/90).
    Status: active (sent but no match yet), archived (expired or declined).
    """
    __tablename__ = "trade_request"

    request_id = db.Column(UUID(as_uuid=True), primary_key=True)
    requesting_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    requested_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False
    )
    validity_days = db.Column(db.Integer, nullable=False, default=14)  # 7, 14, 30, 60, 90
    status = db.Column(db.Text, nullable=False, default='active')  # active, archived (expired/no match)
    created_at = db.Column(DateTime(timezone=True), nullable=False)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    archived_at = db.Column(DateTime(timezone=True), nullable=True)  # When the request was archived

    # Relationships
    requesting_company = db.relationship("Company", foreign_keys=[requesting_company_id], backref="trade_requests_sent")
    requested_service = db.relationship("Service", backref="trade_requests")

    def __repr__(self) -> str:
        return f"<TradeRequest {self.request_id} ({self.status})>"


# ==========================
# DEAL PROPOSAL
# ==========================
class DealProposal(db.Model):
    """
    A proposal sent from one company admin to another to trade services.
    Can include barter coins to balance value differences.
    """
    __tablename__ = "deal_proposal"

    proposal_id = db.Column(UUID(as_uuid=True), primary_key=True)
    from_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    to_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    from_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False
    )
    to_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False
    )
    message = db.Column(db.Text)  # Optional message from proposer
    status = db.Column(db.Text, nullable=False, default='pending')  # pending, accepted, rejected
    created_at = db.Column(DateTime(timezone=True), nullable=False)

    # Relationships
    from_company = db.relationship("Company", foreign_keys=[from_company_id], backref="sent_proposals")
    to_company = db.relationship("Company", foreign_keys=[to_company_id], backref="received_proposals")
    from_service = db.relationship("Service", foreign_keys=[from_service_id])
    to_service = db.relationship("Service", foreign_keys=[to_service_id])

    def __repr__(self) -> str:
        return f"<DealProposal {self.proposal_id} ({self.status})>"


# ==========================
# ACTIVE DEAL
# ==========================
class ActiveDeal(db.Model):
    """
    Tracks ongoing deals after proposal acceptance.
    Both companies must mark as complete before reviews can be submitted.
    """
    __tablename__ = "active_deal"

    active_deal_id = db.Column(UUID(as_uuid=True), primary_key=True)
    proposal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("deal_proposal.proposal_id"),
        nullable=False
    )
    from_company_completed = db.Column(db.Boolean, nullable=False, default=False)
    to_company_completed = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.Text, nullable=False, default='in_progress')  # in_progress, completed
    created_at = db.Column(DateTime(timezone=True), nullable=False)
    completed_at = db.Column(DateTime(timezone=True))

    # Relationships
    proposal = db.relationship("DealProposal", backref="active_deal")

    def __repr__(self) -> str:
        return f"<ActiveDeal {self.active_deal_id} ({self.status})>"





# ==========================
# REVIEW
# ==========================
class Review(db.Model):
    """
    Review die een user schrijft over een company na een deal.
    Now references active_deal instead of barterdeal.
    """
    __tablename__ = "review"

    review_id = db.Column(UUID(as_uuid=True), primary_key=True)

    # Changed to reference active_deal instead of barterdeal
    deal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("active_deal.active_deal_id"),
        nullable=False,
    )
    reviewer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id"),
        nullable=False,
    )

    rating = db.Column(db.SmallInteger, nullable=False)  # int2
    comment = db.Column(db.Text)

    created_at = db.Column(DateTime(timezone=True))

    reviewed_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
    )
    reviewed_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
    )

    active_deal = db.relationship(
        "ActiveDeal",
        backref=db.backref("reviews", lazy="dynamic"),
    )
    reviewer = db.relationship(
        "User",
        backref=db.backref("given_reviews", lazy="dynamic"),
    )
    reviewed_company = db.relationship(
        "Company",
        backref=db.backref("reviews", lazy="dynamic"),
    )
    reviewed_service = db.relationship(
        "Service",
        backref=db.backref("reviews", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.review_id} rating={self.rating}>"


# ==========================
# TRADEFLOW VIEW TRACKING
# ==========================
class TradeflowView(db.Model):
    """
    Tracks when a user last viewed each tradeflow section for notification badges.
    """
    __tablename__ = "tradeflow_view"

    view_id = db.Column(UUID(as_uuid=True), primary_key=True)
    company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id"),
        nullable=False
    )
    section = db.Column(db.Text, nullable=False)  # 'incoming', 'you_requested', 'archived', 'matches', 'awaiting_signature', 'awaiting_other_party', 'ongoing', 'completed'
    last_viewed_at = db.Column(DateTime(timezone=True), nullable=False)

    # Relationships
    company = db.relationship("Company", backref=db.backref("tradeflow_views", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("tradeflow_views", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<TradeflowView {self.section} for company {self.company_id} by user {self.user_id}>"




