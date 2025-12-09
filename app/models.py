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
    # Barter coins for the company (virtual currency for balancing trades)
    barter_coins = db.Column(db.Integer, nullable=False, default=0)

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
# SERVICE CATEGORY (Association table for many-to-many)
# ==========================
service_categories = db.Table(
    'service_categories',
    db.Column('service_id', UUID(as_uuid=True), db.ForeignKey('service.service_id'), primary_key=True),
    db.Column('category_name', db.Text, primary_key=True)
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
    
    # Barter coins cost for this service
    barter_coins_cost = db.Column(db.Integer, nullable=False, default=0)
    
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

    # Relationships
    requesting_company = db.relationship("Company", foreign_keys=[requesting_company_id], backref="trade_requests_sent")
    requested_service = db.relationship("Service", backref="trade_requests")

    def __repr__(self) -> str:
        return f"<TradeRequest {self.request_id} ({self.status})>"


# ==========================
# SERVICE INTEREST (DEPRECATED - KEPT FOR BACKWARDS COMPATIBILITY)
# ==========================
class ServiceInterest(db.Model):
    """
    Tracks when a company expresses interest in another company's service.
    company_id: The company showing interest
    service_id: The service they're interested in
    offering_service_id: The service they're offering in exchange
    """
    __tablename__ = "service_interest"

    interest_id = db.Column(UUID(as_uuid=True), primary_key=True)
    service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False
    )
    company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    offering_service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False
    )
    created_at = db.Column(DateTime(timezone=True), nullable=False)

    # Relationships
    service = db.relationship("Service", foreign_keys=[service_id], backref="interests")
    company = db.relationship("Company", backref="service_interests")
    offering_service = db.relationship("Service", foreign_keys=[offering_service_id])

    def __repr__(self) -> str:
        return f"<ServiceInterest {self.interest_id}>"


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
    barter_coins_offered = db.Column(db.Integer, nullable=False, default=0)
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
# BARTER DEAL
# ==========================
class BarterDeal(db.Model):
    """
    Een deal tussen twee services (service A en service B).
    """
    __tablename__ = "barterdeal"

    deal_id = db.Column(UUID(as_uuid=True), primary_key=True)

    service_a_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False,
    )
    service_b_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("service.service_id"),
        nullable=False,
    )

    # ENUM 'deal_status' in Supabase → Text in ORM
    status = db.Column(db.Text, nullable=False)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    ratio_a_to_b = db.Column(db.Numeric)  # bv. 1.0 = 1:1, 2.0 = 2:1

    created_at = db.Column(DateTime(timezone=True))
    updated_at = db.Column(DateTime(timezone=True))

    service_a = db.relationship(
        "Service",
        foreign_keys=[service_a_id],
        backref=db.backref("as_service_a_deals", lazy="dynamic"),
    )
    service_b = db.relationship(
        "Service",
        foreign_keys=[service_b_id],
        backref=db.backref("as_service_b_deals", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return f"<BarterDeal {self.deal_id}>"


# ==========================
# CONTRACT
# ==========================
class Contract(db.Model):
    """
    Contract dat hoort bij één BarterDeal.
    """
    __tablename__ = "contract"

    contract_id = db.Column(UUID(as_uuid=True), primary_key=True)
    deal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("barterdeal.deal_id"),
        nullable=False,
    )

    signed_by_initiator = db.Column(db.Boolean)
    signed_by_counterparty = db.Column(db.Boolean)
    signed_at_initiator = db.Column(DateTime(timezone=True))
    signed_at_counterparty = db.Column(DateTime(timezone=True))

    # ENUM 'contract_status' in Supabase
    status = db.Column(db.Text, nullable=False)

    created_at = db.Column(DateTime(timezone=True))

    deal = db.relationship(
        "BarterDeal",
        backref=db.backref("contract", uselist=False),
    )

    def __repr__(self) -> str:
        return f"<Contract {self.contract_id}>"


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

    def __repr__(self) -> str:
        return f"<Review {self.review_id} rating={self.rating}>"


# ==========================
# MESSAGE
# ==========================
class Message(db.Model):
    """
    Negotiation messages between companies on a specific proposal.
    Allows companies to communicate during the proposal phase.
    """
    __tablename__ = "message"

    message_id = db.Column(UUID(as_uuid=True), primary_key=True)
    proposal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("deal_proposal.proposal_id"),
        nullable=False
    )
    from_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(DateTime(timezone=True), nullable=False)

    # Relationships
    proposal = db.relationship("DealProposal", backref=db.backref("messages", lazy="dynamic"))
    from_company = db.relationship("Company", backref=db.backref("sent_messages", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Message {self.message_id} on proposal {self.proposal_id}>"


# ==========================
# DELIVERABLE
# ==========================
class Deliverable(db.Model):
    """
    Files/deliverables uploaded by companies to fulfill their service obligations.
    Associated with an active deal.
    """
    __tablename__ = "deliverable"

    deliverable_id = db.Column(UUID(as_uuid=True), primary_key=True)
    active_deal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("active_deal.active_deal_id"),
        nullable=False
    )
    from_company_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("company.company_id"),
        nullable=False
    )
    file_path = db.Column(db.Text, nullable=False)  # Path to uploaded file
    description = db.Column(db.Text)  # Optional description of the deliverable
    uploaded_at = db.Column(DateTime(timezone=True), nullable=False)

    # Relationships
    active_deal = db.relationship("ActiveDeal", backref=db.backref("deliverables", lazy="dynamic"))
    from_company = db.relationship("Company", backref=db.backref("deliverables", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Deliverable {self.deliverable_id} for deal {self.active_deal_id}>"



