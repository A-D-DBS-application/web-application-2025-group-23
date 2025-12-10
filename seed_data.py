#!/usr/bin/env python
"""
Seed script to populate the database with example data.
Run with: python seed_data.py

================================================================================
EXAMPLE LOGIN CREDENTIALS
================================================================================

All accounts use the same password: testgebruiker

ADMIN ACCOUNTS (Company Founders) - 20 COMPANIES:
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
 11. kyle_reese / testgebruiker → Admin of: Data Analytics Pro
 12. lucy_liu / testgebruiker → Admin of: Content Creators Hub
 13. michael_scott / testgebruiker → Admin of: Sales Excellence
 14. natalie_portman / testgebruiker → Admin of: Event Planning Co
 15. oliver_twist / testgebruiker → Admin of: Supply Chain Solutions
 16. penny_lane / testgebruiker → Admin of: Customer Success Team
 17. quentin_blake / testgebruiker → Admin of: Video Production Studio
 18. rita_hayworth / testgebruiker → Admin of: Translation Services
 19. steve_jobs / testgebruiker → Admin of: Innovation Workshop
 20. tara_reid / testgebruiker → Admin of: Quality Assurance Experts

MEMBER ACCOUNTS (Company Employees) - 20 EMPLOYEES:
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
 11. uma_thurman / testgebruiker → Member of: Data Analytics Pro
 12. victor_hugo / testgebruiker → Member of: Content Creators Hub
 13. walter_white / testgebruiker → Member of: Sales Excellence
 14. xena_warrior / testgebruiker → Member of: Event Planning Co
 15. yasmine_bleeth / testgebruiker → Member of: Supply Chain Solutions
 16. zack_morris / testgebruiker → Member of: Customer Success Team
 17. amy_adams / testgebruiker → Member of: Video Production Studio
 18. brad_pitt / testgebruiker → Member of: Translation Services
 19. cate_blanchett / testgebruiker → Member of: Innovation Workshop
 20. denzel_washington / testgebruiker → Member of: Quality Assurance Experts

COMPANIES & SERVICES:
  - 20 companies, each with 5 services (100 total services)
  - Service durations range from 15 to 160 hours
  - Categories: Finance, Accounting, IT, Marketing, Legal, Design, Development, 
    Consulting, Sales, HR, Operations, Customer Support

TRADE FLOW STATUSES (For testing):
  📨 ONE-SIDED INTEREST (active trade requests):
     - Companies 1-4: Have sent trade requests to various services
  
  🤝 MUTUAL INTEREST (match made, awaiting offer):
     - Companies 5-8: Have mutual interest with other companies
  
  📝 AWAITING SIGNATURE (deal proposal sent):
     - Companies 9-12: Have created offers, waiting for signature
  
  ⏳ ONGOING DEALS (signed contracts, in progress):
     - Companies 13-16: Have active ongoing deals
  
  ✅ COMPLETED DEALS (finished with reviews):
     - Companies 17-20: Have completed deals with reviews

================================================================================
"""

import uuid
import sys
import datetime
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User, Company, CompanyMember, CompanyJoinRequest, Service, DealProposal, ActiveDeal, BarterDeal, Contract, Review, ServiceInterest, TradeRequest, Message

def seed_database(force_reset=False):
    """Populate database with example data"""
    app = create_app()
    
    with app.app_context():
        # Standard seed data usernames
        seed_usernames = [
            'alice_johnson', 'bob_smith', 'charlie_brown', 'diana_prince', 'edward_norton',
            'fiona_apple', 'george_lucas', 'hannah_montana', 'isaac_newton', 'julia_roberts',
            'kevin_hart', 'laura_palmer', 'mark_twain', 'nina_simone', 'oscar_wilde',
            'patricia_hill', 'quincy_jones', 'rachel_green', 'samuel_jackson', 'tina_turner',
            'kyle_reese', 'lucy_liu', 'michael_scott', 'natalie_portman', 'oliver_twist',
            'penny_lane', 'quentin_blake', 'rita_hayworth', 'steve_jobs', 'tara_reid',
            'uma_thurman', 'victor_hugo', 'walter_white', 'xena_warrior', 'yasmine_bleeth',
            'zack_morris', 'amy_adams', 'brad_pitt', 'cate_blanchett', 'denzel_washington'
        ]
        
        # Check if seed data already exists
        seed_users_count = db.session.query(User).filter(User.username.in_(seed_usernames)).count()
        
        if seed_users_count > 0 and not force_reset:
            print("="*70)
            print("⚠️  SEED DATA ALREADY EXISTS!")
            print("="*70)
            print(f"\nFound {seed_users_count}/40 seed users in database.")
            print("Running seed_data.py again would create DUPLICATE accounts!")
            print("\nOptions:")
            print("  1. Do nothing - your existing data is safe")
            print("  2. Reset database: python -m flask db reset")
            print("  3. Force-seed anyway (NOT RECOMMENDED): python seed_data.py --reset")
            print("\nNo changes made. Your data is protected.")
            print("="*70)
            return
        
        if force_reset and seed_users_count > 0:
            print("="*70)
            print("🔄 FORCE RESET INITIATED")
            print("="*70)
            print("\n⚠️  Clearing existing seed data...")
            
            # Delete in correct order to avoid FK conflicts
            try:
                db.session.query(Review).delete()
                db.session.query(ServiceInterest).delete()
                db.session.query(TradeRequest).delete()
                db.session.query(Message).delete()  # Delete messages before deal proposals
                db.session.query(Contract).delete()
                db.session.query(ActiveDeal).delete()
                db.session.query(BarterDeal).delete()
                db.session.query(DealProposal).delete()
                db.session.query(Service).delete()
                db.session.query(CompanyJoinRequest).delete()
                db.session.query(CompanyMember).delete()
                db.session.query(Company).delete()
                db.session.query(User).filter(User.username.in_(seed_usernames)).delete()
                db.session.commit()
                print("✓ Cleared existing seed data")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error clearing data: {e}")
                return
        
        print("✓ Database is empty, proceeding with seeding...")
        print()
        
        # Create 40 users (20 admins + 20 members)
        print("Creating 40 users...")
        users = []
        user_names = [
            # First 20: Admins
            'Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Edward Norton',
            'Fiona Apple', 'George Lucas', 'Hannah Montana', 'Isaac Newton', 'Julia Roberts',
            'Kyle Reese', 'Lucy Liu', 'Michael Scott', 'Natalie Portman', 'Oliver Twist',
            'Penny Lane', 'Quentin Blake', 'Rita Hayworth', 'Steve Jobs', 'Tara Reid',
            # Last 20: Members
            'Kevin Hart', 'Laura Palmer', 'Mark Twain', 'Nina Simone', 'Oscar Wilde',
            'Patricia Hill', 'Quincy Jones', 'Rachel Green', 'Samuel Jackson', 'Tina Turner',
            'Uma Thurman', 'Victor Hugo', 'Walter White', 'Xena Warrior', 'Yasmine Bleeth',
            'Zack Morris', 'Amy Adams', 'Brad Pitt', 'Cate Blanchett', 'Denzel Washington'
        ]
        
        for i, name in enumerate(user_names):
            username = name.lower().replace(' ', '_')
            new_user = User(
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
        
        # Create 20 companies (for the 20 admins)
        print("Creating 20 companies with admins...")
        companies = []
        company_names = [
            'Tech Solutions Inc', 'Green Energy Co', 'Digital Marketing Pro', 'Finance Hub',
            'Creative Studios', 'Legal Associates', 'HR Consulting', 'Design Factory',
            'Development Labs', 'Business Strategy', 'Data Analytics Pro', 'Content Creators Hub',
            'Sales Excellence', 'Event Planning Co', 'Supply Chain Solutions', 'Customer Success Team',
            'Video Production Studio', 'Translation Services', 'Innovation Workshop', 'Quality Assurance Experts'
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
            'Business strategy and organizational development',
            'Advanced data analytics and business intelligence',
            'Content creation and copywriting services',
            'Sales training and revenue optimization',
            'Professional event planning and coordination',
            'Supply chain optimization and logistics',
            'Customer support and success strategies',
            'Video production and multimedia content',
            'Professional translation and localization',
            'Innovation consulting and R&D support',
            'Quality assurance and testing services'
        ]
        
        for i in range(20):
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
        
        # Assign first 20 users as admins of the 20 companies
        print("Assigning admins to companies...")
        for i in range(20):
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
        print("✓ Assigned 20 users as admins")
        
        # Assign remaining 20 users (20-40) as members of companies
        print("Assigning members to companies...")
        for i in range(20, 40):
            company = companies[i - 20]  # Each company gets 1 member
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
        print("✓ Assigned 20 users as members")
        
        # Create 5 services for each company
        print("Creating services for each company...")
        
        service_templates = [
            # Company 0: Tech Solutions Inc
            [
                {'title': 'Web Development', 'description': 'Full-stack web application development using modern frameworks', 'duration': 40, 'categories': 'Development,IT'},
                {'title': 'Cloud Architecture', 'description': 'Design and implement scalable cloud infrastructure', 'duration': 30, 'categories': 'IT,Operations'},
                {'title': 'Database Optimization', 'description': 'Performance tuning and optimization of database systems', 'duration': 20, 'categories': 'IT,Development'},
                {'title': 'System Integration', 'description': 'Integration of legacy systems with modern applications', 'duration': 50, 'categories': 'IT,Consulting'},
                {'title': 'Technical Support', 'description': '24/7 technical support and maintenance services', 'duration': 160, 'categories': 'IT,Customer Support'},
            ],
            # Company 1: Green Energy Co
            [
                {'title': 'Solar Installation', 'description': 'Professional solar panel installation and setup', 'duration': 80, 'categories': 'Operations'},
                {'title': 'Energy Audit', 'description': 'Comprehensive energy consumption analysis', 'duration': 25, 'categories': 'Consulting'},
                {'title': 'Renewable Transition', 'description': 'Help transition to renewable energy sources', 'duration': 60, 'categories': 'Consulting,Operations'},
                {'title': 'Maintenance Services', 'description': 'Regular maintenance of renewable systems', 'duration': 120, 'categories': 'Operations,Customer Support'},
                {'title': 'Staff Training', 'description': 'Staff training on renewable energy systems', 'duration': 15, 'categories': 'HR'},
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
            # Company 9: Business Strategy
            [
                {'title': 'Strategic Planning', 'description': 'Business strategy and planning sessions', 'duration': 60, 'categories': 'Consulting'},
                {'title': 'Market Analysis', 'description': 'Market research and competitive analysis', 'duration': 45, 'categories': 'Consulting,Marketing'},
                {'title': 'Business Transformation', 'description': 'Organizational transformation and change management', 'duration': 150, 'categories': 'Consulting,Operations'},
                {'title': 'Process Improvement', 'description': 'Business process optimization', 'duration': 70, 'categories': 'Consulting,Operations'},
                {'title': 'Leadership Coaching', 'description': 'Executive coaching and development', 'duration': 50, 'categories': 'Consulting,HR'},
            ],
            # Company 10: Data Analytics Pro
            [
                {'title': 'Data Visualization', 'description': 'Create interactive dashboards and visual reports', 'duration': 45, 'categories': 'IT,Consulting'},
                {'title': 'Business Intelligence', 'description': 'BI strategy and implementation', 'duration': 80, 'categories': 'IT,Consulting'},
                {'title': 'Predictive Analytics', 'description': 'Machine learning and predictive modeling', 'duration': 100, 'categories': 'IT,Development'},
                {'title': 'Data Migration', 'description': 'Safe data migration between systems', 'duration': 60, 'categories': 'IT,Operations'},
                {'title': 'Analytics Training', 'description': 'Team training on analytics tools', 'duration': 30, 'categories': 'IT,HR'},
            ],
            # Company 11: Content Creators Hub
            [
                {'title': 'Blog Writing', 'description': 'Professional blog posts and articles', 'duration': 20, 'categories': 'Marketing'},
                {'title': 'Copywriting', 'description': 'Persuasive copy for marketing materials', 'duration': 15, 'categories': 'Marketing,Sales'},
                {'title': 'Email Campaigns', 'description': 'Email marketing content creation', 'duration': 25, 'categories': 'Marketing'},
                {'title': 'Social Media Content', 'description': 'Engaging social media posts', 'duration': 30, 'categories': 'Marketing'},
                {'title': 'Video Scripts', 'description': 'Professional video script writing', 'duration': 18, 'categories': 'Marketing'},
            ],
            # Company 12: Sales Excellence
            [
                {'title': 'Sales Training', 'description': 'Comprehensive sales skills training', 'duration': 50, 'categories': 'Sales,HR'},
                {'title': 'Lead Generation', 'description': 'B2B lead generation strategies', 'duration': 70, 'categories': 'Sales,Marketing'},
                {'title': 'Sales Process Optimization', 'description': 'Streamline your sales pipeline', 'duration': 45, 'categories': 'Sales,Consulting'},
                {'title': 'CRM Implementation', 'description': 'CRM system setup and training', 'duration': 60, 'categories': 'Sales,IT'},
                {'title': 'Negotiation Coaching', 'description': 'Advanced negotiation techniques', 'duration': 35, 'categories': 'Sales,Consulting'},
            ],
            # Company 13: Event Planning Co
            [
                {'title': 'Corporate Events', 'description': 'Full-service corporate event planning', 'duration': 120, 'categories': 'Operations'},
                {'title': 'Conference Management', 'description': 'End-to-end conference organization', 'duration': 150, 'categories': 'Operations,Marketing'},
                {'title': 'Team Building Activities', 'description': 'Plan engaging team building events', 'duration': 40, 'categories': 'HR,Operations'},
                {'title': 'Virtual Events', 'description': 'Online event setup and management', 'duration': 50, 'categories': 'IT,Operations'},
                {'title': 'Event Marketing', 'description': 'Promotional strategy for events', 'duration': 35, 'categories': 'Marketing'},
            ],
            # Company 14: Supply Chain Solutions
            [
                {'title': 'Logistics Optimization', 'description': 'Streamline your logistics operations', 'duration': 65, 'categories': 'Operations,Consulting'},
                {'title': 'Inventory Management', 'description': 'Efficient inventory control systems', 'duration': 55, 'categories': 'Operations'},
                {'title': 'Vendor Management', 'description': 'Optimize supplier relationships', 'duration': 45, 'categories': 'Operations,Consulting'},
                {'title': 'Supply Chain Analysis', 'description': 'Comprehensive supply chain audit', 'duration': 70, 'categories': 'Operations,Consulting'},
                {'title': 'Procurement Strategy', 'description': 'Strategic procurement planning', 'duration': 50, 'categories': 'Operations,Finance'},
            ],
            # Company 15: Customer Success Team
            [
                {'title': 'Customer Onboarding', 'description': 'Smooth customer onboarding processes', 'duration': 40, 'categories': 'Customer Support'},
                {'title': 'Support Training', 'description': 'Train your support team effectively', 'duration': 35, 'categories': 'Customer Support,HR'},
                {'title': 'Help Desk Setup', 'description': 'Implement efficient help desk systems', 'duration': 60, 'categories': 'Customer Support,IT'},
                {'title': 'Customer Feedback Analysis', 'description': 'Analyze and act on customer feedback', 'duration': 30, 'categories': 'Customer Support,Marketing'},
                {'title': 'Retention Strategies', 'description': 'Develop customer retention programs', 'duration': 50, 'categories': 'Customer Support,Consulting'},
            ],
            # Company 16: Video Production Studio
            [
                {'title': 'Commercial Videos', 'description': 'Professional commercial video production', 'duration': 80, 'categories': 'Marketing,Design'},
                {'title': 'Explainer Videos', 'description': 'Animated explainer videos', 'duration': 60, 'categories': 'Marketing,Design'},
                {'title': 'Video Editing', 'description': 'Professional video editing services', 'duration': 40, 'categories': 'Design'},
                {'title': 'Corporate Presentations', 'description': 'High-quality presentation videos', 'duration': 50, 'categories': 'Marketing'},
                {'title': 'Social Media Videos', 'description': 'Short-form social media content', 'duration': 30, 'categories': 'Marketing'},
            ],
            # Company 17: Translation Services
            [
                {'title': 'Document Translation', 'description': 'Professional document translation', 'duration': 35, 'categories': 'Operations'},
                {'title': 'Website Localization', 'description': 'Full website localization services', 'duration': 70, 'categories': 'IT,Marketing'},
                {'title': 'Legal Translation', 'description': 'Specialized legal document translation', 'duration': 45, 'categories': 'Legal'},
                {'title': 'Marketing Copy Translation', 'description': 'Marketing content localization', 'duration': 30, 'categories': 'Marketing'},
                {'title': 'Interpretation Services', 'description': 'Live interpretation for meetings', 'duration': 20, 'categories': 'Operations'},
            ],
            # Company 18: Innovation Workshop
            [
                {'title': 'Innovation Strategy', 'description': 'Develop innovation roadmaps', 'duration': 60, 'categories': 'Consulting'},
                {'title': 'Product Development', 'description': 'New product development consulting', 'duration': 100, 'categories': 'Consulting,Development'},
                {'title': 'Design Thinking Workshops', 'description': 'Facilitated design thinking sessions', 'duration': 40, 'categories': 'Consulting,HR'},
                {'title': 'R&D Strategy', 'description': 'Research and development planning', 'duration': 75, 'categories': 'Consulting'},
                {'title': 'Technology Scouting', 'description': 'Identify emerging technologies', 'duration': 50, 'categories': 'Consulting,IT'},
            ],
            # Company 19: Quality Assurance Experts
            [
                {'title': 'Software Testing', 'description': 'Comprehensive software QA testing', 'duration': 80, 'categories': 'IT,Development'},
                {'title': 'Test Automation', 'description': 'Automated testing framework setup', 'duration': 90, 'categories': 'IT,Development'},
                {'title': 'Quality Audits', 'description': 'Quality management system audits', 'duration': 50, 'categories': 'Operations,Consulting'},
                {'title': 'Performance Testing', 'description': 'Load and performance testing', 'duration': 60, 'categories': 'IT,Development'},
                {'title': 'QA Process Design', 'description': 'Design quality assurance processes', 'duration': 55, 'categories': 'Operations,Consulting'},
            ],
        ]
        
        total_services = 0
        all_services = []  # Store services for later use in trade flows
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
                all_services.append(service)
                total_services += 1
        
        db.session.commit()
        print(f"✓ Created {total_services} services (5 per company)")
        
        # Create trade flows for testing different statuses
        print("Creating trade flow test data...")
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Group 1: ONE-SIDED INTEREST (Companies 0-3)
        # Company 0 requests services from Companies 10, 11
        # Company 1 requests services from Companies 12, 13
        # Company 2 requests services from Companies 14, 15
        # Company 3 requests services from Companies 16, 17
        trade_requests_count = 0
        one_sided_pairs = [(0, 10), (0, 11), (1, 12), (1, 13), (2, 14), (2, 15), (3, 16), (3, 17)]
        for requesting_idx, target_idx in one_sided_pairs:
            # Request 2 services from target company
            target_services = [s for s in all_services if s.company_id == companies[target_idx].company_id][:2]
            for service in target_services:
                trade_request = TradeRequest(
                    request_id=uuid.uuid4(),
                    requesting_company_id=companies[requesting_idx].company_id,
                    requested_service_id=service.service_id,
                    validity_days=30,
                    status='active',
                    created_at=now - datetime.timedelta(days=5),
                    expires_at=now + datetime.timedelta(days=25)
                )
                db.session.add(trade_request)
                trade_requests_count += 1
        
        db.session.commit()
        print(f"✓ Created {trade_requests_count} one-sided trade requests")
        
        # Group 2: MUTUAL INTEREST (Companies 4-7)
        # Create reciprocal trade requests (match made scenario)
        # Company 4 ↔ Company 11
        # Company 5 ↔ Company 12
        # Company 6 ↔ Company 13
        # Company 7 ↔ Company 14
        mutual_pairs = [(4, 11), (5, 12), (6, 13), (7, 14)]
        mutual_count = 0
        for comp_a_idx, comp_b_idx in mutual_pairs:
            # Company A requests from Company B
            service_b = [s for s in all_services if s.company_id == companies[comp_b_idx].company_id][0]
            trade_req_a = TradeRequest(
                request_id=uuid.uuid4(),
                requesting_company_id=companies[comp_a_idx].company_id,
                requested_service_id=service_b.service_id,
                validity_days=30,
                status='active',
                created_at=now - datetime.timedelta(days=7),
                expires_at=now + datetime.timedelta(days=23)
            )
            db.session.add(trade_req_a)
            
            # Company B requests from Company A (mutual!)
            service_a = [s for s in all_services if s.company_id == companies[comp_a_idx].company_id][0]
            trade_req_b = TradeRequest(
                request_id=uuid.uuid4(),
                requesting_company_id=companies[comp_b_idx].company_id,
                requested_service_id=service_a.service_id,
                validity_days=30,
                status='active',
                created_at=now - datetime.timedelta(days=6),
                expires_at=now + datetime.timedelta(days=24)
            )
            db.session.add(trade_req_b)
            mutual_count += 2
        
        db.session.commit()
        print(f"✓ Created {mutual_count} mutual trade requests (match made)")
        
        # Group 3: AWAITING SIGNATURE (Companies 8-11)
        # Create deal proposals awaiting signatures
        # Company 8 ↔ Company 15
        # Company 9 ↔ Company 16
        # Company 10 ↔ Company 17
        # Company 11 ↔ Company 18
        awaiting_pairs = [(8, 15), (9, 16), (10, 17), (11, 18)]
        proposals_count = 0
        for from_idx, to_idx in awaiting_pairs:
            service_from = [s for s in all_services if s.company_id == companies[from_idx].company_id][0]
            service_to = [s for s in all_services if s.company_id == companies[to_idx].company_id][0]
            
            proposal = DealProposal(
                proposal_id=uuid.uuid4(),
                from_company_id=companies[from_idx].company_id,
                to_company_id=companies[to_idx].company_id,
                from_service_id=service_from.service_id,
                to_service_id=service_to.service_id,
                barter_coins_offered=0,
                status='pending',
                created_at=now - datetime.timedelta(days=3)
            )
            db.session.add(proposal)
            proposals_count += 1
        
        db.session.commit()
        print(f"✓ Created {proposals_count} deal proposals awaiting signature")
        
        # Group 4: ONGOING DEALS (Companies 12-15)
        # Create active deals from accepted proposals
        # Company 12 ↔ Company 2
        # Company 13 ↔ Company 3
        # Company 14 ↔ Company 4
        # Company 15 ↔ Company 5
        ongoing_pairs = [(12, 2), (13, 3), (14, 4), (15, 5)]
        ongoing_count = 0
        for from_idx, to_idx in ongoing_pairs:
            service_from = [s for s in all_services if s.company_id == companies[from_idx].company_id][0]
            service_to = [s for s in all_services if s.company_id == companies[to_idx].company_id][0]
            
            # Create deal proposal (accepted)
            proposal = DealProposal(
                proposal_id=uuid.uuid4(),
                from_company_id=companies[from_idx].company_id,
                to_company_id=companies[to_idx].company_id,
                from_service_id=service_from.service_id,
                to_service_id=service_to.service_id,
                barter_coins_offered=0,
                status='accepted',
                created_at=now - datetime.timedelta(days=10)
            )
            db.session.add(proposal)
            db.session.flush()  # Flush to get the proposal_id
            
            # Create active deal
            active_deal = ActiveDeal(
                active_deal_id=uuid.uuid4(),
                proposal_id=proposal.proposal_id,
                from_company_completed=False,
                to_company_completed=False,
                status='in_progress',
                created_at=now - datetime.timedelta(days=10)
            )
            db.session.add(active_deal)
            ongoing_count += 1
        
        db.session.commit()
        print(f"✓ Created {ongoing_count} ongoing active deals")
        
        # Group 5: COMPLETED DEALS (Companies 16-19)
        # Create completed deals with reviews
        # Company 16 ↔ Company 6
        # Company 17 ↔ Company 7
        # Company 18 ↔ Company 8
        # Company 19 ↔ Company 9
        completed_pairs = [(16, 6), (17, 7), (18, 8), (19, 9)]
        completed_count = 0
        reviews_count = 0
        for from_idx, to_idx in completed_pairs:
            service_from = [s for s in all_services if s.company_id == companies[from_idx].company_id][0]
            service_to = [s for s in all_services if s.company_id == companies[to_idx].company_id][0]
            
            # Create deal proposal (accepted)
            proposal = DealProposal(
                proposal_id=uuid.uuid4(),
                from_company_id=companies[from_idx].company_id,
                to_company_id=companies[to_idx].company_id,
                from_service_id=service_from.service_id,
                to_service_id=service_to.service_id,
                barter_coins_offered=0,
                status='accepted',
                created_at=now - datetime.timedelta(days=60)
            )
            db.session.add(proposal)
            db.session.flush()  # Flush to get the proposal_id
            
            # Create active deal (completed)
            active_deal = ActiveDeal(
                active_deal_id=uuid.uuid4(),
                proposal_id=proposal.proposal_id,
                from_company_completed=True,
                to_company_completed=True,
                status='completed',
                created_at=now - datetime.timedelta(days=60),
                completed_at=now - datetime.timedelta(days=15)
            )
            db.session.add(active_deal)
            completed_count += 1
            
            # Create reviews from both companies
            # Company FROM reviews Company TO's service
            review_from = Review(
                review_id=uuid.uuid4(),
                deal_id=active_deal.active_deal_id,  # Reference to active_deal
                reviewer_id=users[from_idx].user_id,
                reviewed_company_id=companies[to_idx].company_id,
                reviewed_service_id=service_to.service_id,
                rating=5,
                comment=f"Excellent service from {companies[to_idx].name}! Highly professional and delivered great results.",
                created_at=now - datetime.timedelta(days=14)
            )
            db.session.add(review_from)
            reviews_count += 1
            
            # Company TO reviews Company FROM's service
            review_to = Review(
                review_id=uuid.uuid4(),
                deal_id=active_deal.active_deal_id,  # Reference to active_deal
                reviewer_id=users[to_idx].user_id,
                reviewed_company_id=companies[from_idx].company_id,
                reviewed_service_id=service_from.service_id,
                rating=4,
                comment=f"Great collaboration with {companies[from_idx].name}. Would work together again!",
                created_at=now - datetime.timedelta(days=14)
            )
            db.session.add(review_to)
            reviews_count += 1
        
        db.session.commit()
        print(f"✓ Created {completed_count} completed deals with {reviews_count} reviews")
        
        print("\n" + "="*70)
        print("✓ Database seeding completed successfully!")
        print("="*70)
        print("\n📊 SUMMARY:")
        print(f"  • 40 users (20 admins + 20 members)")
        print(f"  • 20 companies")
        print(f"  • 100 services (5 per company)")
        print(f"  • Trade Flow Statuses:")
        print(f"    - {trade_requests_count} one-sided trade requests (Companies 0-3)")
        print(f"    - {mutual_count} mutual interest pairs (Companies 4-7)")
        print(f"    - {proposals_count} deal proposals awaiting signature (Companies 8-11)")
        print(f"    - {ongoing_count} ongoing active deals (Companies 12-15)")
        print(f"    - {completed_count} completed deals with {reviews_count} reviews (Companies 16-19)")
        
        print("\n👤 TEST ACCOUNTS (Admin):")
        print("=" * 70)
        for i in range(20):
            print(f"{i+1:2d}. {user_names[i].lower().replace(' ', '_'):25s} / testgebruiker → {company_names[i]}")
        
        print("\n👤 TEST ACCOUNTS (Members):")
        print("=" * 70)
        for i in range(20, 40):
            company_idx = i - 20
            print(f"{i-19:2d}. {user_names[i].lower().replace(' ', '_'):25s} / testgebruiker → {company_names[company_idx]}")

if __name__ == '__main__':
    # Check for --reset flag
    force_reset = '--reset' in sys.argv
    
    if force_reset:
        print("\n⚠️  WARNING: Using --reset flag!")
        print("This will DELETE existing seed data and recreate it.")
        response = input("Are you SURE? Type 'yes' to continue: ").strip().lower()
        if response != 'yes':
            print("Aborted. No changes made.")
            sys.exit(0)
    
    seed_database(force_reset=force_reset)
