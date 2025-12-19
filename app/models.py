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
from sqlalchemy import DateTime, CheckConstraint, Index, text
from sqlalchemy.sql import func
from enum import Enum

db = SQLAlchemy()


# ==========================
# STATUS ENUMS
# ==========================
class TradeRequestStatus(Enum):
    """Status values for trade requests."""
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    
    @classmethod
    def choices(cls) -> list[str]:
        return [c.value for c in cls]


class DealProposalStatus(Enum):
    """Status values for deal proposals."""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    
    @classmethod
    def choices(cls) -> list[str]:
        return [c.value for c in cls]


class ActiveDealStatus(Enum):
    """Status values for active deals."""
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    
    @classmethod
    def choices(cls) -> list[str]:
        return [c.value for c in cls]


class ValidityDays(Enum):
    """Valid options for trade request validity period."""
    WEEK = 7
    TWO_WEEKS = 14
    MONTH = 30
    TWO_MONTHS = 60
    THREE_MONTHS = 90
    
    @classmethod
    def choices(cls) -> list[int]:
        return [c.value for c in cls]


# ==========================
# SERVICE CATEGORIES (Enum)
# ==========================
class ServiceCategory(Enum):
    """
    Predefined categories for services.
    Using Enum ensures consistency and prevents typos.
    
    Usage:
        - In templates: ServiceCategory.choices() returns list of display names
        - In code: ServiceCategory.FINANCE.value returns 'Finance'
        - Validation: ServiceCategory.is_valid('Finance') returns True
    """
    FINANCE = 'Finance'
    ACCOUNTING = 'Accounting'
    IT = 'IT'
    MARKETING = 'Marketing'
    LEGAL = 'Legal'
    DESIGN = 'Design'
    DEVELOPMENT = 'Development'
    CONSULTING = 'Consulting'
    SALES = 'Sales'
    HR = 'HR'
    OPERATIONS = 'Operations'
    CUSTOMER_SUPPORT = 'Customer Support'
    
    @classmethod
    def choices(cls) -> list[str]:
        """Return all category values as a list (for template dropdowns)."""
        return [c.value for c in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a string is a valid category."""
        return value in cls.choices()
    
    @classmethod
    def get_valid_categories(cls, categories: list[str]) -> list[str]:
        """Filter a list to only include valid categories + custom ones."""
        # Allow custom categories (those not in enum) to pass through
        return categories


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
    email = db.Column(db.Text, nullable=False, unique=True)  # Email is now required and unique
    password_hash = db.Column(db.Text, nullable=False)
    
    # Optional profile fields
    location = db.Column(db.Text, nullable=True)
    job_description = db.Column(db.Text, nullable=True)

    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_user_email', 'email'),
        Index('ix_user_username', 'username'),
    )

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
    name = db.Column(db.Text, nullable=False)  # Company name is now required
    description = db.Column(db.Text, nullable=True)  # Company description
    category = db.Column(db.Text, nullable=True)  # Company category/industry
    website = db.Column(db.Text, nullable=True)  # Company website URL
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    # Code users can submit to request joining the company
    join_code = db.Column(db.Text, nullable=True, unique=True)
    
    # Index for faster lookups
    __table_args__ = (
        Index('ix_company_name', 'name'),
        Index('ix_company_join_code', 'join_code'),
    )

    # Relaties:
    # - members: lijst van CompanyMember records
    # - services: lijst van Service records
    members = db.relationship(
        "CompanyMember",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan",  # Delete members when company is deleted
    )
    services = db.relationship(
        "Service",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan",  # Delete services when company is deleted
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
        UUID(as_uuid=True), db.ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes and unique constraint
    __table_args__ = (
        Index('ix_company_join_request_company', 'company_id'),
        Index('ix_company_join_request_user', 'user_id'),
        db.UniqueConstraint('company_id', 'user_id', name='uq_company_join_request_company_user'),
    )

    company = db.relationship("Company", backref=db.backref("join_requests", lazy="dynamic", cascade="all, delete-orphan"))
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
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    member_role = db.Column(db.Text)  # bv. 'founder', 'employee'
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes and unique constraint - one user per company
    __table_args__ = (
        Index('ix_company_member_company', 'company_id'),
        Index('ix_company_member_user', 'user_id'),
        db.UniqueConstraint('company_id', 'user_id', name='uq_company_member_company_user'),
    )

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
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
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

    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_service_company', 'company_id'),
        Index('ix_service_is_active', 'is_active'),
        Index('ix_service_categories', 'categories'),
        # Check constraint for positive duration
        CheckConstraint('duration_hours > 0', name='ck_service_duration_positive'),
    )

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
        db.ForeignKey("service.service_id", ondelete="CASCADE"),
        nullable=False,
    )
    viewed_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Index for analytics queries
    __table_args__ = (
        Index('ix_service_view_event_service', 'service_id'),
        Index('ix_service_view_event_viewed_at', 'viewed_at'),
    )

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
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False
    )
    requested_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id", ondelete="CASCADE"),
        nullable=False
    )
    validity_days = db.Column(db.Integer, nullable=False, default=14)  # 7, 14, 30, 60, 90
    status = db.Column(db.Text, nullable=False, default='active')  # active, archived
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    archived_at = db.Column(DateTime(timezone=True), nullable=True)

    # Indexes and constraints
    __table_args__ = (
        Index('ix_trade_request_requesting_company', 'requesting_company_id'),
        Index('ix_trade_request_requested_service', 'requested_service_id'),
        Index('ix_trade_request_status', 'status'),
        Index('ix_trade_request_expires_at', 'expires_at'),
        # Validity must be one of the allowed values
        CheckConstraint('validity_days IN (7, 14, 30, 60, 90)', name='ck_trade_request_validity_days'),
        # Status must be valid
        CheckConstraint("status IN ('active', 'archived')", name='ck_trade_request_status'),
    )

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
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False
    )
    to_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False
    )
    from_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id", ondelete="CASCADE"),
        nullable=False
    )
    to_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id", ondelete="CASCADE"),
        nullable=False
    )
    message = db.Column(db.Text)  # Optional message from proposer
    status = db.Column(db.Text, nullable=False, default='pending')  # pending, accepted, rejected
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Indexes and constraints
    __table_args__ = (
        Index('ix_deal_proposal_from_company', 'from_company_id'),
        Index('ix_deal_proposal_to_company', 'to_company_id'),
        Index('ix_deal_proposal_status', 'status'),
        # Status must be valid
        CheckConstraint("status IN ('pending', 'accepted', 'rejected')", name='ck_deal_proposal_status'),
        # Cannot propose to yourself
        CheckConstraint('from_company_id != to_company_id', name='ck_deal_proposal_different_companies'),
    )

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
        db.ForeignKey("deal_proposal.proposal_id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One active deal per proposal
    )
    from_company_completed = db.Column(db.Boolean, nullable=False, default=False)
    to_company_completed = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.Text, nullable=False, default='in_progress')  # in_progress, completed
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = db.Column(DateTime(timezone=True))

    # Indexes and constraints
    __table_args__ = (
        Index('ix_active_deal_proposal', 'proposal_id'),
        Index('ix_active_deal_status', 'status'),
        # Status must be valid
        CheckConstraint("status IN ('in_progress', 'completed')", name='ck_active_deal_status'),
    )

    # Relationships
    proposal = db.relationship("DealProposal", backref=db.backref("active_deal", uselist=False))

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
        db.ForeignKey("active_deal.active_deal_id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    rating = db.Column(db.SmallInteger, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)

    created_at = db.Column(DateTime(timezone=True), server_default=func.now())

    reviewed_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id", ondelete="SET NULL"),
    )
    reviewed_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id", ondelete="SET NULL"),
    )

    # Indexes and constraints
    __table_args__ = (
        Index('ix_review_deal', 'deal_id'),
        Index('ix_review_reviewer', 'reviewer_id'),
        Index('ix_review_reviewed_company', 'reviewed_company_id'),
        Index('ix_review_reviewed_service', 'reviewed_service_id'),
        # Rating must be 1-5
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_range'),
        # NOTE: Unique constraint (deal_id, reviewer_id) removed due to existing duplicate data
        # Enforce uniqueness in application code instead
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
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    section = db.Column(db.Text, nullable=False)  # 'incoming', 'you_requested', 'archived', 'matches', etc.
    last_viewed_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Indexes and unique constraint
    __table_args__ = (
        Index('ix_tradeflow_view_company', 'company_id'),
        Index('ix_tradeflow_view_user', 'user_id'),
        # One view record per (company, user, section) combination
        db.UniqueConstraint('company_id', 'user_id', 'section', name='uq_tradeflow_view_company_user_section'),
        # Valid sections only
        CheckConstraint(
            "section IN ('incoming', 'you_requested', 'archived', 'matches', 'awaiting_signature', 'awaiting_other_party', 'ongoing', 'completed')",
            name='ck_tradeflow_view_section'
        ),
    )

    # Relationships
    company = db.relationship("Company", backref=db.backref("tradeflow_views", lazy="dynamic", cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("tradeflow_views", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<TradeflowView {self.section} for company {self.company_id} by user {self.user_id}>"




