"""
Script to add join codes to existing companies that don't have one.
Run this once to update all existing companies.
"""
import random
import string
from app import create_app
from app.models import db, Company

def generate_join_code():
    """Generate a unique 8-character join code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Company.query.filter_by(join_code=code).first():
            return code

def add_join_codes():
    """Add join codes to all companies that don't have one."""
    app = create_app()
    with app.app_context():
        companies_without_code = Company.query.filter(
            (Company.join_code == None) | (Company.join_code == '')
        ).all()
        
        if not companies_without_code:
            print("All companies already have join codes!")
            return
        
        print(f"Found {len(companies_without_code)} companies without join codes")
        
        for company in companies_without_code:
            join_code = generate_join_code()
            company.join_code = join_code
            print(f"  - {company.name}: {join_code}")
        
        db.session.commit()
        print(f"\n✓ Successfully added join codes to {len(companies_without_code)} companies")

if __name__ == '__main__':
    add_join_codes()
