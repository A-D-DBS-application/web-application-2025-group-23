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
from app.models import (
    db,
    User,
    Company,
    CompanyMember,
    CompanyJoinRequest,
    Service,
    DealProposal,
    ActiveDeal,
    Review,
    TradeRequest,
    TradeflowView,
    ServiceViewEvent,
)

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
                db.session.query(TradeRequest).delete()
                db.session.query(ActiveDeal).delete()
                db.session.query(DealProposal).delete()
                db.session.query(ServiceViewEvent).delete()
                db.session.query(TradeflowView).delete()
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
                {'title': 'Web Development', 'description': """Our full-stack web application development service provides comprehensive solutions using cutting-edge modern frameworks including React, Vue.js, Angular for frontend and Node.js, Python Django, or Ruby on Rails for backend. We specialize in creating responsive, scalable, and maintainable web applications that deliver exceptional user experiences. Our experienced developers follow industry best practices, implement robust security measures, and ensure optimal performance across all devices and browsers. From initial concept through deployment and ongoing maintenance, we partner with you to build powerful web solutions that drive business growth.""", 'duration': 40, 'categories': 'Development,IT'},
                {'title': 'Cloud Architecture', 'description': """Transform your infrastructure with our expert cloud architecture services. We design and implement highly scalable, reliable, and cost-effective cloud solutions using leading platforms like AWS, Azure, and Google Cloud. Our architects assess your current infrastructure, identify optimization opportunities, and create tailored migration strategies that minimize downtime and maximize efficiency. We implement containerization with Docker and Kubernetes, set up auto-scaling configurations, establish disaster recovery protocols, and ensure compliance with industry standards. Whether you need a complete cloud migration or optimization of existing cloud resources, our team delivers robust architectures that grow with your business.""", 'duration': 30, 'categories': 'IT,Operations'},
                {'title': 'Database Optimization', 'description': """Unlock the full potential of your database systems with our specialized performance tuning and optimization services. We conduct comprehensive audits of your database infrastructure, identify bottlenecks, and implement strategic improvements that dramatically enhance query performance and reduce response times. Our experts work with all major database platforms including PostgreSQL, MySQL, MongoDB, Oracle, and SQL Server. We optimize indexing strategies, refine query execution plans, implement effective caching mechanisms, and establish monitoring systems to maintain peak performance. Experience faster applications, improved user satisfaction, and reduced infrastructure costs through expert database optimization.""", 'duration': 20, 'categories': 'IT,Development'},
                {'title': 'System Integration', 'description': """Bridge the gap between legacy systems and modern applications with our comprehensive system integration services. We specialize in connecting disparate systems, enabling seamless data flow, and creating unified technology ecosystems that enhance operational efficiency. Our integration experts utilize industry-standard protocols, APIs, and middleware solutions to establish reliable communication channels between your existing infrastructure and new applications. Whether you need to integrate CRM systems, ERP platforms, payment gateways, or custom applications, we deliver secure, scalable integration solutions with robust error handling and monitoring. Modernize your technology stack while preserving valuable legacy investments.""", 'duration': 50, 'categories': 'IT,Consulting'},
                {'title': 'Technical Support', 'description': """Ensure uninterrupted operations with our comprehensive 24/7 technical support and maintenance services. Our dedicated support team provides round-the-clock monitoring, rapid incident response, and proactive maintenance to keep your systems running smoothly. We offer multi-tier support with escalation procedures, regular system health checks, security patch management, performance monitoring, and detailed reporting. Our service includes helpdesk support for end users, server maintenance, application updates, backup verification, and disaster recovery support. With guaranteed response times and experienced technicians available anytime, we provide peace of mind and allow you to focus on your core business while we handle your technical infrastructure.""", 'duration': 160, 'categories': 'IT,Customer Support'},
            ],
            # Company 1: Green Energy Co
            [
                {'title': 'Solar Installation', 'description': """Transform your energy consumption with our professional solar panel installation services. Our certified technicians handle every aspect of your solar project from initial site assessment and system design through installation and grid connection. We work with premium solar equipment, ensure optimal panel placement for maximum energy generation, and handle all permitting and regulatory requirements. Our installations meet or exceed industry standards and come with comprehensive warranties. We provide detailed energy production estimates, financing guidance, and post-installation monitoring to ensure your system performs as expected. Make the switch to clean, renewable energy with confidence.""", 'duration': 80, 'categories': 'Operations'},
                {'title': 'Energy Audit', 'description': """Discover opportunities to reduce energy costs and environmental impact with our comprehensive energy audit services. Our certified energy auditors conduct thorough assessments of your facilities, analyzing energy consumption patterns, identifying inefficiencies, and quantifying potential savings. We utilize advanced diagnostic tools including thermal imaging, blower door tests, and power monitoring equipment to uncover hidden energy waste. You'll receive a detailed report with prioritized recommendations, cost-benefit analyses, and implementation roadmaps. Our audits cover lighting systems, HVAC equipment, building envelope, process equipment, and operational practices. Start your journey toward improved energy efficiency and reduced operating costs.""", 'duration': 25, 'categories': 'Consulting'},
                {'title': 'Renewable Transition', 'description': """Navigate the complex transition to renewable energy with our expert guidance and implementation support. We develop customized renewable energy strategies that align with your sustainability goals, budget constraints, and operational requirements. Our comprehensive service includes feasibility studies, technology selection, financial modeling, incentive identification, and project management. We help you evaluate solar, wind, geothermal, and biomass options, assess grid integration requirements, and plan for energy storage solutions. Our team coordinates with utilities, manages contractor relationships, and ensures smooth implementation. Take control of your energy future while reducing costs and meeting sustainability commitments.""", 'duration': 60, 'categories': 'Consulting,Operations'},
                {'title': 'Maintenance Services', 'description': """Protect your renewable energy investment with our comprehensive maintenance services designed to maximize system performance and longevity. We provide scheduled preventive maintenance, performance monitoring, cleaning services, and rapid repair response for solar panels, wind turbines, and other renewable energy systems. Our technicians conduct thorough inspections, test critical components, verify energy production levels, and address issues before they impact performance. We maintain detailed service records, track system efficiency over time, and provide regular performance reports. With our maintenance services, you can ensure optimal energy generation, extend equipment lifespan, and protect warranty coverage while avoiding costly downtime.""", 'duration': 120, 'categories': 'Operations,Customer Support'},
                {'title': 'Staff Training', 'description': """Empower your team with specialized knowledge through our comprehensive renewable energy training programs. We offer customized training sessions covering solar technology, system maintenance, safety procedures, performance monitoring, and troubleshooting techniques. Our experienced instructors provide hands-on learning experiences, technical documentation, and certification opportunities. Training can be delivered on-site or at our facilities, with content tailored to your specific systems and staff roles. Whether you need basic awareness training for facility managers or advanced technical training for maintenance personnel, we ensure your team has the knowledge and skills to effectively manage your renewable energy systems and maximize their performance.""", 'duration': 15, 'categories': 'HR'},
            ],
            # Digital Marketing Pro
            [
                {'title': 'Social Media Strategy', 'description': """Elevate your brand presence with data-driven social media strategies that engage audiences and drive business results. Our social media experts conduct comprehensive audits of your current presence, analyze competitor strategies, and identify opportunities for growth across all major platforms. We develop customized content calendars, establish brand voice guidelines, create engagement strategies, and implement community management protocols. Our campaigns integrate paid advertising, influencer partnerships, and organic growth tactics to maximize reach and ROI. We provide ongoing performance monitoring, A/B testing, and strategy refinement to ensure continuous improvement. Transform your social media channels into powerful marketing assets that build brand awareness, foster customer loyalty, and generate measurable business outcomes.""", 'duration': 35, 'categories': 'Marketing,Consulting'},
                {'title': 'SEO Optimization', 'description': """Dominate search engine rankings and drive organic traffic with our comprehensive SEO optimization services. We conduct thorough keyword research, technical site audits, and competitive analyses to develop targeted optimization strategies. Our services include on-page optimization (meta tags, content optimization, internal linking), technical SEO (site speed, mobile responsiveness, structured data), and off-page optimization (link building, local SEO). We address indexing issues, improve site architecture, and ensure your website meets current search engine guidelines. Regular performance reporting tracks ranking improvements, traffic growth, and conversion metrics. Our white-hat techniques deliver sustainable results that improve visibility, attract qualified traffic, and increase conversions while building long-term search authority.""", 'duration': 45, 'categories': 'Marketing,IT'},
                {'title': 'Content Creation', 'description': """Captivate your audience with professionally crafted content that informs, engages, and converts. Our creative team produces high-quality blog posts, articles, website copy, social media content, email campaigns, and visual assets tailored to your brand voice and target audience. We conduct thorough audience research, develop content strategies aligned with business objectives, and create compelling narratives that resonate with readers. Our content is optimized for search engines, formatted for readability, and designed to drive desired actions. From initial concept through final delivery, we ensure every piece of content serves your marketing goals, strengthens brand authority, and provides genuine value to your audience while maintaining consistent messaging across all channels.""", 'duration': 50, 'categories': 'Marketing,Design'},
                {'title': 'Analytics Review', 'description': """Gain actionable insights from your marketing data with our comprehensive analytics review services. We analyze performance metrics across all digital channels including website traffic, social media engagement, email campaigns, and paid advertising. Our experts identify trends, uncover optimization opportunities, and provide clear recommendations backed by data. We set up custom dashboards, establish meaningful KPIs, track conversion funnels, and analyze user behavior patterns. Our detailed reports translate complex data into understandable insights that inform strategic decisions. Whether you need one-time analysis or ongoing reporting, we help you understand what's working, what's not, and how to improve marketing performance and ROI continuously.""", 'duration': 18, 'categories': 'Marketing,Consulting'},
                {'title': 'Brand Development', 'description': """Build a powerful, memorable brand identity that differentiates your business and resonates with target audiences. Our comprehensive brand development process includes market research, competitive analysis, positioning strategy, visual identity creation, and brand guidelines development. We craft compelling brand stories, define unique value propositions, and establish consistent messaging frameworks. Our deliverables include logo design, color palettes, typography systems, brand voice guidelines, and application examples. We ensure your brand communicates authentically across all touchpoints while standing out in competitive markets. Whether launching a new brand or refreshing an existing one, we create cohesive identities that build recognition, foster emotional connections, and support long-term business growth.""", 'duration': 70, 'categories': 'Marketing,Design,Consulting'},
            ],
            # Finance Hub
            [
                {'title': 'Financial Planning', 'description': """Achieve your financial objectives with strategic planning services tailored to your unique business circumstances. Our certified financial planners analyze your current financial position, identify goals, assess risk tolerance, and develop comprehensive strategies for sustainable growth. We provide cash flow forecasting, capital allocation recommendations, debt management strategies, and succession planning. Our planning process considers tax implications, market conditions, and industry-specific challenges to create actionable roadmaps. We deliver detailed financial models, scenario analyses, and implementation guidance with ongoing support to adjust strategies as circumstances change. Whether you need retirement planning, business expansion strategies, or wealth preservation approaches, we provide expert guidance to build financial security and achieve long-term success.""", 'duration': 55, 'categories': 'Finance,Consulting'},
                {'title': 'Tax Consultation', 'description': """Navigate complex tax regulations and minimize liabilities with expert tax consultation services. Our experienced tax professionals stay current with constantly changing tax laws to identify optimization opportunities while ensuring full compliance. We provide strategic tax planning, entity structure recommendations, deduction maximization strategies, and audit defense support. Our services cover income tax, sales tax, payroll tax, and specialized situations including international taxation, mergers and acquisitions, and restructuring. We analyze your specific circumstances to develop proactive strategies that legally minimize tax burdens and avoid costly penalties. Year-round support ensures you make tax-smart decisions, maintain proper documentation, and stay prepared for filing deadlines while taking advantage of available credits and deductions.""", 'duration': 40, 'categories': 'Finance,Legal'},
                {'title': 'Accounting Services', 'description': """Maintain accurate financial records and gain clear visibility into business performance with our comprehensive accounting services. We handle daily bookkeeping, accounts payable and receivable, bank reconciliation, payroll processing, and financial statement preparation. Our team uses industry-leading accounting software, implements proper internal controls, and follows GAAP standards to ensure accuracy and compliance. We provide monthly financial reports, cash flow statements, balance sheets, and profit and loss statements with meaningful commentary. Our services include expense tracking, budget variance analysis, and financial forecasting. From startups needing basic bookkeeping to established businesses requiring full-service accounting departments, we deliver reliable financial management that supports informed decision-making and business growth.""", 'duration': 150, 'categories': 'Accounting,Finance'},
                {'title': 'Investment Advisory', 'description': """Optimize investment performance with personalized advisory services based on thorough analysis and strategic thinking. Our investment advisors evaluate your current portfolio, assess risk-return profiles, and develop diversification strategies aligned with your financial goals and time horizons. We provide research-backed recommendations across asset classes including stocks, bonds, real estate, and alternative investments. Our analysis considers market conditions, economic trends, tax implications, and liquidity needs. We monitor portfolio performance continuously, rebalance allocations as needed, and adjust strategies based on changing circumstances or goals. With transparent fee structures and fiduciary responsibility, we provide unbiased advice focused entirely on your financial success and long-term wealth building objectives.""", 'duration': 35, 'categories': 'Finance,Consulting'},
                {'title': 'Audit Support', 'description': """Navigate financial audits confidently with comprehensive preparation and support services. We help organizations prepare for external audits by reviewing financial records, identifying potential issues, organizing documentation, and implementing corrective measures. Our audit support includes internal control assessments, compliance reviews, financial statement analysis, and workpaper preparation. We coordinate with external auditors, respond to information requests, and provide explanations for complex transactions. Our team identifies areas requiring adjustment before auditors discover them, reducing the risk of findings and qualifications. Whether facing routine annual audits, regulatory examinations, or special investigations, we provide experienced guidance that streamlines the audit process, ensures compliance, and maintains stakeholder confidence in your financial reporting.""", 'duration': 85, 'categories': 'Accounting,Finance,Legal'},
            ],
            # Creative Studios
            [
                {'title': 'Logo Design', 'description': """Create a distinctive visual identity with custom logo design that captures your brand essence and makes lasting impressions. Our design process begins with comprehensive discovery sessions to understand your business, values, target audience, and competitive landscape. We develop multiple concept directions, refine chosen designs based on feedback, and deliver final logos in all necessary formats and variations. Our logos are versatile, scalable, and designed to work across all applications from business cards to billboards. We provide complete usage guidelines, color specifications, and file formats optimized for print, web, and social media. A well-designed logo becomes the cornerstone of your brand identity, building recognition and trust with audiences while communicating professionalism and credibility.""", 'duration': 25, 'categories': 'Design,Marketing'},
                {'title': 'Graphic Design', 'description': """Bring your visual communications to life with professional graphic design services that combine creativity, strategy, and technical expertise. Our talented designers create compelling visuals for marketing materials, presentations, social media, websites, and more. We handle projects of all sizes from single-asset creation to comprehensive design systems, always maintaining focus on your brand guidelines and communication objectives. Our design process emphasizes collaboration, with multiple revision rounds to ensure complete satisfaction. We deliver print-ready and web-optimized files in appropriate formats, along with source files for future modifications. Whether you need eye-catching advertisements, informative infographics, or cohesive marketing collateral, our design services help you communicate effectively and stand out in crowded markets.""", 'duration': 35, 'categories': 'Design'},
                {'title': 'UX/UI Design', 'description': """Transform digital experiences with user-centered UX/UI design that balances aesthetics, usability, and business goals. Our design process includes user research, persona development, journey mapping, information architecture, wireframing, and high-fidelity interface design. We create intuitive navigation structures, optimize interaction patterns, and design visually appealing interfaces that guide users toward desired actions. Our designs are responsive, accessible, and tested with real users to validate effectiveness. We provide detailed design specifications, interactive prototypes, and design systems that ensure consistency across your digital products. By focusing on user needs while meeting business objectives, we create engaging experiences that increase satisfaction, reduce friction, and drive conversions across websites, mobile apps, and software applications.""", 'duration': 60, 'categories': 'Design,Development'},
                {'title': 'Brand Identity', 'description': """Establish a cohesive, memorable brand presence with comprehensive identity systems that work seamlessly across all touchpoints. Our brand identity development goes beyond logo design to create complete visual languages including typography, color systems, imagery styles, iconography, and application templates. We develop thorough brand guidelines documenting proper usage, providing examples, and ensuring consistency across all materials. Our process includes stakeholder interviews, market research, positioning strategy, and iterative design development. Deliverables include primary and secondary logos, brand patterns, marketing templates, digital assets, and comprehensive style guides. We ensure your brand identity authentically represents your values, resonates with target audiences, differentiates from competitors, and scales effectively as your organization grows.""", 'duration': 90, 'categories': 'Design,Marketing,Consulting'},
                {'title': 'Print Design', 'description': """Make powerful impressions with professionally designed print materials that communicate your message effectively and reflect your brand quality. We create brochures, flyers, business cards, posters, catalogs, and other print collateral with careful attention to typography, layout, color, and paper selection. Our designers understand print production requirements, ensuring designs translate beautifully from screen to paper while meeting technical specifications for commercial printing. We provide print-ready PDF files with proper bleeds, color modes, and resolution, along with printer coordination if needed. Whether you need elegant business stationery, impactful event materials, or informative product catalogs, our print design services deliver tangible marketing tools that engage audiences and leave lasting impressions.""", 'duration': 20, 'categories': 'Design'},
            ],
            # Legal Associates
            [
                {'title': 'Contract Review', 'description': """Protect your interests with thorough contract review services that identify risks, clarify ambiguities, and ensure favorable terms. Our experienced attorneys analyze agreements of all types including vendor contracts, employment agreements, partnership documents, licensing arrangements, and service agreements. We examine contractual obligations, termination clauses, liability provisions, dispute resolution mechanisms, and intellectual property rights. You'll receive detailed analysis highlighting problematic provisions, suggesting modifications, and explaining legal implications in plain language. We also provide negotiation support to achieve more favorable terms. Whether reviewing contracts before signing or analyzing existing agreements for renegotiation, our service helps you avoid costly disputes, understand obligations fully, and enter agreements with confidence and clarity.""", 'duration': 45, 'categories': 'Legal,Consulting'},
                {'title': 'Compliance Audit', 'description': """Ensure regulatory compliance and identify potential liabilities with comprehensive compliance audits conducted by experienced legal professionals. We assess your organization's adherence to applicable laws, regulations, and industry standards across areas including employment law, data privacy, environmental regulations, financial reporting, and sector-specific requirements. Our audits include policy review, procedure assessment, documentation examination, and employee interviews. We identify compliance gaps, assess risk levels, and provide prioritized remediation recommendations with practical implementation guidance. Our detailed reports document findings, explain regulatory requirements, and outline corrective actions. Regular compliance audits demonstrate due diligence, reduce legal exposure, avoid penalties, and provide peace of mind that your organization operates within legal boundaries while maintaining ethical standards.""", 'duration': 50, 'categories': 'Legal,Consulting'},
                {'title': 'Legal Consultation', 'description': """Access expert legal guidance on diverse business and legal matters through our comprehensive consultation services. Our attorneys provide advice on business formation, contract negotiations, employment matters, intellectual property protection, regulatory compliance, risk management, and dispute avoidance. We take time to understand your specific circumstances, explain legal concepts clearly, outline options with pros and cons, and recommend practical courses of action. Consultations can be one-time sessions for specific issues or ongoing advisory relationships for continuous support. We help you make informed decisions, avoid legal pitfalls, and navigate complex legal landscapes confidently. Whether facing immediate legal questions or seeking proactive guidance to prevent future issues, our consultation services provide accessible, practical legal expertise tailored to your needs.""", 'duration': 30, 'categories': 'Legal,Consulting'},
                {'title': 'Document Preparation', 'description': """Obtain professionally drafted legal documents that protect your interests and comply with applicable laws. We prepare a wide range of legal documents including contracts, agreements, policies, terms of service, privacy policies, employment documents, operating agreements, and corporate resolutions. Our attorneys ensure documents are comprehensive, legally sound, and tailored to your specific requirements. We use clear language while maintaining legal precision, address relevant legal issues, and include necessary protective provisions. All documents comply with current laws and regulations in your jurisdiction. We provide explanations of key terms and provisions, offer revision opportunities, and deliver final documents in editable formats. Properly prepared legal documents prevent misunderstandings, protect rights, and establish clear frameworks for business relationships and operations.""", 'duration': 35, 'categories': 'Legal'},
                {'title': 'Dispute Resolution', 'description': """Resolve conflicts efficiently and cost-effectively through professional mediation and alternative dispute resolution services. Our experienced mediators facilitate productive discussions between parties, helping identify common ground, explore creative solutions, and reach mutually acceptable agreements. We handle business disputes, contract disagreements, partnership conflicts, employment matters, and vendor disputes. Mediation often resolves issues faster and more affordably than litigation while preserving business relationships. Our neutral mediators create safe environments for open dialogue, manage emotions, clarify misunderstandings, and guide parties toward win-win outcomes. We provide conflict analysis, facilitation services, and settlement documentation. When conflicts arise, our dispute resolution services offer practical alternatives to costly litigation, helping you find resolutions that work for all parties while maintaining confidentiality and control over outcomes.""", 'duration': 120, 'categories': 'Legal,Consulting'},
            ],
            # HR Consulting
            [
                {'title': 'Recruitment Services', 'description': """Attract and hire top talent with comprehensive recruitment services that streamline your hiring process and improve candidate quality. We handle everything from job description development and sourcing strategy through candidate screening, interviewing, and offer negotiation. Our recruiters leverage extensive networks, utilize modern sourcing techniques, and conduct thorough assessments to identify candidates who match both skills requirements and cultural fit. We manage applicant tracking, coordinate interview schedules, conduct reference checks, and facilitate hiring decisions. Our process includes employer branding guidance, candidate experience optimization, and diversity recruitment strategies. Whether you need to fill individual positions or build entire teams, our recruitment services deliver qualified candidates efficiently while providing positive experiences that enhance your employer reputation and support long-term talent acquisition success.""", 'duration': 100, 'categories': 'HR,Consulting'},
                {'title': 'HR Strategy', 'description': """Develop human resources strategies that align with business objectives and support organizational success. Our HR consultants work with leadership to assess current HR capabilities, identify gaps, and design comprehensive strategies covering talent management, organizational development, compensation and benefits, employee engagement, and succession planning. We analyze workforce data, benchmark against industry standards, and consider future business needs to create actionable roadmaps. Our strategic planning process includes stakeholder input, scenario analysis, and implementation timelines. We provide guidance on HR technology investments, organizational structure optimization, and culture development initiatives. Whether undergoing rapid growth, restructuring, or seeking to enhance HR effectiveness, our strategic consulting helps you build HR functions that attract, develop, and retain talent while supporting business goals and creating competitive advantages.""", 'duration': 40, 'categories': 'HR,Consulting'},
                {'title': 'Training Programs', 'description': """Develop employee capabilities and drive performance improvements with customized training programs addressing your specific organizational needs. We design and deliver training on leadership development, technical skills, communication, customer service, compliance, safety, and soft skills. Our instructional designers assess learning needs, develop engaging curriculum, create training materials, and utilize varied delivery methods including instructor-led training, e-learning modules, workshops, and on-the-job training. We incorporate adult learning principles, interactive elements, and practical applications to maximize knowledge retention and behavior change. Training programs include pre and post assessments, participant feedback collection, and effectiveness measurement. Invest in your workforce development with training solutions that build skills, increase productivity, improve employee satisfaction, and support career progression while addressing organizational performance goals.""", 'duration': 80, 'categories': 'HR'},
                {'title': 'Compliance Support', 'description': """Navigate complex employment laws and regulations with expert compliance support that protects your organization from legal risks. Our HR compliance specialists stay current with federal, state, and local employment laws covering wage and hour rules, anti-discrimination provisions, leave requirements, safety regulations, and recordkeeping obligations. We conduct compliance audits, review policies and procedures, provide regulatory updates, and offer guidance on specific situations. Our services include employee handbook development, manager training on compliance issues, investigation support, and accommodation guidance. We help you establish compliant practices, maintain required documentation, and respond appropriately to regulatory inquiries. Proactive compliance support reduces legal exposure, avoids penalties, and creates fair, consistent workplace practices that protect both employees and the organization.""", 'duration': 35, 'categories': 'HR,Legal,Consulting'},
                {'title': 'Performance Management', 'description': """Enhance organizational performance with effective performance management systems and coaching services. We design comprehensive performance management processes including goal setting frameworks, continuous feedback mechanisms, formal review procedures, and development planning. Our consultants help implement modern performance management approaches that emphasize ongoing dialogue, growth mindset, and clear performance expectations. We train managers on effective feedback delivery, difficult conversation navigation, and performance improvement planning. Our coaching services support leaders in developing their teams, addressing performance issues, and recognizing achievements. We also design compensation linkages, succession planning integration, and metrics for measuring system effectiveness. Strong performance management drives engagement, improves productivity, supports talent development, and ensures accountability while fostering positive manager-employee relationships and organizational success.""", 'duration': 60, 'categories': 'HR,Consulting'},
            ],
            # Design Factory
            [
                {'title': 'Web Design', 'description': """Create stunning, user-friendly websites with modern, responsive design that works flawlessly across all devices and browsers. Our web designers combine aesthetic excellence with usability principles to create engaging online experiences that reflect your brand and achieve your goals. We conduct user research, develop information architectures, create wireframes, and design high-fidelity mockups with attention to typography, color, spacing, and visual hierarchy. Our designs are responsive, accessible, and optimized for performance. We consider SEO best practices, implement conversion optimization techniques, and ensure designs are technically feasible. Deliverables include design files, style guides, and developer handoff documentation. Whether creating new websites or redesigning existing ones, our web design services produce beautiful, functional sites that engage visitors and drive results.""", 'duration': 75, 'categories': 'Design,Development'},
                {'title': 'UI Component Library', 'description': """Accelerate development and ensure design consistency with comprehensive UI component libraries containing reusable, well-documented interface elements. We design and document complete sets of buttons, forms, cards, navigation elements, modals, and other components following atomic design principles. Each component includes multiple states, variants, usage guidelines, and accessibility considerations. We create component specifications with detailed measurements, behaviors, and interaction patterns. Our libraries are designed for flexibility and scalability, supporting your product's current needs while accommodating future growth. We deliver component libraries in design tools like Figma or Sketch along with implementation-ready specifications. Component libraries reduce design and development time, maintain visual consistency, streamline collaboration, and provide solid foundations for scalable digital products.""", 'duration': 55, 'categories': 'Design,Development'},
                {'title': 'Wireframing', 'description': """Establish solid structural foundations for digital products with professional wireframing services that focus on functionality, content hierarchy, and user flow. We create low and mid-fidelity wireframes that communicate layout structures, navigation patterns, content placement, and interaction logic without visual design details. Our wireframing process emphasizes user needs, information architecture, and conversion goals. We iterate quickly based on feedback, test concepts with users, and refine structures before investing in visual design. Wireframes facilitate stakeholder alignment, identify usability issues early, and serve as blueprints for designers and developers. Whether designing websites, mobile apps, or software interfaces, wireframing ensures strong foundational structures that support effective user experiences and successful products.""", 'duration': 20, 'categories': 'Design'},
                {'title': 'Prototyping', 'description': """Validate concepts and test user experiences with interactive prototypes that simulate final product functionality. We create clickable prototypes ranging from simple navigation flows to high-fidelity interactive experiences with animations, transitions, and realistic interactions. Prototypes allow stakeholders to experience designs before development, identify issues, gather user feedback, and make informed decisions. We use industry-leading prototyping tools to create realistic simulations that communicate design intent clearly. Our prototyping process includes user testing, iteration based on feedback, and detailed documentation of interactions. Prototypes reduce development risks, facilitate better communication among teams, validate assumptions, and ensure final products meet user needs and business goals effectively.""", 'duration': 40, 'categories': 'Design,Development'},
                {'title': 'Design System', 'description': """Build scalable, consistent digital products with comprehensive design systems that unify design and development processes. We create complete design systems including component libraries, design tokens, patterns, guidelines, and governance models. Our process involves auditing existing interfaces, establishing design principles, defining visual language systems, creating reusable components, and documenting usage guidelines. Design systems include accessibility standards, responsive behaviors, content guidelines, and contribution processes. We deliver design system documentation, component libraries in design tools and code, and training for teams. Effective design systems improve collaboration, maintain consistency across products, accelerate development, reduce design debt, and create cohesive user experiences that scale efficiently as organizations grow.""", 'duration': 100, 'categories': 'Design,Development,Consulting'},
            ],
            # Development Labs
            [
                {'title': 'Mobile App Development', 'description': """Bring your ideas to life with professional mobile app development for iOS and Android platforms. Our experienced developers create native and cross-platform applications using technologies like Swift, Kotlin, React Native, and Flutter. We handle the complete development lifecycle from concept and design through development, testing, and App Store submission. Our apps feature intuitive interfaces, smooth performance, offline capabilities, push notifications, and seamless backend integration. We follow platform-specific design guidelines, implement security best practices, and optimize for various device sizes and OS versions. Development includes comprehensive testing, performance optimization, and post-launch support. Whether building consumer apps, enterprise solutions, or mvp prototypes, our mobile development services deliver high-quality applications that engage users and achieve your business objectives.""", 'duration': 120, 'categories': 'Development,IT'},
                {'title': 'API Development', 'description': """Enable seamless system integration and data exchange with robust, well-documented APIs designed for reliability and ease of use. We develop RESTful and GraphQL APIs that follow industry best practices for authentication, versioning, error handling, and documentation. Our APIs feature efficient data structures, proper HTTP methods, comprehensive error responses, and security measures including authentication, rate limiting, and input validation. We implement proper API documentation using tools like Swagger or Postman, provide example requests, and create developer-friendly integration guides. Our development includes thorough testing, performance optimization, and monitoring setup. Whether building public APIs, internal service integrations, or third-party connections, we deliver APIs that enable powerful integrations while maintaining security, reliability, and excellent developer experiences.""", 'duration': 50, 'categories': 'Development,IT'},
                {'title': 'Backend Development', 'description': """Power your applications with robust backend systems built for performance, scalability, and security. Our backend developers create server-side solutions using modern technologies like Node.js, Python, Java, and .NET. We design database schemas, implement business logic, create APIs, handle authentication and authorization, and integrate third-party services. Our architectures emphasize modularity, testability, and maintainability. We implement caching strategies, optimize database queries, handle asynchronous processing, and establish monitoring and logging. Security is paramount with proper input validation, SQL injection prevention, secure authentication, and data encryption. Whether building new backends or enhancing existing systems, we deliver reliable server-side solutions that support your application functionality, handle growth, and maintain performance under load.""", 'duration': 90, 'categories': 'Development,IT'},
                {'title': 'DevOps Setup', 'description': """Streamline development and deployment with comprehensive DevOps practices and automation. We implement CI/CD pipelines using tools like Jenkins, GitLab CI, GitHub Actions, or CircleCI to automate testing, building, and deployment processes. Our DevOps setup includes containerization with Docker, orchestration with Kubernetes, infrastructure as code using Terraform or CloudFormation, and monitoring with tools like Prometheus and Grafana. We establish automated testing frameworks, implement deployment strategies like blue-green or canary deployments, and configure proper logging and alerting. Our approach reduces manual errors, accelerates release cycles, improves collaboration between teams, and enables rapid recovery from issues. Proper DevOps practices increase deployment frequency, reduce failure rates, and improve overall software delivery performance.""", 'duration': 40, 'categories': 'Development,IT,Operations'},
                {'title': 'Code Review', 'description': """Improve code quality and team knowledge with expert code review services that identify issues and share best practices. Our experienced developers conduct thorough reviews examining code architecture, logic, security, performance, maintainability, and adherence to coding standards. We identify bugs, security vulnerabilities, performance bottlenecks, and technical debt while suggesting improvements and alternative approaches. Reviews include constructive feedback, explanations of issues, and recommendations following industry best practices. We assess test coverage, documentation quality, and code organization. Code reviews catch issues before production, facilitate knowledge sharing, maintain code quality standards, and help teams improve their development skills. Whether conducting one-time reviews or establishing ongoing review processes, we help you build better, more maintainable software.""", 'duration': 25, 'categories': 'Development,IT'},
            ],
            # Company 9: Business Strategy
            [
                {'title': 'Strategic Planning', 'description': """Define clear direction and achieve ambitious goals with comprehensive strategic planning services. We facilitate structured planning processes that assess your current position, define vision and mission, establish strategic objectives, and create actionable implementation roadmaps. Our approach includes environmental scanning, SWOT analysis, competitive positioning, and stakeholder engagement. We help leadership teams make difficult choices about priorities, resource allocation, and competitive differentiation. Planning sessions produce documented strategies with clear goals, metrics, responsibilities, and timelines. We facilitate alignment across leadership, identify potential obstacles, and establish monitoring frameworks. Whether developing three-year strategic plans or addressing specific strategic challenges, our planning services provide clarity, focus, and actionable direction that guide organizational decisions and drive sustainable growth.""", 'duration': 60, 'categories': 'Consulting'},
                {'title': 'Market Analysis', 'description': """Make informed strategic decisions with comprehensive market research and competitive analysis services. We conduct primary and secondary research to understand market size, growth trends, customer segments, buying behaviors, and emerging opportunities. Our competitive analysis examines competitor strategies, positioning, strengths, weaknesses, and market share. We analyze industry dynamics, identify market gaps, assess threats and opportunities, and benchmark your performance. Deliverables include detailed reports with data visualizations, strategic insights, and actionable recommendations. Our analysis helps you understand market realities, identify growth opportunities, refine positioning, and develop strategies that leverage your strengths against competitive weaknesses. Whether entering new markets or strengthening existing positions, our market analysis provides the insights needed for strategic success.""", 'duration': 45, 'categories': 'Consulting,Marketing'},
                {'title': 'Business Transformation', 'description': """Navigate major organizational change successfully with comprehensive transformation services covering strategy, process, technology, and culture. We help organizations reimagine business models, restructure operations, implement new technologies, and transform cultures. Our transformation approach includes current state assessment, future state visioning, gap analysis, roadmap development, and change management. We address the people side of change through communication planning, stakeholder engagement, training programs, and resistance management. Our consultants provide program management, ensure cross-functional coordination, track progress, and adjust approaches based on feedback. Whether undergoing digital transformation, restructuring operations, or pursuing new strategic directions, we guide you through complex change while minimizing disruption, maintaining momentum, and achieving sustainable transformation results.""", 'duration': 150, 'categories': 'Consulting,Operations'},
                {'title': 'Process Improvement', 'description': """Enhance operational efficiency and effectiveness with systematic process improvement services that eliminate waste and optimize workflows. We analyze current processes through observation, data collection, and stakeholder interviews to identify bottlenecks, redundancies, and improvement opportunities. Using methodologies like Lean, Six Sigma, and process mapping, we redesign workflows to improve speed, quality, and cost-effectiveness. Our approach includes process documentation, standard operating procedure development, performance metrics establishment, and continuous improvement frameworks. We facilitate implementation, provide change management support, and train staff on new processes. Process improvement initiatives reduce cycle times, lower costs, improve quality, and enhance customer satisfaction while empowering teams to continuously identify and implement improvements.""", 'duration': 70, 'categories': 'Consulting,Operations'},
                {'title': 'Leadership Coaching', 'description': """Develop exceptional leaders through personalized coaching that enhances skills, addresses challenges, and accelerates professional growth. Our experienced executive coaches work one-on-one with leaders to improve communication, decision-making, strategic thinking, team development, and emotional intelligence. Coaching engagements begin with assessments and goal-setting, followed by regular sessions exploring challenges, providing feedback, and practicing new approaches. We use proven coaching methodologies, maintain strict confidentiality, and focus on actionable development. Coaching addresses specific situations like role transitions, conflict management, or executive presence while building long-term leadership capabilities. Whether developing emerging leaders or enhancing executive effectiveness, our coaching services unlock leadership potential, improve organizational performance, and support career progression through personalized, results-focused development.""", 'duration': 50, 'categories': 'Consulting,HR'},
            ],
            # Company 10: Data Analytics Pro
            [
                {'title': 'Data Visualization', 'description': """Transform complex data into compelling visual stories with interactive dashboards and reports that drive understanding and action. Our data visualization experts design and build custom dashboards using tools like Tableau, Power BI, or custom web-based solutions. We apply data visualization best practices, choosing appropriate chart types, designing effective color schemes, and creating intuitive navigation. Our dashboards connect to various data sources, update in real-time, and provide drill-down capabilities for deeper analysis. We focus on the metrics that matter most to your business, presenting information clearly for different audiences from executives to analysts. Effective data visualization makes insights accessible, facilitates data-driven decision making, reveals patterns and trends, and enables stakeholders to monitor performance and identify opportunities at a glance.""", 'duration': 45, 'categories': 'IT,Consulting'},
                {'title': 'Business Intelligence', 'description': """Unlock the power of your data with comprehensive business intelligence strategy and implementation services. We assess your current analytics capabilities, identify business intelligence needs, and design BI architectures that turn data into actionable insights. Our services include data warehouse design, ETL pipeline development, reporting framework creation, and analytics tool implementation. We integrate data from multiple sources, establish data governance, create standardized metrics, and build self-service analytics capabilities. Our BI solutions provide executives with strategic insights, managers with operational metrics, and analysts with exploration tools. We train users, establish best practices, and ensure sustainable adoption. Effective business intelligence improves decision quality, reveals hidden opportunities, optimizes operations, and provides competitive advantages through better understanding of business performance and market dynamics.""", 'duration': 80, 'categories': 'IT,Consulting'},
                {'title': 'Predictive Analytics', 'description': """Anticipate future trends and outcomes with advanced predictive analytics leveraging machine learning and statistical modeling. Our data scientists build predictive models for customer churn, demand forecasting, risk assessment, fraud detection, and more. We handle the complete analytics lifecycle from data collection and preparation through model development, validation, and deployment. Our models use algorithms including regression, classification, clustering, and neural networks, selected based on your specific use cases. We explain model predictions, measure accuracy, and monitor performance over time. Predictive analytics provides foresight for proactive decision-making, optimizes resource allocation, identifies high-value opportunities, and mitigates risks. Whether predicting customer behavior, forecasting sales, or assessing credit risk, our predictive analytics services turn historical data into future insights that drive competitive advantages.""", 'duration': 100, 'categories': 'IT,Development'},
                {'title': 'Data Migration', 'description': """Execute safe, successful data migrations between systems with comprehensive planning and execution services that preserve data integrity and minimize disruption. We manage migrations from legacy systems to modern platforms, between cloud providers, or during system consolidations. Our process includes data assessment, mapping strategy development, migration tool selection, testing protocols, and rollback procedures. We validate data accuracy, maintain audit trails, handle data transformations, and coordinate timing to minimize downtime. Our team addresses data quality issues, resolves conflicts, and ensures compliance with data regulations. We provide post-migration validation, reconciliation reports, and support. Whether migrating databases, applications, or entire data centers, our methodical approach ensures your valuable data transfers completely, accurately, and securely to new systems.""", 'duration': 60, 'categories': 'IT,Operations'},
                {'title': 'Analytics Training', 'description': """Empower your team to leverage data effectively with comprehensive training programs on analytics tools and techniques. We provide customized training on platforms like Excel, SQL, Tableau, Power BI, Python for data analysis, and statistical methods. Our training programs include hands-on exercises, real-world examples using your data, and reference materials for ongoing learning. We adapt content to different skill levels from beginners learning foundational concepts to advanced users seeking specialized techniques. Training covers data preparation, analysis methods, visualization best practices, and critical thinking about data. We offer in-person workshops, virtual sessions, and self-paced materials. Analytics training builds organizational data literacy, enables self-service analytics, reduces dependence on specialists, and fosters data-driven culture where teams confidently use data to inform decisions and drive improvements.""", 'duration': 30, 'categories': 'IT,HR'},
            ],
            # Company 11: Content Creators Hub
            [
                {'title': 'Blog Writing', 'description': """Build authority and attract audiences with professionally crafted blog posts and articles that inform, engage, and drive action. Our experienced writers create well-researched, original content optimized for both readers and search engines. We develop content strategies aligned with your business goals, identify relevant topics, conduct keyword research, and write compelling articles in your brand voice. Our blog posts feature clear structure, engaging introductions, valuable insights, practical takeaways, and effective calls to action. Content is SEO-optimized with proper heading structure, meta descriptions, and internal linking. We handle everything from topic ideation through final editing, delivering publication-ready content. Regular blog publishing establishes thought leadership, improves search rankings, attracts qualified traffic, and nurtures prospects through valuable information that builds trust and authority.""", 'duration': 20, 'categories': 'Marketing'},
                {'title': 'Copywriting', 'description': """Convert prospects into customers with persuasive copy that communicates value and motivates action. Our professional copywriters craft compelling messaging for websites, landing pages, advertisements, brochures, product descriptions, and other marketing materials. We research your audience, understand their pain points and motivations, and write copy that resonates emotionally while highlighting benefits clearly. Our copy follows proven frameworks, uses active voice, maintains appropriate tone, and includes strong calls to action. We write headlines that grab attention, body copy that builds interest and desire, and closes that drive conversions. Whether you need punchy ad copy, detailed product descriptions, or conversion-optimized landing page content, our copywriting services deliver messages that engage audiences and achieve marketing objectives.""", 'duration': 15, 'categories': 'Marketing,Sales'},
                {'title': 'Email Campaigns', 'description': """Engage subscribers and drive conversions with strategically crafted email marketing content that cuts through inbox clutter. We create complete email campaigns including welcome series, promotional emails, newsletters, abandoned cart sequences, and re-engagement campaigns. Our email content features attention-grabbing subject lines, personalized messaging, clear value propositions, compelling visuals, and strong calls to action. We optimize for mobile devices, follow email best practices, and ensure compliance with regulations. Our campaigns incorporate segmentation strategies, A/B testing recommendations, and timing optimization. We write content that builds relationships, nurtures leads, promotes products, and drives repeat business. Effective email marketing delivers high ROI, maintains customer relationships, drives website traffic, and generates sales through targeted, relevant messages delivered directly to engaged audiences.""", 'duration': 25, 'categories': 'Marketing'},
                {'title': 'Social Media Content', 'description': """Capture attention and drive engagement with compelling social media content tailored to each platform's unique characteristics and audience expectations. We create posts for Facebook, Instagram, LinkedIn, Twitter, TikTok, and other platforms that align with your brand voice and marketing goals. Our content includes eye-catching visuals or videos, engaging captions with appropriate hashtags, and clear calls to action. We develop content calendars, balance promotional and value-adding posts, and adapt messaging for different platforms and audience segments. Our social media content sparks conversations, encourages sharing, builds community, and drives traffic to your website. Whether you need daily posts, campaign content, or community management support, our social media content services help you build meaningful connections with audiences and achieve social marketing objectives.""", 'duration': 30, 'categories': 'Marketing'},
                {'title': 'Video Scripts', 'description': """Tell compelling visual stories with professionally written video scripts that engage viewers and communicate messages effectively. We write scripts for explainer videos, promotional content, product demonstrations, testimonials, social media videos, and educational content. Our scriptwriting process includes concept development, research, storytelling structure, dialogue writing, and visual direction notes. We write for your target audience, maintain appropriate tone and pacing, incorporate storytelling techniques, and include clear calls to action. Scripts are formatted for easy production with scene descriptions, speaker notes, and timing considerations. We collaborate with video producers to ensure scripts work visually and align with production capabilities. Well-written video scripts ensure your video content engages viewers, communicates clearly, and achieves marketing or educational objectives efficiently.""", 'duration': 18, 'categories': 'Marketing'},
            ],
            # Company 12: Sales Excellence
            [
                {'title': 'Sales Training', 'description': """Transform your sales team's performance with comprehensive training programs covering essential skills, modern techniques, and winning mindsets. Our sales training addresses prospecting strategies, qualification methods, needs discovery, solution positioning, objection handling, closing techniques, and relationship building. We use role-playing exercises, real-world scenarios, and practical frameworks that participants can apply immediately. Training is customized to your industry, sales cycle, and specific challenges. We cover both foundational skills for new sellers and advanced techniques for experienced representatives. Our programs include pre and post assessments, ongoing reinforcement, and coaching support. Sales training increases win rates, shortens sales cycles, improves average deal sizes, and builds confidence. Invest in your sales team's development to drive revenue growth and competitive advantage.""", 'duration': 50, 'categories': 'Sales,HR'},
                {'title': 'Lead Generation', 'description': """Fill your pipeline with qualified prospects through strategic B2B lead generation services that identify and engage potential customers. We develop multi-channel lead generation strategies incorporating content marketing, email outreach, social selling, paid advertising, and account-based marketing tactics. Our process includes ideal customer profile development, prospect identification, contact information verification, messaging creation, and multi-touch outreach sequences. We qualify leads based on your criteria, warm prospects through value-adding interactions, and schedule appointments with your sales team. Our lead generation services provide consistent flow of qualified opportunities, allowing sales teams to focus on closing rather than prospecting. Whether you need to enter new markets, expand within existing accounts, or consistently fill your pipeline, our lead generation delivers results that drive revenue growth.""", 'duration': 70, 'categories': 'Sales,Marketing'},
                {'title': 'Sales Process Optimization', 'description': """Increase sales efficiency and effectiveness by optimizing your sales process from initial contact through closed deals. We analyze your current sales pipeline, identify bottlenecks and inefficiencies, and redesign processes to improve conversion rates and shorten sales cycles. Our optimization includes stage definitions, qualification criteria, required activities, content and tools for each stage, and handoff protocols. We implement sales methodologies appropriate to your business, establish metrics and reporting, and create playbooks documenting best practices. Our approach balances structure with flexibility, ensuring processes support rather than constrain sellers. Sales process optimization improves forecasting accuracy, increases win rates, reduces sales cycle length, and enables scalable growth. Transform your sales operation from ad-hoc approaches to predictable, repeatable processes that consistently drive revenue.""", 'duration': 45, 'categories': 'Sales,Consulting'},
                {'title': 'CRM Implementation', 'description': """Maximize sales productivity and visibility with comprehensive CRM implementation services covering system setup, customization, integration, and user adoption. We help you select appropriate CRM platforms, configure systems to match your sales process, customize fields and workflows, set up automation, and integrate with existing tools. Our implementation includes data migration, report and dashboard creation, user permission configuration, and comprehensive training. We establish data quality standards, create user adoption strategies, and provide ongoing support. A well-implemented CRM provides visibility into pipeline health, automates administrative tasks, enables better forecasting, improves collaboration, and provides insights that drive strategic decisions. Whether implementing new CRM systems or optimizing existing ones, we ensure technology enhances rather than hinders sales performance.""", 'duration': 60, 'categories': 'Sales,IT'},
                {'title': 'Negotiation Coaching', 'description': """Master the art of negotiation with advanced coaching that improves outcomes while preserving relationships. Our negotiation coaching covers preparation strategies, opening techniques, value communication, concession management, objection handling, and closing tactics. We teach principled negotiation approaches that seek win-win outcomes rather than adversarial tactics. Coaching includes preparation frameworks for analyzing negotiation dynamics, identifying leverage points, and developing strategic approaches. We use role-playing exercises to practice techniques in safe environments before high-stakes negotiations. Our coaching addresses both transactional negotiations and complex, multi-party situations. Effective negotiation skills increase deal profitability, preserve margins, build customer relationships, and create agreements that both parties enthusiastically support. Develop negotiation mastery that drives better business outcomes consistently.""", 'duration': 35, 'categories': 'Sales,Consulting'},
            ],
            # Company 13: Event Planning Co
            [
                {'title': 'Corporate Events', 'description': """Create memorable corporate events that achieve business objectives while providing exceptional attendee experiences. Our full-service event planning covers everything from initial concept development through post-event follow-up. We handle venue selection and negotiation, catering coordination, audiovisual arrangements, entertainment booking, registration management, and on-site coordination. Our planners understand corporate culture and business goals, ensuring events align with organizational objectives whether celebrating milestones, launching products, or building relationships. We manage budgets carefully, handle logistics meticulously, and prepare contingency plans. Our attention to detail and vendor relationships ensure smooth execution. From intimate executive dinners to large-scale company celebrations, we deliver professional events that reflect well on your organization, engage participants, and achieve desired outcomes.""", 'duration': 120, 'categories': 'Operations'},
                {'title': 'Conference Management', 'description': """Execute successful conferences with comprehensive end-to-end organization services that handle every detail. We manage all conference aspects including venue sourcing, speaker recruitment and coordination, agenda development, registration systems, sponsorship programs, exhibition management, audiovisual production, and attendee engagement. Our conference management includes website development, mobile app setup, marketing support, and post-event analytics. We coordinate multiple tracks, manage speaker logistics, facilitate networking opportunities, and ensure seamless technical execution. Our team handles crisis management and adapts to last-minute changes while maintaining professional standards. Whether organizing industry conferences, internal company events, or educational symposiums, we deliver well-orchestrated conferences that provide value to attendees, meet sponsor expectations, and achieve organizational goals.""", 'duration': 150, 'categories': 'Operations,Marketing'},
                {'title': 'Team Building Activities', 'description': """Strengthen teams and boost morale with engaging team building events designed to improve collaboration, communication, and relationships. We design customized activities that align with your team goals whether building trust, improving communication, celebrating achievements, or simply having fun together. Our offerings range from indoor workshops and problem-solving challenges to outdoor adventures and competitive games. Activities are facilitated by professionals who create inclusive environments where all participants contribute. We handle all logistics including venue arrangements, equipment, catering, and transportation. Team building activities break down silos, reveal individual strengths, create shared experiences, and energize teams. Whether you need brief energizers or day-long retreats, our team building services create memorable experiences that strengthen workplace relationships and improve team effectiveness.""", 'duration': 40, 'categories': 'HR,Operations'},
                {'title': 'Virtual Events', 'description': """Engage remote audiences with professionally produced virtual events that deliver impactful experiences regardless of physical location. We handle all aspects of online event production including platform selection and setup, registration management, speaker coaching, technical production, audience engagement features, and post-event analytics. Our virtual events incorporate interactive elements like polls, Q&A sessions, breakout rooms, and networking opportunities that maintain engagement. We provide technical support for presenters and attendees, manage live streaming, and handle recording for on-demand access. Our production quality ensures professional presentations with good audio, video, and connectivity. Whether hosting webinars, virtual conferences, or hybrid events, we leverage technology effectively to create engaging experiences that achieve communication and business objectives.""", 'duration': 50, 'categories': 'IT,Operations'},
                {'title': 'Event Marketing', 'description': """Maximize event attendance and engagement with comprehensive marketing strategies that build awareness, generate registrations, and create buzz. Our event marketing services include promotional strategy development, marketing materials creation, email campaign execution, social media promotion, content marketing, paid advertising, and PR outreach. We develop compelling messaging that communicates event value, create landing pages optimized for conversions, and implement multi-channel promotion campaigns. Our strategies include early-bird promotions, referral incentives, and remarketing tactics. We track campaign performance, optimize based on results, and provide registration analytics. Effective event marketing fills seats, attracts the right attendees, builds anticipation, and extends event impact beyond the actual date through content promotion and follow-up communications.""", 'duration': 35, 'categories': 'Marketing'},
            ],
            # Company 14: Supply Chain Solutions
            [
                {'title': 'Logistics Optimization', 'description': """Transform logistics operations to reduce costs, improve delivery performance, and enhance customer satisfaction. We analyze your current logistics network including transportation modes, routes, carrier relationships, and distribution strategies to identify optimization opportunities. Our services include network design, route optimization, carrier selection and negotiation, warehouse location analysis, and technology implementation. We use data analytics and modeling to simulate scenarios and recommend improvements. Our optimization addresses inbound and outbound logistics, returns management, and last-mile delivery challenges. We implement tracking systems, establish performance metrics, and create continuous improvement processes. Logistics optimization reduces transportation costs, shortens delivery times, improves on-time performance, and increases supply chain visibility. Whether managing domestic or international logistics, we help you build efficient, reliable logistics operations that support business growth.""", 'duration': 65, 'categories': 'Operations,Consulting'},
                {'title': 'Inventory Management', 'description': """Achieve optimal inventory levels that balance service levels with carrying costs through efficient inventory control systems and practices. We implement inventory management strategies including ABC analysis, safety stock calculations, reorder point optimization, and demand forecasting. Our services include system selection and implementation, policy development, process design, and team training. We establish inventory metrics, implement cycle counting programs, and create inventory visibility across locations. Our approach considers lead times, demand variability, service level requirements, and carrying costs to determine optimal inventory policies. Effective inventory management reduces stockouts and excess inventory, improves cash flow, decreases obsolescence, and enhances customer service. Whether managing retail inventory, raw materials, or finished goods, we help you implement systems and practices that optimize inventory investment while meeting customer demands.""", 'duration': 55, 'categories': 'Operations'},
                {'title': 'Vendor Management', 'description': """Build strong supplier relationships and optimize procurement performance through strategic vendor management services. We help you develop vendor evaluation criteria, conduct supplier assessments, negotiate contracts, establish performance metrics, and implement vendor scorecards. Our services include vendor rationalization, relationship development, risk assessment, and continuous improvement programs. We facilitate regular business reviews, address performance issues, and identify collaboration opportunities. Our approach balances cost management with quality, reliability, and innovation. We help establish governance structures, create escalation procedures, and develop contingency plans for supply disruptions. Effective vendor management reduces costs, improves quality and delivery performance, mitigates supply chain risks, and builds partnerships that drive mutual success. Transform vendors from transactional suppliers into strategic partners contributing to your competitive advantage.""", 'duration': 45, 'categories': 'Operations,Consulting'},
                {'title': 'Supply Chain Analysis', 'description': """Gain comprehensive understanding of supply chain performance and identify improvement opportunities through thorough supply chain audits and analysis. We examine all supply chain aspects including planning processes, procurement practices, production operations, logistics, inventory management, and technology systems. Our analysis includes data gathering, process mapping, performance benchmarking, and stakeholder interviews. We identify bottlenecks, inefficiencies, risks, and opportunities while assessing capabilities against industry best practices. Deliverables include detailed findings, prioritized recommendations, cost-benefit analyses, and implementation roadmaps. Our supply chain analysis provides objective assessment of current state, identifies quick wins and strategic initiatives, and creates data-driven improvement plans. Whether addressing specific issues or conducting comprehensive reviews, we provide insights and recommendations that drive supply chain excellence and competitive advantage.""", 'duration': 70, 'categories': 'Operations,Consulting'},
                {'title': 'Procurement Strategy', 'description': """Develop strategic procurement approaches that reduce costs, mitigate risks, and support business objectives. Our procurement strategy services include spend analysis, category strategies, sourcing strategies, supplier relationship approaches, and organizational design. We analyze spending patterns, identify consolidation opportunities, develop commodity strategies, and establish governance frameworks. Our strategies address direct and indirect procurement, balance cost with quality and service, and consider total cost of ownership. We recommend technology enablers, establish metrics and KPIs, and create implementation plans with change management support. Strategic procurement transforms purchasing from tactical transaction processing into strategic value creation through better supplier relationships, improved processes, and leveraging spend for competitive advantage. Build procurement capabilities that consistently deliver savings, ensure supply continuity, and support innovation.""", 'duration': 50, 'categories': 'Operations,Finance'},
            ],
            # Company 15: Customer Success Team
            [
                {'title': 'Customer Onboarding', 'description': """Set new customers up for success with structured onboarding processes that accelerate time-to-value and build strong relationships from the start. We design comprehensive onboarding programs including welcome communications, setup assistance, training sessions, resource provision, and milestone tracking. Our onboarding addresses technical implementation, user adoption, and value realization while building personal connections. We create onboarding playbooks, develop training materials, establish success metrics, and implement tracking systems. Our approach identifies at-risk customers early, ensuring proactive intervention. Effective onboarding reduces early churn, increases product adoption, shortens time to value, and sets positive tone for ongoing relationships. We help customers achieve quick wins, understand product capabilities fully, and integrate solutions into their workflows. Transform onboarding from administrative necessity into strategic advantage that drives retention, expansion, and advocacy.""", 'duration': 40, 'categories': 'Customer Support'},
                {'title': 'Support Training', 'description': """Build exceptional support teams through comprehensive training programs covering technical knowledge, communication skills, problem-solving techniques, and customer service excellence. Our training addresses product knowledge, troubleshooting methodologies, ticket management systems, communication best practices, de-escalation techniques, and empathy development. We create training materials including product guides, troubleshooting flowcharts, response templates, and knowledge bases. Training includes role-playing exercises, real-world scenarios, and ongoing coaching. We cover phone, email, chat, and social media support channels with channel-specific best practices. Our programs include new hire onboarding, ongoing skill development, and advanced training for senior support staff. Effective support training improves first-contact resolution rates, reduces average handle time, increases customer satisfaction, and builds confident, capable teams that represent your brand positively in every customer interaction.""", 'duration': 35, 'categories': 'Customer Support,HR'},
                {'title': 'Help Desk Setup', 'description': """Establish efficient, scalable help desk operations that provide excellent customer support while controlling costs. We help you select and implement help desk systems, design support processes, establish ticket routing and escalation procedures, create knowledge bases, and set up reporting. Our help desk implementations include multi-channel support setup (phone, email, chat, portal), integration with CRM and other systems, self-service portal development, and automation configuration. We establish SLAs, define support tiers, create agent workflows, and implement quality monitoring. Our setup includes initial content creation, team training, and launch support. Well-designed help desk systems improve response times, increase resolution rates, provide visibility into support operations, enable self-service, and scale efficiently as support volume grows. Transform support from cost center into strategic asset that drives customer loyalty.""", 'duration': 60, 'categories': 'Customer Support,IT'},
                {'title': 'Customer Feedback Analysis', 'description': """Turn customer feedback into actionable insights that drive product improvements and enhance customer experiences. We collect, analyze, and synthesize feedback from surveys, support tickets, reviews, social media, and user interviews to identify trends, pain points, and opportunities. Our analysis categorizes feedback by theme, quantifies impact, prioritizes issues, and tracks sentiment over time. We create actionable reports with specific recommendations for product, service, and experience improvements. Our services include feedback system implementation, survey design, response analysis, and stakeholder reporting. We establish closed-loop feedback processes ensuring customers know their input drives changes. Systematic feedback analysis helps you understand customer needs deeply, identify improvement priorities, validate product decisions, reduce churn, and demonstrate customer-centric culture. Make data-driven decisions that enhance customer satisfaction and drive business growth.""", 'duration': 30, 'categories': 'Customer Support,Marketing'},
                {'title': 'Retention Strategies', 'description': """Reduce churn and increase customer lifetime value through strategic retention programs that identify at-risk customers and drive engagement. We develop comprehensive retention strategies including early warning systems, proactive outreach programs, value demonstration activities, and win-back campaigns. Our approach analyzes customer behavior data to identify churn signals, segments customers by risk level, and triggers appropriate interventions. We create retention playbooks, develop communication cadences, establish health scoring, and implement success metrics. Retention strategies address root causes of churn including product fit, adoption challenges, competitive threats, and customer service issues. We design loyalty programs, expansion initiatives, and advocacy development that increase customer stickiness. Effective retention strategies improve lifetime value, reduce acquisition costs, generate referrals, and build sustainable revenue growth. Focus on keeping customers happy and engaged to maximize business value.""", 'duration': 50, 'categories': 'Customer Support,Consulting'},
            ],
            # Company 16: Video Production Studio
            [
                {'title': 'Commercial Videos', 'description': """Captivate audiences and drive action with professionally produced commercial videos that showcase your brand, products, or services compellingly. Our full-service video production handles concept development, scriptwriting, storyboarding, filming, editing, and delivery. We manage casting, location scouting, equipment, crew, and post-production including color grading, sound design, and motion graphics. Our commercial videos work across television, digital platforms, and social media with platform-specific optimizations. We understand marketing objectives, target audiences, and brand guidelines to create videos that resonate emotionally while communicating key messages clearly. Our production quality rivals major brands while remaining cost-effective. Whether creating brand stories, product demonstrations, or testimonial videos, we deliver broadcast-quality commercial content that elevates brand perception, engages viewers, and achieves marketing goals.""", 'duration': 80, 'categories': 'Marketing,Design'},
                {'title': 'Explainer Videos', 'description': """Simplify complex concepts and engage audiences with animated explainer videos that communicate your value proposition clearly and memorably. Our explainer videos use animation, motion graphics, and visual storytelling to break down complicated ideas into digestible, engaging content. We handle scriptwriting, storyboarding, voiceover recording, animation, and sound design. Our videos work for product explanations, service overviews, process demonstrations, and educational content. We develop visual styles that align with your brand while appealing to target audiences. Explainer videos are versatile assets for websites, landing pages, sales presentations, and social media. They increase comprehension, improve conversion rates, reduce support inquiries, and make strong impressions. Whether explaining software features, introducing services, or teaching concepts, our explainer videos transform complex information into compelling visual stories that inform and persuade.""", 'duration': 60, 'categories': 'Marketing,Design'},
                {'title': 'Video Editing', 'description': """Transform raw footage into polished, professional videos with expert editing services covering cutting, color correction, audio enhancement, and effects. Our editors work with footage from any source, applying technical expertise and creative vision to create cohesive, engaging final products. Services include narrative structuring, pacing optimization, color grading, audio mixing, title creation, motion graphics, and visual effects. We edit videos for any purpose including marketing content, event coverage, training materials, social media, and more. Our editing enhances storytelling, maintains viewer engagement, ensures technical quality, and aligns with brand standards. We deliver final videos in any format optimized for intended platforms. Whether polishing existing footage, creating highlight reels, or completely restructuring content, our video editing services elevate production value and maximize content impact.""", 'duration': 40, 'categories': 'Design'},
                {'title': 'Corporate Presentations', 'description': """Engage stakeholders and communicate effectively with high-quality presentation videos that bring corporate messages to life. We produce videos for annual reports, investor presentations, employee communications, stakeholder updates, and more. Our corporate videos feature professional presenters, compelling visuals, data visualization, and clear messaging. We handle teleprompter setup, multi-camera filming, professional lighting, and broadcast-quality audio. Post-production includes editing, graphics, lower thirds, and branding elements. Corporate presentation videos work for live events, virtual meetings, websites, and internal communications. They convey professionalism, clarify complex information, maintain consistent messaging, and engage audiences more effectively than traditional presentations. Whether communicating vision, reporting results, or announcing initiatives, our presentation videos help leaders connect with audiences and deliver messages with impact and credibility.""", 'duration': 50, 'categories': 'Marketing'},
                {'title': 'Social Media Videos', 'description': """Capture attention and drive engagement with short-form video content optimized for social media platforms. We create videos specifically for Instagram, TikTok, Facebook, LinkedIn, Twitter, and YouTube that work within platform specifications and audience expectations. Our social media videos feature attention-grabbing openings, fast pacing, bold visuals, captions for sound-off viewing, and clear calls to action. Content types include product showcases, behind-the-scenes glimpses, tips and tutorials, announcements, and entertaining brand content. We understand platform-specific best practices, optimal lengths, and formats. Our videos are designed for mobile viewing, encourage shares, and drive desired actions. Social media video content increases reach, builds brand awareness, drives website traffic, and generates engagement. In social media feeds dominated by video, our short-form content helps your brand stand out and connect with audiences authentically.""", 'duration': 30, 'categories': 'Marketing'},
            ],
            # Company 17: Translation Services
            [
                {'title': 'Document Translation', 'description': """Break language barriers with professional document translation services that maintain meaning, tone, and intent across languages. Our experienced translators handle business documents, technical manuals, reports, presentations, policies, and more in dozens of language pairs. We use native speakers with subject matter expertise to ensure accuracy and cultural appropriateness. Our process includes translation, editing, proofreading, and quality assurance with terminology consistency and formatting preservation. We handle documents of any length from single-page letters to comprehensive manuals. Translations are certified when required for official purposes. We maintain confidentiality, meet deadlines reliably, and provide competitive pricing. Professional translation enables international business, ensures clear communication, demonstrates respect for diverse audiences, and opens global opportunities. Whether expanding internationally or communicating with diverse stakeholders, our translation services ensure your message resonates across languages.""", 'duration': 35, 'categories': 'Operations'},
                {'title': 'Website Localization', 'description': """Expand global reach with comprehensive website localization that adapts content, design, and functionality for target markets. Our localization goes beyond translation to consider cultural preferences, local conventions, regulatory requirements, and user expectations. We localize all website elements including text content, images, videos, navigation, forms, and metadata. Our process includes translation, cultural adaptation, functionality testing, SEO optimization for local search, and currency/date/measurement format adjustments. We manage technical aspects like character encoding, right-to-left languages, and content management system integration. Localized websites provide native-language experiences that build trust, improve engagement, and increase conversions in international markets. Whether localizing e-commerce sites, corporate websites, or web applications, we help you connect authentically with global audiences and compete effectively in international markets.""", 'duration': 70, 'categories': 'IT,Marketing'},
                {'title': 'Legal Translation', 'description': """Ensure accuracy in legal matters with specialized legal translation services from translators with legal expertise and training. We translate contracts, agreements, patents, litigation documents, regulatory filings, terms and conditions, privacy policies, and other legal materials. Our legal translators understand legal terminology, concepts, and systems in both source and target languages. We maintain precise meaning, preserve legal intent, and ensure terminology consistency critical in legal contexts. Our translations are suitable for legal proceedings, regulatory submissions, and contract execution with certification available when required. We maintain strict confidentiality, deliver accurate translations, and meet filing deadlines. Legal translation requires specialized expertise beyond general translation. Our services ensure your legal documents communicate clearly and precisely across languages, protecting your interests in international legal and business matters.""", 'duration': 45, 'categories': 'Legal'},
                {'title': 'Marketing Copy Translation', 'description': """Maintain brand voice and persuasive power across languages with marketing copy localization that resonates with target audiences. Our marketing translators are creative copywriters who adapt messaging to cultural contexts while preserving brand personality and marketing objectives. We localize advertisements, brochures, websites, email campaigns, social media content, and product descriptions. Our approach considers cultural references, humor, idioms, and emotional triggers that vary across markets. We maintain brand consistency while ensuring content feels native rather than translated. Marketing localization includes adaptation of slogans, taglines, and calls to action that may not translate directly. We conduct market research, test messaging with target audiences, and refine based on feedback. Effective marketing translation drives engagement, builds brand affinity, and achieves marketing goals in international markets by speaking to audiences in their language and cultural context.""", 'duration': 30, 'categories': 'Marketing'},
                {'title': 'Interpretation Services', 'description': """Enable real-time multilingual communication with professional interpretation services for meetings, conferences, negotiations, and events. We provide consecutive interpretation for smaller meetings and simultaneous interpretation for larger events requiring real-time translation. Our interpreters are fluent, experienced professionals with subject matter knowledge who facilitate clear communication between parties speaking different languages. We handle business meetings, legal proceedings, medical appointments, conference presentations, and more. Our interpreters maintain neutrality, preserve confidentiality, and convey messages accurately including tone and nuance. We provide in-person or remote interpretation via phone or video. Interpretation services enable international collaboration, facilitate negotiations, ensure understanding in critical situations, and demonstrate respect for linguistic diversity. Break down language barriers and communicate effectively across languages with professional interpretation.""", 'duration': 20, 'categories': 'Operations'},
            ],
            # Company 18: Innovation Workshop
            [
                {'title': 'Innovation Strategy', 'description': """Build sustainable innovation capabilities with comprehensive innovation strategies that align with business objectives and create competitive advantages. We help organizations define innovation ambitions, establish innovation portfolios balancing incremental and breakthrough initiatives, allocate resources effectively, and create governance structures. Our strategy development includes innovation maturity assessment, capability gap analysis, ecosystem mapping, and roadmap creation. We address innovation culture, processes, metrics, and organizational structures that enable innovation. Our strategies consider market trends, technology developments, and competitive dynamics. We facilitate leadership alignment, establish innovation metrics, and create implementation plans with clear milestones. Innovation strategy transforms innovation from ad-hoc activities into systematic capabilities that consistently generate new growth opportunities, improve offerings, and adapt to changing markets. Build innovation capabilities that drive long-term success and resilience.""", 'duration': 60, 'categories': 'Consulting'},
                {'title': 'Product Development', 'description': """Bring successful new products to market with comprehensive product development consulting covering opportunity identification through launch and beyond. We guide you through market research, concept development, business case creation, prototype development, testing, and go-to-market planning. Our process emphasizes customer needs, rapid experimentation, and iterative development. We facilitate cross-functional collaboration, apply design thinking and agile methodologies, and help teams navigate uncertainty inherent in innovation. Our consultants provide frameworks, tools, coaching, and hands-on support throughout development. We help validate assumptions, make go/no-go decisions, and optimize product-market fit. Whether developing physical products, software, or services, our product development expertise increases success rates, reduces time to market, and creates offerings that customers value. Transform ideas into successful products that drive growth and strengthen market position.""", 'duration': 100, 'categories': 'Consulting,Development'},
                {'title': 'Design Thinking Workshops', 'description': """Unlock creative problem-solving and generate innovative solutions through facilitated design thinking workshops. We guide teams through human-centered innovation processes including empathy development, problem definition, ideation, prototyping, and testing. Our workshops bring diverse participants together to tackle challenges through structured, creative approaches. We facilitate sessions ranging from half-day workshops to multi-day innovation sprints. Activities include customer journey mapping, brainstorming, rapid prototyping, and solution testing. Design thinking workshops generate numerous ideas, identify innovative solutions, build innovation capabilities, and create alignment around customer needs. Our experienced facilitators create safe environments for creative thinking, manage group dynamics, and ensure productive outcomes. Whether addressing specific challenges or building innovation skills, design thinking workshops energize teams, generate breakthrough ideas, and create customer-centric solutions.""", 'duration': 40, 'categories': 'Consulting,HR'},
                {'title': 'R&D Strategy', 'description': """Maximize research and development impact with strategic R&D planning that balances short-term needs with long-term capability building. We help organizations define R&D priorities, allocate resources across projects, establish portfolio management processes, and create governance structures. Our R&D strategy considers technology trends, competitive dynamics, customer needs, and organizational capabilities. We assess current R&D effectiveness, identify improvement opportunities, and recommend organizational structures, processes, and metrics. Our strategies address open innovation, partnerships, IP management, and technology platforms. We facilitate leadership alignment on R&D direction and investment levels. Strategic R&D planning ensures research investments generate competitive advantages, support business strategy, and create future growth options. Transform R&D from cost center into strategic asset that drives innovation, differentiates offerings, and builds sustainable competitive advantages through superior technology and capabilities.""", 'duration': 75, 'categories': 'Consulting'},
                {'title': 'Technology Scouting', 'description': """Stay ahead of disruption and identify opportunities through systematic technology scouting that monitors emerging technologies and trends. We track developments in relevant technology domains, assess potential impacts on your business, and identify opportunities for adoption or partnership. Our scouting covers technologies like artificial intelligence, blockchain, IoT, advanced materials, and more based on your interests. We attend conferences, monitor research publications, engage with startups, and leverage networks to identify emerging capabilities. Our reports highlight relevant technologies, assess maturity and commercialization timelines, and recommend actions. Technology scouting helps you anticipate disruption, identify competitive threats, discover innovation opportunities, and make informed technology investment decisions. Build awareness of technological change that enables proactive adaptation rather than reactive response when technologies disrupt markets.""", 'duration': 50, 'categories': 'Consulting,IT'},
            ],
            # Company 19: Quality Assurance Experts
            [
                {'title': 'Software Testing', 'description': """Ensure software quality and reliability with comprehensive QA testing services covering functional, integration, regression, and user acceptance testing. Our experienced QA engineers develop test strategies, create detailed test cases, execute testing, document defects, and verify fixes. We test web applications, mobile apps, APIs, and software systems using manual and automated approaches. Our testing covers functionality, usability, compatibility across browsers and devices, security vulnerabilities, and edge cases. We integrate with development processes, provide clear defect reports with reproduction steps, and track quality metrics. Our testing identifies issues before release, reduces production defects, improves user experiences, and builds confidence in software quality. Whether providing ongoing QA support or testing specific releases, our software testing services help you deliver reliable, high-quality software that meets requirements and user expectations.""", 'duration': 80, 'categories': 'IT,Development'},
                {'title': 'Test Automation', 'description': """Accelerate testing and improve coverage with automated testing frameworks that execute tests efficiently and consistently. We implement test automation using tools like Selenium, Cypress, Appium, and custom frameworks. Our services include automation strategy development, framework design and implementation, test script creation, CI/CD integration, and team training. We automate regression tests, API tests, and critical user journeys while identifying tests best suited for automation versus manual testing. Automated testing provides fast feedback, enables continuous integration, increases test coverage, and reduces manual testing effort. We maintain test suites as applications evolve, ensuring automation remains valuable. Test automation enables faster release cycles, improves software quality through consistent testing, and frees QA teams to focus on exploratory testing and complex scenarios that require human judgment.""", 'duration': 90, 'categories': 'IT,Development'},
                {'title': 'Quality Audits', 'description': """Ensure quality management systems meet standards and drive continuous improvement with comprehensive quality audits. We conduct internal audits assessing compliance with quality standards like ISO 9001, industry-specific requirements, and internal quality policies. Our audits examine processes, documentation, training records, corrective actions, and management reviews. We interview personnel, observe processes, and review records to identify non-conformances and improvement opportunities. Audit deliverables include detailed findings, corrective action recommendations, and improvement suggestions. We help prepare for external audits, ensuring organizations meet certification requirements. Quality audits verify system effectiveness, identify gaps before external auditors do, drive continuous improvement, and demonstrate commitment to quality. Regular audits maintain quality system integrity, ensure ongoing compliance, and create culture of continuous improvement that enhances operational excellence.""", 'duration': 50, 'categories': 'Operations,Consulting'},
                {'title': 'Performance Testing', 'description': """Ensure applications perform reliably under expected and peak loads with comprehensive performance and load testing services. We simulate realistic user loads, identify performance bottlenecks, measure response times, and assess system scalability. Our testing covers web applications, APIs, databases, and infrastructure using tools like JMeter, LoadRunner, and Gatling. We develop performance test strategies, create test scenarios, execute load tests, analyze results, and provide optimization recommendations. Testing identifies bottlenecks in application code, database queries, server configurations, and network capacity. We test normal loads, peak loads, stress conditions, and endurance scenarios. Performance testing prevents production performance issues, ensures positive user experiences, validates infrastructure sizing, and builds confidence in system scalability. Launch with confidence knowing your application performs reliably under real-world conditions.""", 'duration': 60, 'categories': 'IT,Development'},
                {'title': 'QA Process Design', 'description': """Build effective quality assurance capabilities with well-designed QA processes that ensure consistent quality while supporting rapid development. We design testing processes, define quality gates, establish standards, create templates and checklists, and implement metrics. Our process design considers development methodologies (Agile, Waterfall, DevOps), organizational structure, product complexity, and risk tolerance. We define test strategies, establish defect management processes, create testing workflows, and implement quality metrics and reporting. Our processes balance thoroughness with efficiency, emphasizing risk-based testing and continuous improvement. We provide implementation support, training, and ongoing optimization. Well-designed QA processes ensure consistent quality, provide clear accountability, enable efficient testing, and scale as organizations grow. Transform QA from bottleneck into enabler of rapid, reliable software delivery.""", 'duration': 55, 'categories': 'Operations,Consulting'},
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

        # Timestamp reference for the rest of the seed data
        now = datetime.datetime.now(datetime.timezone.utc)

        # Create marketplace view events to drive demand signals
        print("Creating marketplace view events for demand signal...")
        view_buckets = [30, 24, 18, 12, 8, 4, 2]  # descending counts to give variation
        view_events = 0
        for idx, service in enumerate(all_services):
            bucket = view_buckets[idx % len(view_buckets)]
            for m in range(bucket):
                evt = ServiceViewEvent(
                    view_id=uuid.uuid4(),
                    service_id=service.service_id,
                    viewed_at=now - datetime.timedelta(days=idx % 10, minutes=m)
                )
                db.session.add(evt)
                view_events += 1
        db.session.commit()
        print(f"✓ Created {view_events} service view events")
        
        # Create trade flows for testing different statuses
        print("Creating trade flow test data...")
        
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

        # Create matched proposals to simulate chosenAsReturn counts
        matched_pairs = [(0, 10), (4, 11), (5, 12), (6, 13), (7, 14)]
        matched_created = 0
        for from_idx, to_idx in matched_pairs:
            service_from = [s for s in all_services if s.company_id == companies[from_idx].company_id][0]
            service_to = [s for s in all_services if s.company_id == companies[to_idx].company_id][1]
            proposal = DealProposal(
                proposal_id=uuid.uuid4(),
                from_company_id=companies[from_idx].company_id,
                to_company_id=companies[to_idx].company_id,
                from_service_id=service_from.service_id,
                to_service_id=service_to.service_id,
                status='matched',
                created_at=now - datetime.timedelta(days=4)
            )
            db.session.add(proposal)
            matched_created += 1
        db.session.commit()
        print(f"✓ Created {matched_created} matched proposals (counts as chosenAsReturn)")
        
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
        # Extended pairs for massive review data (60 deals = 120 reviews)
        completed_pairs = [
            (16, 6), (17, 7), (18, 8), (19, 9),
            (16, 8), (17, 9), (18, 6), (19, 7),
            (16, 10), (17, 11), (18, 12), (19, 13),
            (0, 5), (1, 4), (2, 3), (3, 2),
            (4, 14), (5, 15), (6, 16), (7, 17),
            (8, 18), (9, 19), (10, 0), (11, 1),
            (12, 2), (13, 3), (14, 4), (15, 5),
            (0, 10), (1, 11), (2, 12), (3, 13),
            (4, 0), (5, 1), (6, 2), (7, 3),
            (8, 4), (9, 5), (10, 6), (11, 7),
            # Additional pairs for more review data
            (12, 14), (13, 15), (14, 16), (15, 17),
            (0, 14), (1, 15), (2, 16), (3, 17),
            (4, 18), (5, 19), (6, 0), (7, 1),
            (8, 2), (9, 3), (10, 4), (11, 5),
            (12, 6), (13, 7), (14, 8), (15, 9),
            (16, 0), (17, 1), (18, 2), (19, 3),
            (0, 18), (1, 19), (2, 0), (3, 1),
            (4, 2), (5, 3), (6, 4), (7, 5),
        ]
        
        # Diverse review comments
        positive_comments = [
            "Excellent service! Highly professional and delivered great results.",
            "Outstanding collaboration. The team was responsive and exceeded our expectations.",
            "Top-notch quality work. Communication was clear throughout the entire process.",
            "Fantastic experience! Would definitely recommend and work with them again.",
            "Very impressed with the professionalism and attention to detail.",
            "Superb service delivery. The team was knowledgeable and efficient.",
            "Exceeded expectations in every way. A pleasure to work with!",
            "Remarkable expertise and dedication to the project. Highly satisfied!",
            "Exceptional quality and outstanding customer service throughout.",
            "Incredible work ethic and delivered beyond what we expected.",
            "Stellar performance! The best service provider we have worked with.",
            "Absolutely fantastic! Professional, timely, and exceeded all requirements.",
            "Amazing results! The team went above and beyond our expectations.",
            "Outstanding professionalism and incredible attention to detail.",
            "Phenomenal service! Would highly recommend to anyone.",
            "Flawless execution from start to finish. Truly impressive!",
        ]
        
        good_comments = [
            "Great collaboration. Would work together again!",
            "Solid service delivery. Minor delays but overall satisfied.",
            "Good experience overall. Professional team and decent quality.",
            "Satisfactory work. Met most of our requirements effectively.",
            "Positive experience. Good communication and reasonable turnaround time.",
            "Well executed project. A few hiccups but resolved quickly.",
            "Reliable service provider. Delivered what was promised.",
            "Professional approach and good quality deliverables.",
            "Competent team that handled the project efficiently.",
            "Good results. Some communication gaps but resolved well.",
            "Quality work with reasonable timelines. Happy with the outcome.",
            "Professional service with good attention to our needs.",
            "Delivered solid results. Would consider working with them again.",
            "Effective collaboration with minor room for improvement.",
            "Good value for the service provided. Satisfied overall.",
        ]
        
        average_comments = [
            "Average service. Met basic requirements but nothing exceptional.",
            "Decent work but room for improvement in communication.",
            "Acceptable results. Expected a bit more attention to detail.",
            "Fair experience. Service was okay but delivery could be faster.",
            "Middle-of-the-road performance. Gets the job done adequately.",
            "Satisfactory but not outstanding. Met minimum expectations.",
            "Adequate service level. Nothing special but completed the work.",
            "Okay experience. Some delays and communication issues.",
        ]
        
        below_average_comments = [
            "Disappointing experience. Several issues with quality and communication.",
            "Below expectations. Had to request multiple revisions.",
            "Subpar service. Would not recommend to others.",
            "Poor communication throughout. Delivery was late and quality was lacking.",
            "Unsatisfied with the results. Did not meet our requirements.",
        ]
        
        completed_count = 0
        reviews_count = 0
        for pair_idx, (from_idx, to_idx) in enumerate(completed_pairs):
            service_from = [s for s in all_services if s.company_id == companies[from_idx].company_id][0]
            service_to = [s for s in all_services if s.company_id == companies[to_idx].company_id][0]
            
            # Vary the timeline for more realistic data
            days_ago = 60 + (pair_idx * 5)
            completed_days_ago = 15 + (pair_idx * 2)
            
            # Create deal proposal (accepted)
            proposal = DealProposal(
                proposal_id=uuid.uuid4(),
                from_company_id=companies[from_idx].company_id,
                to_company_id=companies[to_idx].company_id,
                from_service_id=service_from.service_id,
                to_service_id=service_to.service_id,
                status='accepted',
                created_at=now - datetime.timedelta(days=days_ago)
            )
            db.session.add(proposal)
            db.session.flush()
            
            # Create active deal (completed)
            active_deal = ActiveDeal(
                active_deal_id=uuid.uuid4(),
                proposal_id=proposal.proposal_id,
                from_company_completed=True,
                to_company_completed=True,
                status='completed',
                created_at=now - datetime.timedelta(days=days_ago),
                completed_at=now - datetime.timedelta(days=completed_days_ago)
            )
            db.session.add(active_deal)
            completed_count += 1
            
            # Vary ratings and comments for diversity
            if pair_idx < 10:
                rating_from = 5
                rating_to = 5
                comment_from = positive_comments[pair_idx % len(positive_comments)]
                comment_to = positive_comments[(pair_idx + 1) % len(positive_comments)]
            elif pair_idx < 20:
                rating_from = 5 if pair_idx % 2 == 0 else 4
                rating_to = 4 if pair_idx % 3 == 0 else 5
                comment_from = positive_comments[(pair_idx - 10) % len(positive_comments)]
                comment_to = good_comments[(pair_idx - 10) % len(good_comments)]
            elif pair_idx < 28:
                rating_from = 4 if pair_idx % 2 == 0 else 3
                rating_to = 4
                comment_from = good_comments[(pair_idx - 20) % len(good_comments)]
                comment_to = good_comments[(pair_idx - 19) % len(good_comments)]
            elif pair_idx < 32:
                rating_from = 3
                rating_to = 3
                comment_from = average_comments[(pair_idx - 28) % len(average_comments)]
                comment_to = average_comments[(pair_idx - 27) % len(average_comments)]
            else:
                rating_from = 2 if pair_idx % 2 == 0 else 3
                rating_to = 2 if pair_idx % 3 == 0 else 3
                comment_from = below_average_comments[(pair_idx - 32) % len(below_average_comments)]
                comment_to = average_comments[(pair_idx - 32) % len(average_comments)]
            
            # Create reviews from both companies
            review_from = Review(
                review_id=uuid.uuid4(),
                deal_id=active_deal.active_deal_id,
                reviewer_id=users[from_idx].user_id,
                reviewed_company_id=companies[to_idx].company_id,
                reviewed_service_id=service_to.service_id,
                rating=rating_from,
                comment=f"{comment_from} - {companies[to_idx].name}",
                created_at=now - datetime.timedelta(days=completed_days_ago - 1)
            )
            db.session.add(review_from)
            reviews_count += 1
            
            review_to = Review(
                review_id=uuid.uuid4(),
                deal_id=active_deal.active_deal_id,
                reviewer_id=users[to_idx].user_id,
                reviewed_company_id=companies[from_idx].company_id,
                reviewed_service_id=service_from.service_id,
                rating=rating_to,
                comment=f"{comment_to} - {companies[from_idx].name}",
                created_at=now - datetime.timedelta(days=completed_days_ago - 1)
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
