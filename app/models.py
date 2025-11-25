#Belangrijk, skip deze uitleg pls ff niet: 
# Migration zorgt ervoor dat als je de database wil aanpassen, dit via hier in models.py kan in plaats van in supabase
# Dit is handiger want anders kunnen er verschillen zijn tussen de code en supabase en dan runt hij niet en blabla.
# Na elke wijziging in dit bestand (models.py) (EERST SAVEN), voer je volgende commando's uit in terminal (zorg dat je in de venv zit):
#   source .venv/bin/activate
#   # gebruik de venv python ("python") — vermijd twijfel met system python3
#   python -m flask --app run db migrate -m "{wat je deed} - {je naam}"
#   python -m flask --app run db upgrade
#
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
class user(db.Model):
    """
    Profielgegevens van een gebruiker.
    Komt overeen met de 'user' tabel in Supabase.
    """
    __tablename__ = "user"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text)

    # Korte beschrijving/omschrijving van iemands job / functie
    job_description = db.Column(db.Text)

    location = db.Column(db.Text)

    verified = db.Column(db.Boolean)         # mag NULL zijn in Supabase

    created_at = db.Column(DateTime(timezone=True))
    updated_at = db.Column(DateTime(timezone=True))

    role = db.Column(db.Text)                

    def __repr__(self) -> str:
        return f"<user {self.username}>"


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
    user = db.relationship("user", backref=db.backref("join_requests", lazy="dynamic"))

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
        "user",
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
    Komt overeen met de 'service' tabel (uuid, jsonb, enum, ...).
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
    category = db.Column(db.Text, nullable=False)

    is_offered = db.Column(db.Boolean, nullable=False)  # True = aanbod, False = vraag

    estimated_time_min = db.Column(db.Integer)          # int4, mag NULL
    value_estimate = db.Column(db.Numeric)              # numeric, mag NULL
    availability = db.Column(JSONB)                     # jsonb, bv. {"mon": ["evening"]}

    # In Supabase: ENUM 'service_status' → hier gewoon Text,
    # DB zelf bewaakt toegelaten waarden.
    status = db.Column(db.Text, nullable=False)

    created_at = db.Column(DateTime(timezone=True))
    updated_at = db.Column(DateTime(timezone=True))

    company = db.relationship("Company", back_populates="services")

    def __repr__(self) -> str:
        return f"<Service {self.title} ({self.service_id})>"


# ==========================
# BARTERDEAL
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
    """
    __tablename__ = "review"

    review_id = db.Column(UUID(as_uuid=True), primary_key=True)

    deal_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("barterdeal.deal_id"),
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

    deal = db.relationship(
        "BarterDeal",
        backref=db.backref("reviews", lazy="dynamic"),
    )
    reviewer = db.relationship(
        "user",
        backref=db.backref("given_reviews", lazy="dynamic"),
    )
    reviewed_company = db.relationship(
        "Company",
        backref=db.backref("reviews", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.review_id} rating={self.rating}>"
