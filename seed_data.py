#!/usr/bin/env python
"""
Seed script to populate the database with example data.
Run with: python seed_data.py

================================================================================
EXAMPLE LOGIN CREDENTIALS
================================================================================

All accounts use the same password: testgebruiker

ADMIN ACCOUNTS (Company Founders):
  1. alice_johnson / testgebruiker → Admin of: Tech Solutions Inc
  2. bob_smith / testgebruiker → Admin of: Green Energy Co
  3. charlie_brown / testgebruiker → Admin of: Digital Marketing Pro
  4. diana_prince / testgebruiker → Admin of: Finance Hub
  5. edward_norton / testgebruiker → Admin of: Creative Studios
  6. fiona_apple / testgebruiker → Admin of: Legal Associates
  7. george_lucas / testgebruiker → Admin of: HR Consulting
  8. hannah_montana / testgebruiker → Admin of: Design Factory
  9. isaac_newton / testgebruiker → Admin of: Development Labs
 10. julia_roberts / testgebruiker → Admin of: Business Strategy

MEMBER ACCOUNTS (Company Employees):
  1. kevin_hart / testgebruiker → Member of: Tech Solutions Inc
  2. laura_palmer / testgebruiker → Member of: Green Energy Co
  3. mark_twain / testgebruiker → Member of: Digital Marketing Pro
  4. nina_simone / testgebruiker → Member of: Finance Hub
  5. oscar_wilde / testgebruiker → Member of: Creative Studios
  6. patricia_hill / testgebruiker → Member of: Legal Associates
  7. quincy_jones / testgebruiker → Member of: HR Consulting
  8. rachel_green / testgebruiker → Member of: Design Factory
  9. samuel_jackson / testgebruiker → Member of: Development Labs
 10. tina_turner / testgebruiker → Member of: Business Strategy

COMPANIES & SERVICES:
  - Each company has 5 services with realistic titles, descriptions, and categories
  - Service durations range from 15 to 160 hours
  - Categories include: Finance, IT, Marketing, Design, Development, Legal, HR, etc.

================================================================================
"""

import uuid
import datetime
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, user, Company, CompanyMember, CompanyJoinRequest, Service, DealProposal, ActiveDeal, BarterDeal, Contract, Review, ServiceInterest

def seed_database():
    """Populate database with example data"""
    app = create_app()
    
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        # Delete in reverse order of foreign key dependencies
        db.session.query(Review).delete()
        db.session.query(Contract).delete()
        db.session.query(ActiveDeal).delete()
        db.session.query(BarterDeal).delete()
        db.session.query(DealProposal).delete()
        db.session.query(ServiceInterest).delete()
        db.session.query(Service).delete()
        db.session.query(CompanyJoinRequest).delete()
        db.session.query(CompanyMember).delete()
        db.session.query(Company).delete()
        db.session.query(user).delete()
        db.session.commit()
        
        # Create 20 users
        print("Creating 20 users...")
        users = []
        user_names = [
            'Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Edward Norton',
            'Fiona Apple', 'George Lucas', 'Hannah Montana', 'Isaac Newton', 'Julia Roberts',
            'Kevin Hart', 'Laura Palmer', 'Mark Twain', 'Nina Simone', 'Oscar Wilde',
            'Patricia Hill', 'Quincy Jones', 'Rachel Green', 'Samuel Jackson', 'Tina Turner'
        ]
        
        for i, name in enumerate(user_names):
            username = name.lower().replace(' ', '_')
            new_user = user(
                user_id=uuid.uuid4(),
                username=username,
                email=f"{username}@example.com",
                password_hash=generate_password_hash('testgebruiker'),
                location=f"City {i % 5 + 1}",
                job_description=f"Professional in field {i % 3 + 1}",
                created_at=datetime.datetime.now(datetime.timezone.utc),
                updated_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.session.add(new_user)
            users.append(new_user)
        
        db.session.commit()
        print(f"✓ Created {len(users)} users")
        
        # Create 10 companies (for the 10 admins)
        print("Creating 10 companies with admins...")
        companies = []
        company_names = [
            'Tech Solutions Inc', 'Green Energy Co', 'Digital Marketing Pro', 'Finance Hub',
            'Creative Studios', 'Legal Associates', 'HR Consulting', 'Design Factory',
            'Development Labs', 'Business Strategy'
        ]
        
        company_descriptions = [
            'Providing cutting-edge technology solutions',
            'Renewable energy consulting and implementation',
            'Digital marketing and social media strategies',
            'Financial planning and investment advice',
            'Creative design and branding services',
            'Legal consultation and contract review',
            'Human resources and talent management',
            'Graphic and UX/UI design services',
            'Software development and web applications',
            'Business strategy and organizational development'
        ]
        
        for i in range(10):
            company = Company(
                company_id=uuid.uuid4(),
                name=company_names[i],
                description=company_descriptions[i],
                join_code=f"JOIN{i+1:03d}",
                barter_coins=1000,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.session.add(company)
            companies.append(company)
        
        db.session.commit()
        print(f"✓ Created {len(companies)} companies")
        
        # Assign first 10 users as admins of the 10 companies
        print("Assigning admins to companies...")
        for i in range(10):
            member = CompanyMember(
                member_id=uuid.uuid4(),
                company_id=companies[i].company_id,
                user_id=users[i].user_id,
                member_role='founder',
                is_admin=True,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.session.add(member)
        
        db.session.commit()
        print("✓ Assigned 10 users as admins")
        
        # Assign remaining 10 users (11-20) as members of companies
        print("Assigning members to companies...")
        for i in range(10, 20):
            company = companies[i % 10]  # Distribute among 10 companies
            member = CompanyMember(
                member_id=uuid.uuid4(),
                company_id=company.company_id,
                user_id=users[i].user_id,
                member_role='employee',
                is_admin=False,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.session.add(member)
        
        db.session.commit()
        print("✓ Assigned 10 users as members")
        
        # Create 5 services for each company
        print("Creating services for each company...")
        
        service_templates = [
            # Tech Solutions Inc
            [
                {'title': 'Web Development', 'description': 'Full-stack web application development using modern frameworks', 'duration': 40, 'categories': 'Development,IT,Consulting'},
                {'title': 'Cloud Architecture', 'description': 'Design and implement scalable cloud infrastructure', 'duration': 30, 'categories': 'IT,Development,Consulting'},
                {'title': 'Database Optimization', 'description': 'Performance tuning and optimization of database systems', 'duration': 20, 'categories': 'IT,Development'},
                {'title': 'System Integration', 'description': 'Integration of legacy systems with modern applications', 'duration': 50, 'categories': 'IT,Development,Consulting'},
                {'title': 'Technical Support', 'description': '24/7 technical support and maintenance services', 'duration': 160, 'categories': 'IT,Customer Support'},
            ],
            # Green Energy Co
            [
                {'title': 'Solar Installation', 'description': 'Professional solar panel installation and setup', 'duration': 80, 'categories': 'Operations,Consulting'},
                {'title': 'Energy Audit', 'description': 'Comprehensive energy consumption analysis', 'duration': 25, 'categories': 'Consulting,Operations'},
                {'title': 'Renewable Transition', 'description': 'Help transition to renewable energy sources', 'duration': 60, 'categories': 'Consulting,Operations'},
                {'title': 'Maintenance Services', 'description': 'Regular maintenance of renewable systems', 'duration': 120, 'categories': 'Operations,Customer Support'},
                {'title': 'Training', 'description': 'Staff training on renewable energy systems', 'duration': 15, 'categories': 'HR,Consulting'},
            ],
            # Digital Marketing Pro
            [
                {'title': 'Social Media Strategy', 'description': 'Develop comprehensive social media campaigns', 'duration': 35, 'categories': 'Marketing,Consulting'},
                {'title': 'SEO Optimization', 'description': 'Search engine optimization and online visibility', 'duration': 45, 'categories': 'Marketing,IT'},
                {'title': 'Content Creation', 'description': 'Professional content writing and design', 'duration': 50, 'categories': 'Marketing,Design'},
                {'title': 'Analytics Review', 'description': 'In-depth analytics and performance reporting', 'duration': 18, 'categories': 'Marketing,Consulting'},
                {'title': 'Brand Development', 'description': 'Brand identity and positioning strategy', 'duration': 70, 'categories': 'Marketing,Design,Consulting'},
            ],
            # Finance Hub
            [
                {'title': 'Financial Planning', 'description': 'Comprehensive financial planning and strategy', 'duration': 55, 'categories': 'Finance,Consulting'},
                {'title': 'Tax Consultation', 'description': 'Tax optimization and compliance advice', 'duration': 40, 'categories': 'Finance,Legal'},
                {'title': 'Accounting Services', 'description': 'Bookkeeping and financial statement preparation', 'duration': 150, 'categories': 'Accounting,Finance'},
                {'title': 'Investment Advisory', 'description': 'Investment portfolio analysis and recommendations', 'duration': 35, 'categories': 'Finance,Consulting'},
                {'title': 'Audit Support', 'description': 'Audit preparation and financial review', 'duration': 85, 'categories': 'Accounting,Finance,Legal'},
            ],
            # Creative Studios
            [
                {'title': 'Logo Design', 'description': 'Custom logo design and branding', 'duration': 25, 'categories': 'Design,Marketing'},
                {'title': 'Graphic Design', 'description': 'Professional graphic design services', 'duration': 35, 'categories': 'Design'},
                {'title': 'UX/UI Design', 'description': 'User experience and interface design', 'duration': 60, 'categories': 'Design,Development'},
                {'title': 'Brand Identity', 'description': 'Complete brand identity system creation', 'duration': 90, 'categories': 'Design,Marketing,Consulting'},
                {'title': 'Print Design', 'description': 'Brochures, flyers, and print materials', 'duration': 20, 'categories': 'Design'},
            ],
            # Legal Associates
            [
                {'title': 'Contract Review', 'description': 'Thorough contract analysis and negotiation', 'duration': 45, 'categories': 'Legal,Consulting'},
                {'title': 'Compliance Audit', 'description': 'Regulatory compliance assessment', 'duration': 50, 'categories': 'Legal,Consulting'},
                {'title': 'Legal Consultation', 'description': 'General legal advice and guidance', 'duration': 30, 'categories': 'Legal,Consulting'},
                {'title': 'Document Preparation', 'description': 'Preparation of legal documents', 'duration': 35, 'categories': 'Legal'},
                {'title': 'Dispute Resolution', 'description': 'Mediation and conflict resolution services', 'duration': 120, 'categories': 'Legal,Consulting'},
            ],
            # HR Consulting
            [
                {'title': 'Recruitment Services', 'description': 'Full recruitment and hiring process support', 'duration': 100, 'categories': 'HR,Consulting'},
                {'title': 'HR Strategy', 'description': 'Human resources strategy development', 'duration': 40, 'categories': 'HR,Consulting'},
                {'title': 'Training Programs', 'description': 'Employee training and development programs', 'duration': 80, 'categories': 'HR'},
                {'title': 'Compliance Support', 'description': 'HR compliance and employment law guidance', 'duration': 35, 'categories': 'HR,Legal,Consulting'},
                {'title': 'Performance Management', 'description': 'Performance review systems and coaching', 'duration': 60, 'categories': 'HR,Consulting'},
            ],
            # Design Factory
            [
                {'title': 'Web Design', 'description': 'Modern, responsive website design', 'duration': 75, 'categories': 'Design,Development'},
                {'title': 'UI Component Library', 'description': 'Creation of reusable UI components', 'duration': 55, 'categories': 'Design,Development'},
                {'title': 'Wireframing', 'description': 'Website and app wireframe design', 'duration': 20, 'categories': 'Design'},
                {'title': 'Prototyping', 'description': 'Interactive prototype development', 'duration': 40, 'categories': 'Design,Development'},
                {'title': 'Design System', 'description': 'Comprehensive design system creation', 'duration': 100, 'categories': 'Design,Development,Consulting'},
            ],
            # Development Labs
            [
                {'title': 'Mobile App Development', 'description': 'iOS and Android app development', 'duration': 120, 'categories': 'Development,IT'},
                {'title': 'API Development', 'description': 'REST and GraphQL API development', 'duration': 50, 'categories': 'Development,IT'},
                {'title': 'Backend Development', 'description': 'Server-side application development', 'duration': 90, 'categories': 'Development,IT'},
                {'title': 'DevOps Setup', 'description': 'Continuous integration and deployment setup', 'duration': 40, 'categories': 'Development,IT,Operations'},
                {'title': 'Code Review', 'description': 'Expert code review and optimization', 'duration': 25, 'categories': 'Development,IT'},
            ],
            # Business Strategy
            [
                {'title': 'Strategic Planning', 'description': 'Business strategy and planning sessions', 'duration': 60, 'categories': 'Consulting'},
                {'title': 'Market Analysis', 'description': 'Market research and competitive analysis', 'duration': 45, 'categories': 'Consulting,Marketing'},
                {'title': 'Business Transformation', 'description': 'Organizational transformation and change management', 'duration': 150, 'categories': 'Consulting,Operations'},
                {'title': 'Process Improvement', 'description': 'Business process optimization', 'duration': 70, 'categories': 'Consulting,Operations'},
                {'title': 'Leadership Coaching', 'description': 'Executive coaching and development', 'duration': 50, 'categories': 'Consulting,HR'},
            ],
        ]
        
        total_services = 0
        for i, company in enumerate(companies):
            services_for_company = service_templates[i]
            for service_info in services_for_company:
                service = Service(
                    service_id=uuid.uuid4(),
                    company_id=company.company_id,
                    title=service_info['title'],
                    description=service_info['description'],
                    duration_hours=service_info['duration'],
                    barter_coins_cost=0,
                    categories=service_info['categories'],
                    is_offered=True,
                    is_active=True,
                    status='active',
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    updated_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.session.add(service)
                total_services += 1
        
        db.session.commit()
        print(f"✓ Created {total_services} services (5 per company)")
        
        print("\n" + "="*50)
        print("✓ Database seeding completed successfully!")
        print("="*50)
        print("\nTest Accounts:")
        print("=" * 50)
        for i in range(10):
            print(f"Admin {i+1}: {user_names[i].lower().replace(' ', '_')} / testgebruiker")
            print(f"  → Admin of: {company_names[i]}")
        print("\nMember Accounts:")
        print("=" * 50)
        for i in range(10, 20):
            company_idx = i % 10
            print(f"Member: {user_names[i].lower().replace(' ', '_')} / testgebruiker")
            print(f"  → Member of: {company_names[company_idx]}")

if __name__ == '__main__':
    seed_database()
