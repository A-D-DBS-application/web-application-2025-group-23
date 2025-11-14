from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class user(db.Model):
    __tablename__ = 'user'  # expliciete naam
    user_id = db.Column(db.String(36), primary_key=True)  # uuid opgeslagen als string (36 tekens)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(50))
    location = db.Column(db.String(120))
    job_description = db.Column(db.String(120))
    company_name = db.Column(db.String(120))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<user {self.username}>'
