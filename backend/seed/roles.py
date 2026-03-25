import random
from datetime import datetime, timedelta
from uuid import uuid4


def generate_roles(org_ids: dict[str, str], client_ids: list[str]) -> list[dict]:
    """Generate 15+ realistic roles across sectors."""
    now = datetime.utcnow()

    ROLES = [
        # Fintech
        {
            "title": "Senior Backend Engineer",
            "description": "Join our payments team to build the next generation of international transfer infrastructure. You will design and implement high-throughput, low-latency services processing millions of transactions daily. Strong Python experience required, with knowledge of distributed systems and message queues.",
            "org": "Monzo",
            "required_skills": [
                {"name": "Python", "min_years": 5, "importance": "required"},
                {"name": "PostgreSQL", "min_years": 3, "importance": "required"},
                {"name": "Docker", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Kubernetes", "min_years": None, "importance": "preferred"},
                {"name": "Kafka", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "85000", "max_amount": "105000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "fintech",
        },
        {
            "title": "Staff Platform Engineer",
            "description": "Lead our platform engineering efforts, designing and maintaining the infrastructure that powers our banking services. You will work across Kubernetes, Terraform, and AWS to ensure our platform scales reliably.",
            "org": "Starling Bank",
            "required_skills": [
                {"name": "Kubernetes", "min_years": 4, "importance": "required"},
                {"name": "AWS", "min_years": 5, "importance": "required"},
                {"name": "Terraform", "min_years": 3, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Go", "min_years": None, "importance": "preferred"},
                {"name": "Prometheus", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "lead",
            "salary_band": {"min_amount": "110000", "max_amount": "140000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "fintech",
        },
        {
            "title": "Senior Data Engineer",
            "description": "Build and maintain our real-time data platform powering fraud detection and customer analytics. Experience with Spark, Airflow, and modern data stack required.",
            "org": "Checkout.com",
            "required_skills": [
                {"name": "Python", "min_years": 4, "importance": "required"},
                {"name": "Apache Spark", "min_years": 2, "importance": "required"},
                {"name": "SQL", "min_years": 4, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Airflow", "min_years": None, "importance": "preferred"},
                {"name": "dbt", "min_years": None, "importance": "preferred"},
                {"name": "Kafka", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "90000", "max_amount": "115000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "fintech",
        },
        # Healthtech
        {
            "title": "ML Engineer — Clinical NLP",
            "description": "Work on cutting-edge NLP models for clinical text understanding. You will build and deploy models that extract medical insights from consultation transcripts, improving patient outcomes across our platform.",
            "org": "Babylon Health",
            "required_skills": [
                {"name": "Python", "min_years": 4, "importance": "required"},
                {"name": "PyTorch", "min_years": 2, "importance": "required"},
                {"name": "NLP", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "MLflow", "min_years": None, "importance": "preferred"},
                {"name": "Docker", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "95000", "max_amount": "120000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "healthtech",
        },
        {
            "title": "Full-Stack Engineer",
            "description": "Build patient-facing web applications using React and Node.js. You will work closely with clinicians and designers to create intuitive interfaces for remote patient monitoring.",
            "org": "Huma",
            "required_skills": [
                {"name": "React", "min_years": 3, "importance": "required"},
                {"name": "TypeScript", "min_years": 2, "importance": "required"},
                {"name": "Node.js", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "GraphQL", "min_years": None, "importance": "preferred"},
                {"name": "PostgreSQL", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "mid",
            "salary_band": {"min_amount": "60000", "max_amount": "80000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "remote",
            "industry": "healthtech",
        },
        # SaaS
        {
            "title": "Senior Frontend Engineer",
            "description": "Join our product team to build beautiful, high-performance dashboards using React and Next.js. You will own the frontend architecture for our analytics platform, serving enterprise customers worldwide.",
            "org": "ContentSquare",
            "required_skills": [
                {"name": "React", "min_years": 4, "importance": "required"},
                {"name": "TypeScript", "min_years": 3, "importance": "required"},
                {"name": "Next.js", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Tailwind CSS", "min_years": None, "importance": "preferred"},
                {"name": "GraphQL", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "80000", "max_amount": "100000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "SaaS",
        },
        {
            "title": "Python Backend Developer",
            "description": "Build and scale our revenue delivery platform APIs. Work with a small, high-impact engineering team processing billions in payment volume for SaaS companies globally.",
            "org": "Paddle",
            "required_skills": [
                {"name": "Python", "min_years": 3, "importance": "required"},
                {"name": "FastAPI", "min_years": 1, "importance": "required"},
                {"name": "PostgreSQL", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Redis", "min_years": None, "importance": "preferred"},
                {"name": "Docker", "min_years": None, "importance": "preferred"},
                {"name": "AWS", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "mid",
            "salary_band": {"min_amount": "60000", "max_amount": "80000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "SaaS",
        },
        {
            "title": "Senior ML Engineer",
            "description": "Lead the development of our AI decision intelligence platform. Build production ML pipelines that help enterprise customers optimise pricing, inventory, and demand forecasting.",
            "org": "Peak AI",
            "required_skills": [
                {"name": "Python", "min_years": 5, "importance": "required"},
                {"name": "Machine Learning", "min_years": 3, "importance": "required"},
                {"name": "AWS", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "PyTorch", "min_years": None, "importance": "preferred"},
                {"name": "Scikit-learn", "min_years": None, "importance": "preferred"},
                {"name": "MLflow", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "80000", "max_amount": "100000", "currency": "GBP"},
            "location": "Manchester",
            "remote_policy": "hybrid",
            "industry": "SaaS",
        },
        # E-commerce
        {
            "title": "Senior Backend Engineer — Personalisation",
            "description": "Build the recommendation and personalisation engine that powers our recipe box experience. Work with data scientists and product to deliver personalised meal plans using collaborative filtering and real-time signals.",
            "org": "Gousto",
            "required_skills": [
                {"name": "Python", "min_years": 4, "importance": "required"},
                {"name": "AWS", "min_years": 3, "importance": "required"},
                {"name": "PostgreSQL", "min_years": 3, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Redis", "min_years": None, "importance": "preferred"},
                {"name": "Machine Learning", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "80000", "max_amount": "100000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "e-commerce",
        },
        # More roles
        {
            "title": "DevOps Engineer",
            "description": "Support and improve our CI/CD pipelines and cloud infrastructure. Work with Docker, Kubernetes, and Terraform to ensure reliable, scalable deployments across multiple environments.",
            "org": "Thought Machine",
            "required_skills": [
                {"name": "Docker", "min_years": 3, "importance": "required"},
                {"name": "Kubernetes", "min_years": 2, "importance": "required"},
                {"name": "CI/CD", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Terraform", "min_years": None, "importance": "preferred"},
                {"name": "AWS", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "mid",
            "salary_band": {"min_amount": "65000", "max_amount": "85000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "fintech",
        },
        {
            "title": "Junior Software Engineer",
            "description": "Join our graduate programme and work alongside experienced engineers building identity verification technology. You will learn Python, testing, and deployment practices in a supportive team environment.",
            "org": "Onfido",
            "required_skills": [
                {"name": "Python", "min_years": None, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "JavaScript", "min_years": None, "importance": "preferred"},
                {"name": "Docker", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "junior",
            "salary_band": {"min_amount": "35000", "max_amount": "45000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "onsite",
            "industry": "fintech",
        },
        {
            "title": "Product Manager — Learning Platform",
            "description": "Own the product roadmap for our employer-facing learning platform. You will work with engineering, design, and sales to define features, prioritise the backlog, and measure impact through data-driven decision making.",
            "org": "Multiverse",
            "required_skills": [
                {"name": "Product Strategy", "min_years": 3, "importance": "required"},
                {"name": "Agile", "min_years": 3, "importance": "required"},
                {"name": "Data Analysis", "min_years": 2, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "SQL", "min_years": None, "importance": "preferred"},
                {"name": "Stakeholder Management", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "85000", "max_amount": "105000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "edtech",
        },
        {
            "title": "Lead Backend Engineer",
            "description": "Lead a team of 6 engineers building core banking infrastructure. You will define technical direction, mentor engineers, and deliver critical payment processing capabilities serving millions of business customers.",
            "org": "Starling Bank",
            "required_skills": [
                {"name": "Java", "min_years": 7, "importance": "required"},
                {"name": "Microservices", "min_years": 4, "importance": "required"},
                {"name": "Team Leadership", "min_years": 3, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Kubernetes", "min_years": None, "importance": "preferred"},
                {"name": "AWS", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "lead",
            "salary_band": {"min_amount": "110000", "max_amount": "130000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "fintech",
        },
        {
            "title": "Data Analyst",
            "description": "Join our analytics team to help drive data-informed decisions across the business. You will build dashboards, run analyses, and partner with product and commercial teams to uncover growth opportunities.",
            "org": "Gousto",
            "required_skills": [
                {"name": "SQL", "min_years": 2, "importance": "required"},
                {"name": "Python", "min_years": 1, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "dbt", "min_years": None, "importance": "preferred"},
                {"name": "Tableau", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "mid",
            "salary_band": {"min_amount": "45000", "max_amount": "60000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "hybrid",
            "industry": "e-commerce",
        },
        {
            "title": "Senior React Engineer",
            "description": "Build the next generation of our merchant dashboard, a data-heavy web application used by thousands of global SaaS companies. You will own component architecture, performance optimisation, and design system development.",
            "org": "Paddle",
            "required_skills": [
                {"name": "React", "min_years": 4, "importance": "required"},
                {"name": "TypeScript", "min_years": 3, "importance": "required"},
            ],
            "preferred_skills": [
                {"name": "Next.js", "min_years": None, "importance": "preferred"},
                {"name": "Tailwind CSS", "min_years": None, "importance": "preferred"},
                {"name": "Testing Library", "min_years": None, "importance": "preferred"},
            ],
            "seniority": "senior",
            "salary_band": {"min_amount": "80000", "max_amount": "100000", "currency": "GBP"},
            "location": "London",
            "remote_policy": "remote",
            "industry": "SaaS",
        },
    ]

    results = []
    for role_data in ROLES:
        org_name = role_data.pop("org")
        org_id = org_ids.get(org_name)
        days_ago = random.randint(1, 30)
        created = now - timedelta(days=days_ago)

        results.append({
            "id": str(uuid4()),
            "title": role_data["title"],
            "description": role_data["description"],
            "organisation_id": org_id,
            "required_skills": role_data["required_skills"],
            "preferred_skills": role_data["preferred_skills"],
            "seniority": role_data["seniority"],
            "salary_band": role_data["salary_band"],
            "location": role_data["location"],
            "remote_policy": role_data["remote_policy"],
            "industry": role_data["industry"],
            "embedding": None,
            "extraction_confidence": round(random.uniform(0.85, 0.98), 2),
            "status": "active",
            "created_at": created.isoformat(),
            "created_by": random.choice(client_ids),
        })

    # Generate 30 additional roles programmatically
    EXTRA_ROLES = [
        ("Senior React Engineer", "frontend", "senior", 80000, 100000),
        ("Junior Python Developer", "backend", "junior", 35000, 45000),
        ("Staff Data Engineer", "data", "lead", 110000, 140000),
        ("Mid-Level Go Developer", "backend", "mid", 60000, 75000),
        ("Head of Engineering", "backend", "principal", 130000, 170000),
        ("DevOps Engineer", "devops", "mid", 65000, 80000),
        ("ML Engineer — NLP", "ml", "senior", 90000, 120000),
        ("Frontend Tech Lead", "frontend", "lead", 95000, 120000),
        ("Data Analyst", "data", "junior", 35000, 45000),
        ("Platform Engineer", "devops", "senior", 85000, 110000),
        ("Full Stack Developer", "frontend", "mid", 55000, 70000),
        ("Senior Data Scientist", "ml", "senior", 90000, 115000),
        ("Backend Engineer — Payments", "backend", "mid", 60000, 80000),
        ("SRE / Infrastructure", "devops", "senior", 85000, 105000),
        ("React Native Developer", "frontend", "mid", 55000, 70000),
        ("AI/ML Research Engineer", "ml", "lead", 100000, 135000),
        ("Junior Frontend Developer", "frontend", "junior", 30000, 42000),
        ("Senior TypeScript Engineer", "frontend", "senior", 80000, 100000),
        ("Data Platform Lead", "data", "lead", 100000, 130000),
        ("Cloud Architect", "devops", "lead", 110000, 140000),
        ("Python Backend — Healthcare", "backend", "senior", 80000, 100000),
        ("Quantitative Developer", "backend", "senior", 100000, 140000),
        ("Analytics Engineer", "data", "mid", 55000, 70000),
        ("Senior iOS Engineer", "frontend", "senior", 80000, 100000),
        ("MLOps Engineer", "ml", "mid", 65000, 85000),
        ("Junior DevOps Engineer", "devops", "junior", 35000, 48000),
        ("Tech Lead — Marketplace", "backend", "lead", 95000, 120000),
        ("Senior Golang Engineer", "backend", "senior", 85000, 110000),
        ("Product Engineer", "frontend", "mid", 60000, 80000),
        ("Principal Engineer", "backend", "principal", 130000, 160000),
    ]

    ROLE_DESCRIPTIONS = {
        "backend": "We are looking for an experienced engineer to join our growing team building scalable backend services. You will work with modern technologies in a fast-paced environment, contributing to architecture decisions and mentoring junior developers.",
        "frontend": "Join our product team to build beautiful, performant user interfaces. You will work closely with designers and product managers to deliver delightful experiences for our users across web and mobile platforms.",
        "data": "We need a talented data professional to help us build and maintain our data infrastructure. You will design pipelines, build models, and ensure data quality across the organisation.",
        "devops": "Help us scale our infrastructure and improve developer experience. You will own our deployment pipelines, monitoring, and cloud infrastructure, ensuring reliability and performance at scale.",
        "ml": "Join our AI team to build production machine learning systems. You will develop, deploy, and monitor ML models that directly impact our product and users.",
    }

    SKILL_MAP = {
        "backend": ([("Python", 3), ("PostgreSQL", 2), ("Docker", 2)], [("Kubernetes", None), ("Redis", None)]),
        "frontend": ([("React", 2), ("TypeScript", 2), ("CSS", 2)], [("Next.js", None), ("GraphQL", None)]),
        "data": ([("Python", 2), ("SQL", 3), ("Apache Spark", 1)], [("dbt", None), ("Airflow", None)]),
        "devops": ([("AWS", 3), ("Kubernetes", 2), ("Terraform", 2)], [("Docker", None), ("CI/CD", None)]),
        "ml": ([("Python", 3), ("PyTorch", 1), ("Machine Learning", 2)], [("MLflow", None), ("NLP", None)]),
    }

    all_org_ids = list(org_ids.values())
    locations = ["London", "London", "London", "Manchester", "Remote", "Edinburgh", "Bristol", "Cambridge"]
    policies = ["hybrid", "hybrid", "remote", "onsite", "hybrid"]
    industries = ["fintech", "healthtech", "SaaS", "e-commerce", "edtech", "fintech"]
    statuses = ["active", "active", "active", "active", "paused", "draft"]

    for title, spec, seniority, sal_min, sal_max in EXTRA_ROLES:
        req, pref = SKILL_MAP[spec]
        required_skills = [{"name": s, "min_years": y, "importance": "required"} for s, y in req]
        preferred_skills = [{"name": s, "min_years": y, "importance": "preferred"} for s, y in pref]
        days_ago = random.randint(1, 45)

        results.append({
            "id": str(uuid4()),
            "title": title,
            "description": ROLE_DESCRIPTIONS[spec],
            "organisation_id": random.choice(all_org_ids),
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "seniority": seniority,
            "salary_band": {"min_amount": str(sal_min), "max_amount": str(sal_max), "currency": "GBP"},
            "location": random.choice(locations),
            "remote_policy": random.choice(policies),
            "industry": random.choice(industries),
            "embedding": None,
            "extraction_confidence": round(random.uniform(0.82, 0.97), 2),
            "status": random.choice(statuses),
            "created_at": (now - timedelta(days=days_ago)).isoformat(),
            "created_by": random.choice(client_ids),
        })

    return results
