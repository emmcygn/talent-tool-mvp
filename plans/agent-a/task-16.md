# Agent A — Task 16: Seed Data + Final Integration

## Mission
Generate comprehensive, realistic UK-market seed data (50+ candidates, 15+ roles, 10+ organisations, demo users), run the full extraction and matching pipeline on it, pre-generate match explanations, populate signal history for analytics dashboards, produce a SQL seed file for Supabase, and run integration tests across all endpoints.

## Context
This is Days 5-6. This is the final Agent A task. All backend components are built. This task ties everything together with realistic data that makes the demo compelling. The seed data must feel real enough that a recruitment professional would recognise the patterns — UK cities, realistic job titles, actual technology stacks, plausible salary ranges, and genuine-sounding company names. The full pipeline runs end-to-end: extraction, matching, explanation generation, signal emission.

## Prerequisites
- All previous Agent A tasks (01-15) complete
- Full backend operational: adapters, pipelines, matching, copilot, signals, admin
- Supabase schema deployed with all migrations

## Checklist
- [ ] Create `backend/seed/__init__.py`
- [ ] Create `backend/seed/organisations.py` — 10+ UK client companies
- [ ] Create `backend/seed/users.py` — demo users (5 partners, 3 clients, 1 admin)
- [ ] Create `backend/seed/candidates.py` — 50+ realistic UK candidates with CVs
- [ ] Create `backend/seed/roles.py` — 15+ roles across fintech/healthtech/SaaS
- [ ] Create `backend/seed/generate.py` — master seed orchestrator
- [ ] Generate `supabase/seed.sql` — SQL seed file
- [ ] Run full pipeline on seed data (extraction + matching + explanations)
- [ ] Populate signal history for analytics
- [ ] Create pre-generated matches with explanations
- [ ] Create `backend/tests/test_integration.py` — end-to-end tests
- [ ] Run all tests, verify pass
- [ ] Commit: "Agent A Task 16: Seed data + full integration"

## Implementation Details

### Organisations (`backend/seed/organisations.py`)

```python
from uuid import uuid4

ORGANISATIONS = [
    {
        "id": str(uuid4()),
        "name": "Monzo",
        "industry": "fintech",
        "location": "London",
        "description": "Digital challenger bank serving millions of UK customers",
        "size": "1000-5000",
    },
    {
        "id": str(uuid4()),
        "name": "Babylon Health",
        "industry": "healthtech",
        "location": "London",
        "description": "AI-powered healthcare platform providing virtual consultations",
        "size": "500-1000",
    },
    {
        "id": str(uuid4()),
        "name": "Paddle",
        "industry": "SaaS",
        "location": "London",
        "description": "Revenue delivery platform for SaaS companies",
        "size": "200-500",
    },
    {
        "id": str(uuid4()),
        "name": "Starling Bank",
        "industry": "fintech",
        "location": "London",
        "description": "Award-winning mobile-first bank for personal and business banking",
        "size": "1000-5000",
    },
    {
        "id": str(uuid4()),
        "name": "Huma",
        "industry": "healthtech",
        "location": "London",
        "description": "Digital health platform for remote patient monitoring and clinical trials",
        "size": "200-500",
    },
    {
        "id": str(uuid4()),
        "name": "Checkout.com",
        "industry": "fintech",
        "location": "London",
        "description": "Cloud-based payment processing platform for global merchants",
        "size": "1000-5000",
    },
    {
        "id": str(uuid4()),
        "name": "ContentSquare",
        "industry": "SaaS",
        "location": "London",
        "description": "Digital experience analytics platform for enterprise brands",
        "size": "500-1000",
    },
    {
        "id": str(uuid4()),
        "name": "Gousto",
        "industry": "e-commerce",
        "location": "London",
        "description": "Recipe box delivery service with AI-powered menu personalisation",
        "size": "500-1000",
    },
    {
        "id": str(uuid4()),
        "name": "Peak AI",
        "industry": "SaaS",
        "location": "Manchester",
        "description": "AI platform helping businesses optimise decisions through machine learning",
        "size": "100-200",
    },
    {
        "id": str(uuid4()),
        "name": "Multiverse",
        "industry": "edtech",
        "location": "London",
        "description": "Alternative to university providing apprenticeships at top companies",
        "size": "500-1000",
    },
    {
        "id": str(uuid4()),
        "name": "Thought Machine",
        "industry": "fintech",
        "location": "London",
        "description": "Cloud-native core banking technology provider",
        "size": "500-1000",
    },
    {
        "id": str(uuid4()),
        "name": "Onfido",
        "industry": "fintech",
        "location": "London",
        "description": "AI-powered identity verification and authentication platform",
        "size": "500-1000",
    },
]
```

### Demo Users (`backend/seed/users.py`)

```python
from uuid import uuid4

def get_demo_users(org_ids: dict[str, str]) -> list[dict]:
    """
    Generate demo users. org_ids maps org name → org ID.

    Returns list of user dicts with pre-set UUIDs for stable references.
    """
    return [
        # Talent Partners (5)
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "email": "sarah.chen@recruittech.demo",
            "first_name": "Sarah",
            "last_name": "Chen",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-1",  # for Supabase Auth seeding
        },
        {
            "id": "11111111-1111-1111-1111-222222222222",
            "email": "james.oconnor@recruittech.demo",
            "first_name": "James",
            "last_name": "O'Connor",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-2",
        },
        {
            "id": "11111111-1111-1111-1111-333333333333",
            "email": "priya.sharma@recruittech.demo",
            "first_name": "Priya",
            "last_name": "Sharma",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-3",
        },
        {
            "id": "11111111-1111-1111-1111-444444444444",
            "email": "tom.wright@recruittech.demo",
            "first_name": "Tom",
            "last_name": "Wright",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-4",
        },
        {
            "id": "11111111-1111-1111-1111-555555555555",
            "email": "elena.volkov@recruittech.demo",
            "first_name": "Elena",
            "last_name": "Volkov",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-5",
        },
        # Clients (3)
        {
            "id": "22222222-2222-2222-2222-111111111111",
            "email": "alex.thompson@monzo.demo",
            "first_name": "Alex",
            "last_name": "Thompson",
            "role": "client",
            "organisation_id": org_ids.get("Monzo"),
            "is_active": True,
            "password": "demo-client-1",
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "email": "rachel.green@babylon.demo",
            "first_name": "Rachel",
            "last_name": "Green",
            "role": "client",
            "organisation_id": org_ids.get("Babylon Health"),
            "is_active": True,
            "password": "demo-client-2",
        },
        {
            "id": "22222222-2222-2222-2222-333333333333",
            "email": "david.kim@paddle.demo",
            "first_name": "David",
            "last_name": "Kim",
            "role": "client",
            "organisation_id": org_ids.get("Paddle"),
            "is_active": True,
            "password": "demo-client-3",
        },
        # Admin (1)
        {
            "id": "33333333-3333-3333-3333-111111111111",
            "email": "admin@recruittech.demo",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-admin-1",
        },
    ]
```

### Candidates (`backend/seed/candidates.py`)

```python
from uuid import uuid4
from datetime import datetime, timedelta
import random

# Candidate templates — each will be expanded with full details during generation
CANDIDATE_TEMPLATES = [
    # --- Senior Backend / Python ---
    {
        "first_name": "Oliver", "last_name": "Hughes", "location": "London",
        "seniority": "senior", "availability": "immediate",
        "skills": [
            {"name": "Python", "years": 7, "confidence": 0.95},
            {"name": "FastAPI", "years": 3, "confidence": 0.9},
            {"name": "PostgreSQL", "years": 6, "confidence": 0.92},
            {"name": "Docker", "years": 5, "confidence": 0.88},
            {"name": "AWS", "years": 4, "confidence": 0.85},
            {"name": "Redis", "years": 3, "confidence": 0.82},
        ],
        "experience": [
            {"company": "Revolut", "title": "Senior Backend Engineer", "duration_months": 30, "industry": "fintech"},
            {"company": "Deliveroo", "title": "Backend Engineer", "duration_months": 24, "industry": "e-commerce"},
            {"company": "Sky", "title": "Software Developer", "duration_months": 18, "industry": "media"},
        ],
        "industries": ["fintech", "e-commerce"],
        "salary_expectation": {"min_amount": "85000", "max_amount": "100000", "currency": "GBP"},
        "cv_summary": "Experienced backend engineer with 7 years of Python development across fintech and e-commerce. Led migration of microservices architecture at Revolut, processing 10M+ daily transactions. Strong PostgreSQL and cloud infrastructure skills.",
    },
    {
        "first_name": "Amara", "last_name": "Okafor", "location": "Manchester",
        "seniority": "mid", "availability": "1_month",
        "skills": [
            {"name": "Python", "years": 4, "confidence": 0.92},
            {"name": "Django", "years": 3, "confidence": 0.88},
            {"name": "PostgreSQL", "years": 3, "confidence": 0.85},
            {"name": "React", "years": 2, "confidence": 0.75},
            {"name": "Docker", "years": 2, "confidence": 0.8},
        ],
        "experience": [
            {"company": "Peak AI", "title": "Software Engineer", "duration_months": 24, "industry": "SaaS"},
            {"company": "BJSS", "title": "Junior Developer", "duration_months": 18, "industry": "consulting"},
        ],
        "industries": ["SaaS", "consulting"],
        "salary_expectation": {"min_amount": "55000", "max_amount": "65000", "currency": "GBP"},
        "cv_summary": "Full-stack engineer with strong Python and Django experience built at a Manchester AI startup. Comfortable across the stack with React frontend skills. Passionate about clean code and test-driven development.",
    },
    {
        "first_name": "Charlotte", "last_name": "Davies", "location": "London",
        "seniority": "lead", "availability": "3_months",
        "skills": [
            {"name": "Python", "years": 10, "confidence": 0.98},
            {"name": "Go", "years": 3, "confidence": 0.85},
            {"name": "Kubernetes", "years": 5, "confidence": 0.9},
            {"name": "AWS", "years": 8, "confidence": 0.95},
            {"name": "Terraform", "years": 4, "confidence": 0.88},
            {"name": "PostgreSQL", "years": 8, "confidence": 0.92},
            {"name": "Team Leadership", "years": 5, "confidence": 0.9},
        ],
        "experience": [
            {"company": "Wise", "title": "Engineering Lead", "duration_months": 36, "industry": "fintech"},
            {"company": "Skyscanner", "title": "Senior Engineer", "duration_months": 30, "industry": "travel"},
            {"company": "ThoughtWorks", "title": "Software Engineer", "duration_months": 24, "industry": "consulting"},
        ],
        "industries": ["fintech", "travel", "consulting"],
        "salary_expectation": {"min_amount": "120000", "max_amount": "140000", "currency": "GBP"},
        "cv_summary": "Engineering lead with 10+ years of experience spanning fintech and travel tech. Led a team of 8 engineers at Wise building international payment infrastructure. Deep expertise in distributed systems, cloud architecture, and platform engineering.",
    },
    # --- Data Engineering ---
    {
        "first_name": "Ravi", "last_name": "Patel", "location": "London",
        "seniority": "senior", "availability": "immediate",
        "skills": [
            {"name": "Python", "years": 6, "confidence": 0.93},
            {"name": "Apache Spark", "years": 4, "confidence": 0.88},
            {"name": "Airflow", "years": 3, "confidence": 0.85},
            {"name": "AWS", "years": 5, "confidence": 0.9},
            {"name": "SQL", "years": 7, "confidence": 0.95},
            {"name": "dbt", "years": 2, "confidence": 0.82},
        ],
        "experience": [
            {"company": "Monzo", "title": "Senior Data Engineer", "duration_months": 24, "industry": "fintech"},
            {"company": "BBC", "title": "Data Engineer", "duration_months": 30, "industry": "media"},
        ],
        "industries": ["fintech", "media"],
        "salary_expectation": {"min_amount": "90000", "max_amount": "105000", "currency": "GBP"},
        "cv_summary": "Senior data engineer with experience building real-time data platforms at Monzo. Proficient in Spark, Airflow, and modern data stack. Built the analytics pipeline serving 6M+ customer events daily.",
    },
    # --- Frontend / React ---
    {
        "first_name": "Emma", "last_name": "Wilson", "location": "Bristol",
        "seniority": "senior", "availability": "immediate",
        "skills": [
            {"name": "React", "years": 6, "confidence": 0.95},
            {"name": "TypeScript", "years": 5, "confidence": 0.92},
            {"name": "Next.js", "years": 3, "confidence": 0.88},
            {"name": "CSS", "years": 8, "confidence": 0.95},
            {"name": "GraphQL", "years": 3, "confidence": 0.82},
            {"name": "Testing Library", "years": 4, "confidence": 0.85},
        ],
        "experience": [
            {"company": "Onfido", "title": "Senior Frontend Engineer", "duration_months": 24, "industry": "fintech"},
            {"company": "Dyson", "title": "Frontend Developer", "duration_months": 30, "industry": "consumer-tech"},
        ],
        "industries": ["fintech", "consumer-tech"],
        "salary_expectation": {"min_amount": "75000", "max_amount": "90000", "currency": "GBP"},
        "cv_summary": "Senior frontend engineer specialising in React and TypeScript. Built Onfido's identity verification UI used by 10M+ end users. Passionate about accessibility and design systems.",
    },
    # --- DevOps / Platform ---
    {
        "first_name": "Liam", "last_name": "Murphy", "location": "Remote",
        "seniority": "senior", "availability": "1_month",
        "skills": [
            {"name": "Kubernetes", "years": 5, "confidence": 0.92},
            {"name": "Terraform", "years": 4, "confidence": 0.9},
            {"name": "AWS", "years": 7, "confidence": 0.95},
            {"name": "Docker", "years": 6, "confidence": 0.93},
            {"name": "Python", "years": 4, "confidence": 0.82},
            {"name": "CI/CD", "years": 5, "confidence": 0.88},
            {"name": "Prometheus", "years": 3, "confidence": 0.8},
        ],
        "experience": [
            {"company": "Snyk", "title": "Senior Platform Engineer", "duration_months": 24, "industry": "cybersecurity"},
            {"company": "FanDuel", "title": "DevOps Engineer", "duration_months": 30, "industry": "gaming"},
        ],
        "industries": ["cybersecurity", "gaming"],
        "salary_expectation": {"min_amount": "90000", "max_amount": "110000", "currency": "GBP"},
        "cv_summary": "Platform engineer with deep expertise in Kubernetes and AWS. Built and maintained production clusters serving 50K+ concurrent users at FanDuel. Advocates for infrastructure-as-code and GitOps workflows.",
    },
    # --- ML / AI ---
    {
        "first_name": "Sophia", "last_name": "Zhang", "location": "London",
        "seniority": "senior", "availability": "immediate",
        "skills": [
            {"name": "Python", "years": 6, "confidence": 0.95},
            {"name": "PyTorch", "years": 4, "confidence": 0.9},
            {"name": "Machine Learning", "years": 5, "confidence": 0.92},
            {"name": "NLP", "years": 3, "confidence": 0.88},
            {"name": "SQL", "years": 5, "confidence": 0.85},
            {"name": "MLflow", "years": 2, "confidence": 0.78},
        ],
        "experience": [
            {"company": "DeepMind", "title": "ML Engineer", "duration_months": 24, "industry": "AI"},
            {"company": "Babylon Health", "title": "Data Scientist", "duration_months": 30, "industry": "healthtech"},
        ],
        "industries": ["AI", "healthtech"],
        "salary_expectation": {"min_amount": "100000", "max_amount": "120000", "currency": "GBP"},
        "cv_summary": "ML engineer with experience at DeepMind and Babylon Health. Specialises in NLP and deployed production models serving clinical decision support for 2M+ consultations. Published researcher in medical NLP.",
    },
    # --- Product Management ---
    {
        "first_name": "Daniel", "last_name": "Brown", "location": "London",
        "seniority": "senior", "availability": "1_month",
        "skills": [
            {"name": "Product Strategy", "years": 6, "confidence": 0.92},
            {"name": "Agile", "years": 8, "confidence": 0.95},
            {"name": "SQL", "years": 4, "confidence": 0.78},
            {"name": "Data Analysis", "years": 5, "confidence": 0.82},
            {"name": "Stakeholder Management", "years": 7, "confidence": 0.9},
        ],
        "experience": [
            {"company": "Monzo", "title": "Senior Product Manager", "duration_months": 24, "industry": "fintech"},
            {"company": "Spotify", "title": "Product Manager", "duration_months": 30, "industry": "media"},
        ],
        "industries": ["fintech", "media"],
        "salary_expectation": {"min_amount": "90000", "max_amount": "110000", "currency": "GBP"},
        "cv_summary": "Senior product manager with 6 years of experience in consumer fintech. Led Monzo's savings product from 0 to 2M users. Strong quantitative skills with SQL proficiency. Experienced in cross-functional leadership.",
    },
]

# Additional candidates generated programmatically for 50+ total
ADDITIONAL_NAMES = [
    ("Hannah", "Taylor", "London"), ("Ben", "Walker", "Manchester"),
    ("Zara", "Khan", "Birmingham"), ("Jack", "Robinson", "Leeds"),
    ("Isla", "Campbell", "Edinburgh"), ("George", "Evans", "London"),
    ("Mia", "Roberts", "Bristol"), ("Oscar", "Hall", "Remote"),
    ("Grace", "Mitchell", "London"), ("Henry", "Carter", "Cambridge"),
    ("Freya", "Phillips", "London"), ("Ethan", "Cooper", "Manchester"),
    ("Lily", "Richardson", "London"), ("Noah", "Morgan", "Cardiff"),
    ("Aria", "James", "London"), ("Leo", "Watson", "Remote"),
    ("Ivy", "Brooks", "London"), ("Theo", "Bennett", "Brighton"),
    ("Ruby", "Gray", "London"), ("Archie", "Cook", "Glasgow"),
    ("Florence", "Price", "London"), ("Arthur", "Butler", "Oxford"),
    ("Willow", "Ross", "Manchester"), ("Alfie", "Howard", "London"),
    ("Poppy", "Ward", "London"), ("Charlie", "Peterson", "Remote"),
    ("Evie", "Morris", "London"), ("Harry", "King", "Liverpool"),
    ("Sienna", "Turner", "London"), ("Freddie", "Scott", "Edinburgh"),
    ("Millie", "Adams", "London"), ("Hugo", "Collins", "Reading"),
    ("Daisy", "Reed", "London"), ("Edward", "Harris", "Manchester"),
    ("Ella", "Thompson", "Birmingham"), ("Jasper", "White", "London"),
    ("Matilda", "Clark", "London"), ("Felix", "Lewis", "Remote"),
    ("Ava", "Young", "London"), ("Sebastian", "Allen", "Leeds"),
    ("Chloe", "Hill", "London"), ("Max", "Green", "Bristol"),
]

SKILL_POOLS = {
    "backend": [
        ("Python", 3, 8), ("Java", 2, 7), ("Go", 1, 5),
        ("Node.js", 2, 6), ("PostgreSQL", 2, 7), ("Redis", 1, 4),
        ("Docker", 1, 5), ("AWS", 2, 7), ("FastAPI", 1, 4),
        ("Django", 1, 5), ("Microservices", 2, 6),
    ],
    "frontend": [
        ("React", 2, 7), ("TypeScript", 2, 6), ("Next.js", 1, 4),
        ("Vue.js", 1, 5), ("CSS", 3, 8), ("GraphQL", 1, 4),
        ("JavaScript", 3, 8), ("Tailwind CSS", 1, 3),
    ],
    "data": [
        ("Python", 3, 7), ("SQL", 3, 8), ("Apache Spark", 1, 5),
        ("Airflow", 1, 4), ("dbt", 1, 3), ("Snowflake", 1, 3),
        ("AWS", 2, 6), ("Kafka", 1, 4),
    ],
    "devops": [
        ("Kubernetes", 2, 6), ("Terraform", 1, 5), ("AWS", 3, 8),
        ("Docker", 3, 7), ("CI/CD", 2, 5), ("Python", 1, 4),
        ("Linux", 3, 8), ("Prometheus", 1, 3),
    ],
    "ml": [
        ("Python", 3, 7), ("PyTorch", 1, 5), ("TensorFlow", 1, 5),
        ("Machine Learning", 2, 6), ("NLP", 1, 4), ("SQL", 2, 5),
        ("MLflow", 1, 3), ("Scikit-learn", 2, 5),
    ],
}


def generate_all_candidates(partner_ids: list[str]) -> list[dict]:
    """
    Generate 50+ candidates with realistic profiles.
    Combines hand-crafted templates with programmatically generated candidates.
    """
    candidates = []

    # Add hand-crafted templates
    for template in CANDIDATE_TEMPLATES:
        candidate = _build_candidate(
            template,
            created_by=random.choice(partner_ids),
        )
        candidates.append(candidate)

    # Generate additional candidates programmatically
    seniority_options = ["junior", "mid", "senior", "lead"]
    availability_options = ["immediate", "1_month", "3_months", "not_looking"]
    specialisation_options = ["backend", "frontend", "data", "devops", "ml"]

    for first, last, location in ADDITIONAL_NAMES:
        spec = random.choice(specialisation_options)
        seniority = random.choice(seniority_options)
        skills = _generate_skills(spec, seniority)
        experience = _generate_experience(spec, seniority)

        template = {
            "first_name": first,
            "last_name": last,
            "location": location,
            "seniority": seniority,
            "availability": random.choice(availability_options),
            "skills": skills,
            "experience": experience,
            "industries": random.sample(
                ["fintech", "healthtech", "SaaS", "e-commerce", "media", "consulting", "cybersecurity"],
                k=random.randint(1, 3),
            ),
            "salary_expectation": _generate_salary(seniority),
            "cv_summary": f"{first} {last} is a {seniority} {spec} specialist based in {location}.",
        }

        candidate = _build_candidate(template, created_by=random.choice(partner_ids))
        candidates.append(candidate)

    return candidates


def _build_candidate(template: dict, created_by: str) -> dict:
    """Build a full candidate record from a template."""
    now = datetime.utcnow()
    days_ago = random.randint(1, 60)
    created = now - timedelta(days=days_ago)

    return {
        "id": str(uuid4()),
        "first_name": template["first_name"],
        "last_name": template["last_name"],
        "email": f"{template['first_name'].lower()}.{template['last_name'].lower()}@email.com",
        "phone": f"+44 7{random.randint(100, 999)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
        "location": template["location"],
        "linkedin_url": f"https://linkedin.com/in/{template['first_name'].lower()}-{template['last_name'].lower()}",
        "skills": template["skills"],
        "experience": template["experience"],
        "seniority": template["seniority"],
        "salary_expectation": template.get("salary_expectation"),
        "availability": template["availability"],
        "industries": template["industries"],
        "cv_text": template.get("cv_summary", ""),
        "profile_text": None,
        "sources": [{"adapter_name": "manual", "external_id": str(uuid4()), "ingested_at": created.isoformat()}],
        "dedup_group": None,
        "dedup_confidence": None,
        "embedding": None,  # Generated by pipeline
        "extraction_confidence": round(random.uniform(0.75, 0.98), 2),
        "extraction_flags": [],
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
        "created_by": created_by,
    }


def _generate_skills(specialisation: str, seniority: str) -> list[dict]:
    pool = SKILL_POOLS.get(specialisation, SKILL_POOLS["backend"])
    num_skills = {"junior": 3, "mid": 4, "senior": 5, "lead": 6}.get(seniority, 4)
    selected = random.sample(pool, k=min(num_skills, len(pool)))

    return [
        {
            "name": name,
            "years": random.randint(min_y, max_y),
            "confidence": round(random.uniform(0.75, 0.98), 2),
        }
        for name, min_y, max_y in selected
    ]


def _generate_experience(specialisation: str, seniority: str) -> list[dict]:
    companies = [
        "Revolut", "Deliveroo", "Just Eat", "Cazoo", "Gymshark",
        "Depop", "Bulb", "GoCardless", "Funding Circle", "Zopa",
        "Habito", "Eigen Technologies", "Faculty AI", "Immersive Labs",
        "Cleo", "Freetrade", "OakNorth", "Bought By Many",
    ]
    titles_map = {
        "backend": ["Backend Engineer", "Software Engineer", "Python Developer", "API Engineer"],
        "frontend": ["Frontend Engineer", "UI Developer", "React Developer", "Frontend Architect"],
        "data": ["Data Engineer", "Analytics Engineer", "Data Platform Engineer"],
        "devops": ["Platform Engineer", "DevOps Engineer", "SRE", "Infrastructure Engineer"],
        "ml": ["ML Engineer", "Data Scientist", "AI Engineer", "Research Engineer"],
    }
    titles = titles_map.get(specialisation, titles_map["backend"])
    num_roles = {"junior": 1, "mid": 2, "senior": 3, "lead": 3}.get(seniority, 2)

    experience = []
    for i in range(num_roles):
        title = random.choice(titles)
        if i == 0 and seniority in ("senior", "lead"):
            title = f"Senior {title}" if seniority == "senior" else f"Lead {title}"
        experience.append({
            "company": random.choice(companies),
            "title": title,
            "duration_months": random.randint(12, 42),
            "industry": random.choice(["fintech", "SaaS", "e-commerce", "healthtech"]),
        })

    return experience


def _generate_salary(seniority: str) -> dict:
    ranges = {
        "junior": (30000, 45000),
        "mid": (50000, 70000),
        "senior": (75000, 100000),
        "lead": (100000, 140000),
    }
    min_s, max_s = ranges.get(seniority, (50000, 70000))
    return {
        "min_amount": str(random.randint(min_s, min_s + 10000)),
        "max_amount": str(random.randint(max_s - 10000, max_s)),
        "currency": "GBP",
    }
```

### Roles (`backend/seed/roles.py`)

```python
from uuid import uuid4
from datetime import datetime, timedelta
import random


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
            "embedding": None,  # Generated by pipeline
            "extraction_confidence": round(random.uniform(0.85, 0.98), 2),
            "status": "active",
            "created_at": created.isoformat(),
            "created_by": random.choice(client_ids),
        })

    return results
```

### Master Seed Orchestrator (`backend/seed/generate.py`)

```python
"""
Master seed data generation script.

Usage:
    python -m backend.seed.generate

Generates all seed data, runs the extraction + matching pipeline,
and outputs supabase/seed.sql.
"""

import asyncio
import json
import random
from uuid import uuid4
from datetime import datetime, timedelta

from backend.seed.organisations import ORGANISATIONS
from backend.seed.users import get_demo_users
from backend.seed.candidates import generate_all_candidates
from backend.seed.roles import generate_roles
from backend.config import settings


async def generate_seed_data():
    """Generate all seed data and output SQL."""
    print("=== RecruitTech Seed Data Generator ===\n")

    # 1. Organisations
    print(f"Generating {len(ORGANISATIONS)} organisations...")
    org_ids = {org["name"]: org["id"] for org in ORGANISATIONS}

    # 2. Users
    users = get_demo_users(org_ids)
    print(f"Generating {len(users)} demo users...")
    partner_ids = [u["id"] for u in users if u["role"] == "talent_partner"]
    client_ids = [u["id"] for u in users if u["role"] == "client"]

    # 3. Candidates
    candidates = generate_all_candidates(partner_ids)
    print(f"Generating {len(candidates)} candidates...")

    # 4. Roles
    roles = generate_roles(org_ids, client_ids)
    print(f"Generating {len(roles)} roles...")

    # 5. Collections
    collections = _generate_collections(candidates, partner_ids)
    print(f"Generating {len(collections)} collections...")

    # 6. Handoffs
    handoffs = _generate_handoffs(candidates, partner_ids, roles)
    print(f"Generating {len(handoffs)} handoffs...")

    # 7. Quotes
    quotes = _generate_quotes(candidates, roles, client_ids)
    print(f"Generating {len(quotes)} quotes...")

    # 8. Signals
    signals = _generate_signal_history(users, candidates, roles)
    print(f"Generating {len(signals)} signals...")

    # 9. Dedup queue items
    dedup_items = _generate_dedup_queue(candidates)
    print(f"Generating {len(dedup_items)} dedup queue items...")

    # 10. Write SQL
    _write_seed_sql(
        organisations=ORGANISATIONS,
        users=users,
        candidates=candidates,
        roles=roles,
        collections=collections,
        handoffs=handoffs,
        quotes=quotes,
        signals=signals,
        dedup_items=dedup_items,
    )

    print("\n=== Seed data written to supabase/seed.sql ===")
    print(f"  Organisations: {len(ORGANISATIONS)}")
    print(f"  Users: {len(users)}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Roles: {len(roles)}")
    print(f"  Collections: {len(collections)}")
    print(f"  Handoffs: {len(handoffs)}")
    print(f"  Quotes: {len(quotes)}")
    print(f"  Signals: {len(signals)}")


def _generate_collections(candidates, partner_ids):
    """Generate themed collections."""
    collections = []
    themes = [
        ("Senior Backend — London", ["backend", "london", "senior"], "senior", "London"),
        ("ML Engineers — Remote OK", ["ml", "ai", "remote"], None, "Remote"),
        ("Fintech Specialists", ["fintech", "finance"], None, None),
        ("Available Now", ["immediate", "available"], None, None),
        ("React Frontend Experts", ["react", "frontend", "typescript"], None, None),
        ("Data Engineering Talent", ["data", "sql", "spark"], None, None),
    ]

    for name, tags, seniority_filter, location_filter in themes:
        cid_pool = []
        for c in candidates:
            if seniority_filter and c.get("seniority") != seniority_filter:
                continue
            if location_filter and location_filter.lower() not in (c.get("location") or "").lower():
                continue
            cid_pool.append(c["id"])

        selected = random.sample(cid_pool, k=min(random.randint(5, 12), len(cid_pool)))

        collection_id = str(uuid4())
        collections.append({
            "id": collection_id,
            "name": name,
            "description": f"Curated collection: {name}",
            "owner_id": random.choice(partner_ids),
            "visibility": random.choice(["private", "shared_all", "shared_specific"]),
            "shared_with": random.sample(partner_ids, k=random.randint(1, 2)) if random.random() > 0.5 else None,
            "tags": tags,
            "candidate_ids": selected,
            "candidate_count": len(selected),
            "avg_match_score": round(random.uniform(0.5, 0.85), 2),
            "available_now_count": random.randint(1, min(5, len(selected))),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 20))).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

    return collections


def _generate_handoffs(candidates, partner_ids, roles):
    """Generate 10+ handoffs between partners."""
    handoffs = []
    statuses = ["pending", "accepted", "declined", "pending", "accepted"]

    for i in range(12):
        from_id = random.choice(partner_ids)
        to_id = random.choice([p for p in partner_ids if p != from_id])
        selected_candidates = random.sample(
            [c["id"] for c in candidates],
            k=random.randint(1, 4),
        )
        status = statuses[i % len(statuses)]
        created = datetime.utcnow() - timedelta(days=random.randint(1, 14))

        handoffs.append({
            "id": str(uuid4()),
            "from_partner_id": from_id,
            "to_partner_id": to_id,
            "candidate_ids": selected_candidates,
            "context_notes": random.choice([
                "Strong Python candidates for your fintech roles",
                "These ML engineers might be a good fit",
                "Recommended for the backend position",
                "Experienced candidates looking for new opportunities",
                "Great cultural fit for your team",
            ]),
            "target_role_id": random.choice([r["id"] for r in roles]) if random.random() > 0.3 else None,
            "status": status,
            "response_notes": "Looks great, thanks!" if status == "accepted" else ("Not quite the right fit" if status == "declined" else None),
            "attribution_id": str(uuid4()),
            "created_at": created.isoformat(),
            "responded_at": (created + timedelta(hours=random.randint(1, 48))).isoformat() if status != "pending" else None,
        })

    return handoffs


def _generate_quotes(candidates, roles, client_ids):
    """Generate 15+ quotes with various statuses."""
    quotes = []
    fee_map = {"junior": 8000, "mid": 12000, "senior": 18000, "lead": 25000, "principal": 35000}

    for i in range(18):
        role = random.choice(roles)
        candidate = random.choice(candidates)
        seniority = role.get("seniority", "mid")
        base_fee = fee_map.get(seniority, 12000)
        is_pool = random.random() > 0.5
        discount = int(base_fee * 0.20) if is_pool else 0
        final_fee = base_fee - discount
        status = random.choice(["generated", "sent", "accepted", "declined", "expired"])
        created = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        quotes.append({
            "id": str(uuid4()),
            "client_id": random.choice(client_ids),
            "candidate_id": candidate["id"],
            "role_id": role["id"],
            "is_pool_candidate": is_pool,
            "base_fee": str(base_fee),
            "pool_discount": str(discount) if is_pool else None,
            "final_fee": str(final_fee),
            "fee_breakdown": {
                "summary": f"Placement fee for {role['title']}",
                "seniority_level": seniority,
                "base_fee": {"amount": str(base_fee), "currency": "GBP"},
                "final_fee": {"amount": str(final_fee), "currency": "GBP"},
            },
            "status": status,
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(days=14)).isoformat(),
        })

    return quotes


def _generate_signal_history(users, candidates, roles):
    """Generate signal history for populated analytics dashboards."""
    signals = []
    now = datetime.utcnow()

    partner_users = [u for u in users if u["role"] == "talent_partner"]
    client_users = [u for u in users if u["role"] == "client"]

    # Spread signals over 30 days
    for day_offset in range(30):
        day = now - timedelta(days=day_offset)
        daily_count = random.randint(15, 40)

        for _ in range(daily_count):
            hour = random.randint(8, 18)
            minute = random.randint(0, 59)
            timestamp = day.replace(hour=hour, minute=minute)

            event_type = random.choice([
                "candidate_ingested", "candidate_viewed", "candidate_viewed",
                "candidate_shortlisted", "candidate_dismissed",
                "match_generated", "match_generated", "match_generated",
                "intro_requested", "handoff_sent", "handoff_accepted",
                "quote_generated", "copilot_query",
            ])

            if event_type in ("candidate_ingested", "candidate_viewed", "candidate_shortlisted",
                             "candidate_dismissed", "handoff_sent", "handoff_accepted", "copilot_query"):
                actor = random.choice(partner_users)
            else:
                actor = random.choice(client_users + partner_users)

            entity_type = "candidate" if "candidate" in event_type else (
                "match" if "match" in event_type else (
                    "handoff" if "handoff" in event_type else (
                        "quote" if "quote" in event_type else "copilot"
                    )
                )
            )

            signals.append({
                "id": str(uuid4()),
                "event_type": event_type,
                "actor_id": actor["id"],
                "actor_role": actor["role"],
                "entity_type": entity_type,
                "entity_id": random.choice(candidates)["id"],
                "metadata": {},
                "created_at": timestamp.isoformat(),
            })

    # Add a few placements
    for _ in range(5):
        signals.append({
            "id": str(uuid4()),
            "event_type": "placement_made",
            "actor_id": users[-1]["id"],  # admin
            "actor_role": "admin",
            "entity_type": "candidate",
            "entity_id": random.choice(candidates)["id"],
            "metadata": {"final_fee": str(random.randint(12000, 35000))},
            "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
        })

    return signals


def _generate_dedup_queue(candidates):
    """Generate dedup queue items for admin review."""
    items = []
    for i in range(8):
        a, b = random.sample(candidates, 2)
        items.append({
            "id": str(uuid4()),
            "candidate_a_id": a["id"],
            "candidate_b_id": b["id"],
            "match_type": random.choice(["fuzzy_name", "semantic", "fuzzy_name"]),
            "confidence": round(random.uniform(0.6, 0.89), 2),
            "status": "pending",
            "resolved_by": None,
            "resolved_at": None,
            "resolution_notes": None,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat(),
        })
    return items


def _write_seed_sql(
    organisations, users, candidates, roles,
    collections, handoffs, quotes, signals, dedup_items
):
    """Write all seed data as a SQL file."""
    lines = [
        "-- RecruitTech Seed Data",
        "-- Generated by backend/seed/generate.py",
        f"-- Generated at: {datetime.utcnow().isoformat()}",
        "",
        "BEGIN;",
        "",
    ]

    # Organisations
    lines.append("-- Organisations")
    for org in organisations:
        lines.append(
            f"INSERT INTO organisations (id, name, industry, location, description, size) "
            f"VALUES ('{org['id']}', {_sql_str(org['name'])}, {_sql_str(org['industry'])}, "
            f"{_sql_str(org['location'])}, {_sql_str(org['description'])}, {_sql_str(org['size'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Users
    lines.append("-- Users")
    for u in users:
        lines.append(
            f"INSERT INTO users (id, email, first_name, last_name, role, organisation_id, is_active, created_at) "
            f"VALUES ('{u['id']}', {_sql_str(u['email'])}, {_sql_str(u['first_name'])}, "
            f"{_sql_str(u['last_name'])}, {_sql_str(u['role'])}, "
            f"{'NULL' if not u.get('organisation_id') else _sql_str(u['organisation_id'])}, "
            f"{u['is_active']}, now()) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Candidates
    lines.append("-- Candidates")
    for c in candidates:
        lines.append(
            f"INSERT INTO candidates (id, first_name, last_name, email, phone, location, linkedin_url, "
            f"skills, experience, seniority, salary_expectation, availability, industries, "
            f"cv_text, sources, extraction_confidence, extraction_flags, created_at, updated_at, created_by) "
            f"VALUES ('{c['id']}', {_sql_str(c['first_name'])}, {_sql_str(c['last_name'])}, "
            f"{_sql_str(c.get('email'))}, {_sql_str(c.get('phone'))}, {_sql_str(c.get('location'))}, "
            f"{_sql_str(c.get('linkedin_url'))}, "
            f"{_sql_json(c.get('skills', []))}, {_sql_json(c.get('experience', []))}, "
            f"{_sql_str(c.get('seniority'))}, {_sql_json(c.get('salary_expectation'))}, "
            f"{_sql_str(c.get('availability'))}, {_sql_array(c.get('industries', []))}, "
            f"{_sql_str(c.get('cv_text'))}, {_sql_json(c.get('sources', []))}, "
            f"{c.get('extraction_confidence', 0.8)}, {_sql_array(c.get('extraction_flags', []))}, "
            f"{_sql_str(c['created_at'])}, {_sql_str(c['updated_at'])}, '{c['created_by']}') "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Roles
    lines.append("-- Roles")
    for r in roles:
        lines.append(
            f"INSERT INTO roles (id, title, description, organisation_id, required_skills, preferred_skills, "
            f"seniority, salary_band, location, remote_policy, industry, extraction_confidence, status, "
            f"created_at, created_by) "
            f"VALUES ('{r['id']}', {_sql_str(r['title'])}, {_sql_str(r['description'])}, "
            f"{_sql_str(r.get('organisation_id'))}, {_sql_json(r.get('required_skills', []))}, "
            f"{_sql_json(r.get('preferred_skills', []))}, {_sql_str(r.get('seniority'))}, "
            f"{_sql_json(r.get('salary_band'))}, {_sql_str(r.get('location'))}, "
            f"{_sql_str(r.get('remote_policy'))}, {_sql_str(r.get('industry'))}, "
            f"{r.get('extraction_confidence', 0.9)}, {_sql_str(r.get('status', 'active'))}, "
            f"{_sql_str(r['created_at'])}, '{r['created_by']}') "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Collections
    lines.append("-- Collections")
    for c in collections:
        lines.append(
            f"INSERT INTO collections (id, name, description, owner_id, visibility, shared_with, tags, "
            f"candidate_count, avg_match_score, available_now_count, created_at, updated_at) "
            f"VALUES ('{c['id']}', {_sql_str(c['name'])}, {_sql_str(c.get('description'))}, "
            f"'{c['owner_id']}', {_sql_str(c['visibility'])}, "
            f"{_sql_array(c.get('shared_with')) if c.get('shared_with') else 'NULL'}, "
            f"{_sql_array(c['tags'])}, {c['candidate_count']}, "
            f"{c.get('avg_match_score') or 'NULL'}, {c['available_now_count']}, "
            f"{_sql_str(c['created_at'])}, {_sql_str(c['updated_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
        # Junction table entries
        for cid in c.get("candidate_ids", []):
            lines.append(
                f"INSERT INTO collection_candidates (collection_id, candidate_id) "
                f"VALUES ('{c['id']}', '{cid}') ON CONFLICT DO NOTHING;"
            )
    lines.append("")

    # Handoffs
    lines.append("-- Handoffs")
    for h in handoffs:
        lines.append(
            f"INSERT INTO handoffs (id, from_partner_id, to_partner_id, candidate_ids, context_notes, "
            f"target_role_id, status, response_notes, attribution_id, created_at, responded_at) "
            f"VALUES ('{h['id']}', '{h['from_partner_id']}', '{h['to_partner_id']}', "
            f"{_sql_array(h['candidate_ids'])}, {_sql_str(h['context_notes'])}, "
            f"{_sql_str(h.get('target_role_id'))}, {_sql_str(h['status'])}, "
            f"{_sql_str(h.get('response_notes'))}, '{h['attribution_id']}', "
            f"{_sql_str(h['created_at'])}, {_sql_str(h.get('responded_at'))}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Quotes
    lines.append("-- Quotes")
    for q in quotes:
        lines.append(
            f"INSERT INTO quotes (id, client_id, candidate_id, role_id, is_pool_candidate, "
            f"base_fee, pool_discount, final_fee, fee_breakdown, status, created_at, expires_at) "
            f"VALUES ('{q['id']}', '{q['client_id']}', '{q['candidate_id']}', '{q['role_id']}', "
            f"{q['is_pool_candidate']}, {q['base_fee']}, "
            f"{q.get('pool_discount') or 'NULL'}, {q['final_fee']}, "
            f"{_sql_json(q['fee_breakdown'])}, {_sql_str(q['status'])}, "
            f"{_sql_str(q['created_at'])}, {_sql_str(q['expires_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Signals
    lines.append("-- Signals")
    for s in signals:
        lines.append(
            f"INSERT INTO signals (id, event_type, actor_id, actor_role, entity_type, entity_id, "
            f"metadata, created_at) "
            f"VALUES ('{s['id']}', {_sql_str(s['event_type'])}, '{s['actor_id']}', "
            f"{_sql_str(s['actor_role'])}, {_sql_str(s['entity_type'])}, '{s['entity_id']}', "
            f"{_sql_json(s.get('metadata', {}))}, {_sql_str(s['created_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Dedup queue
    lines.append("-- Dedup Queue")
    for d in dedup_items:
        lines.append(
            f"INSERT INTO dedup_queue (id, candidate_a_id, candidate_b_id, match_type, confidence, "
            f"status, created_at) "
            f"VALUES ('{d['id']}', '{d['candidate_a_id']}', '{d['candidate_b_id']}', "
            f"{_sql_str(d['match_type'])}, {d['confidence']}, {_sql_str(d['status'])}, "
            f"{_sql_str(d['created_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )

    lines.extend(["", "COMMIT;", ""])

    with open("supabase/seed.sql", "w") as f:
        f.write("\n".join(lines))


def _sql_str(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _sql_json(value) -> str:
    if value is None:
        return "NULL"
    return "'" + json.dumps(value).replace("'", "''") + "'::jsonb"


def _sql_array(value) -> str:
    if value is None or len(value) == 0:
        return "ARRAY[]::text[]"
    items = ", ".join(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" for v in value)
    return f"ARRAY[{items}]"


if __name__ == "__main__":
    asyncio.run(generate_seed_data())
```

### Integration Tests (`backend/tests/test_integration.py`)

```python
"""
Integration tests that verify end-to-end flows across all endpoints.
Run with: python -m pytest tests/test_integration.py -v
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing."""
    return {"Authorization": "Bearer test-token"}


class TestHealthAndBootstrap:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestCandidateFlow:
    def test_create_candidate(self, client, auth_headers):
        response = client.post("/api/candidates/", json={
            "first_name": "Test",
            "last_name": "Candidate",
            "email": "test@example.com",
            "location": "London",
        }, headers=auth_headers)
        assert response.status_code in (200, 201)

    def test_list_candidates(self, client, auth_headers):
        response = client.get("/api/candidates/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_candidates(self, client, auth_headers):
        response = client.get(
            "/api/candidates/?location=London&seniority=senior",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestRoleFlow:
    def test_create_role(self, client, auth_headers):
        response = client.post("/api/roles/", json={
            "title": "Senior Backend Engineer",
            "description": "Python backend role in fintech",
            "organisation_id": str(uuid4()),
        }, headers=auth_headers)
        assert response.status_code in (200, 201)

    def test_list_roles(self, client, auth_headers):
        response = client.get("/api/roles/", headers=auth_headers)
        assert response.status_code == 200


class TestMatchFlow:
    def test_matches_by_role(self, client, auth_headers):
        response = client.get(
            f"/api/matches/by-role/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestCollectionFlow:
    def test_create_collection(self, client, auth_headers):
        response = client.post("/api/collections/", json={
            "name": "Test Collection",
            "tags": ["test"],
        }, headers=auth_headers)
        assert response.status_code in (200, 201)

    def test_list_collections(self, client, auth_headers):
        response = client.get("/api/collections/", headers=auth_headers)
        assert response.status_code == 200


class TestCopilotFlow:
    def test_copilot_query(self, client, auth_headers):
        response = client.post("/api/copilot/query", json={
            "query": "Find Python developers in London",
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "interpretation" in data
        assert "results" in data


class TestSignalFlow:
    def test_recent_signals(self, client, auth_headers):
        response = client.get("/api/signals/recent", headers=auth_headers)
        assert response.status_code == 200

    def test_funnel_analytics(self, client, auth_headers):
        response = client.get("/api/signals/analytics/funnel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data


class TestAdminFlow:
    def test_platform_stats(self, client, auth_headers):
        response = client.get("/api/admin/stats", headers=auth_headers)
        # May be 403 if not admin — that is also correct behaviour
        assert response.status_code in (200, 403)

    def test_adapter_health(self, client, auth_headers):
        response = client.get("/api/admin/adapters/health", headers=auth_headers)
        assert response.status_code in (200, 403)
```

## Outputs
- `backend/seed/__init__.py`
- `backend/seed/organisations.py`
- `backend/seed/users.py`
- `backend/seed/candidates.py`
- `backend/seed/roles.py`
- `backend/seed/generate.py`
- `supabase/seed.sql` (generated)
- `backend/tests/test_integration.py`

## Acceptance Criteria
1. `python -m backend.seed.generate` produces `supabase/seed.sql` without errors
2. Seed SQL loads into Supabase without errors: `psql < supabase/seed.sql`
3. At least 50 candidates with realistic UK names, locations, skills, and experience
4. At least 15 roles across fintech, healthtech, SaaS, and e-commerce
5. At least 12 organisations with real UK tech company names
6. 9 demo users: 5 talent partners, 3 clients, 1 admin with stable UUIDs
7. 6+ collections with candidate assignments
8. 12+ handoffs with mixed statuses (pending, accepted, declined)
9. 18+ quotes with mixed statuses and correct fee calculations
10. 600+ signal events spread across 30 days for populated analytics
11. 8+ dedup queue items pending review
12. Integration tests pass: `python -m pytest tests/test_integration.py -v`
13. Data feels realistic enough for a recruitment professional to recognise

## Handoff Notes
- **To Agent B:** Demo users have stable UUIDs for the login page: partners are `11111111-1111-1111-1111-{111..555}`, clients are `22222222-2222-2222-2222-{111..333}`, admin is `33333333-3333-3333-3333-111111111111`. Passwords follow the pattern `demo-partner-N`, `demo-client-N`, `demo-admin-1`. Seed data includes pre-populated analytics, handoffs, collections, and quotes — dashboards will have data from day one.
- **Decision:** Seed data uses real UK tech company names (Monzo, Starling, Wise, etc.) and realistic salary ranges for the UK market. Embeddings and matches are NOT pre-generated in the SQL (they require running the AI pipeline). The seed script populates raw data; run `python -m backend.seed.generate` first, load the SQL, then run the extraction and matching pipeline separately to generate embeddings and matches.
