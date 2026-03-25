import random
from datetime import datetime, timedelta
from uuid import uuid4

# Candidate templates — hand-crafted with full UK market detail
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
    # Batch 1 — original 42
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
    # Batch 2 — 50 more UK names
    ("Imogen", "Patel", "London"), ("Callum", "Murray", "Edinburgh"),
    ("Olivia", "Shaw", "London"), ("Liam", "Barrett", "Manchester"),
    ("Sophie", "Henderson", "Bristol"), ("James", "Fox", "London"),
    ("Emily", "Dixon", "Leeds"), ("Daniel", "Graham", "Remote"),
    ("Jessica", "Spencer", "London"), ("Ryan", "Lawrence", "Birmingham"),
    ("Abigail", "Russell", "London"), ("Connor", "Palmer", "Glasgow"),
    ("Isabelle", "Stevens", "London"), ("Nathan", "Gordon", "Cambridge"),
    ("Amy", "Marshall", "London"), ("Sam", "Crawford", "Manchester"),
    ("Laura", "Ellis", "Remote"), ("Tom", "Stone", "London"),
    ("Rachel", "Webb", "London"), ("Luke", "Griffiths", "Cardiff"),
    ("Victoria", "Pearce", "London"), ("Adam", "Fleming", "Edinburgh"),
    ("Rebecca", "Arnold", "London"), ("Chris", "Mason", "Brighton"),
    ("Natasha", "Hunt", "London"), ("Matt", "Burke", "Manchester"),
    ("Sarah", "Payne", "Remote"), ("Joe", "Hart", "London"),
    ("Katie", "Carr", "London"), ("Jamie", "Fisher", "Liverpool"),
    ("Holly", "Knight", "London"), ("Alex", "Simpson", "Oxford"),
    ("Lucy", "Barker", "London"), ("Rob", "Chambers", "Remote"),
    ("Emma", "Willis", "London"), ("Jake", "Ferguson", "Manchester"),
    ("Hannah", "Watts", "Bristol"), ("Mark", "Douglas", "London"),
    ("Leah", "Sutton", "London"), ("Peter", "Black", "Edinburgh"),
    ("Molly", "Chapman", "London"), ("Will", "Grant", "Leeds"),
    ("Ellie", "Boyd", "London"), ("Dom", "Reeves", "Remote"),
    ("Beth", "Harper", "London"), ("Tim", "Day", "Manchester"),
    ("Anna", "Burns", "London"), ("Paul", "Holland", "Birmingham"),
    ("Phoebe", "Gibson", "London"), ("Nick", "Stephens", "Glasgow"),
    # Batch 3 — 50 more diverse UK names
    ("Priya", "Gupta", "London"), ("Ollie", "Watts", "Manchester"),
    ("Aisha", "Mohammed", "Birmingham"), ("Rhys", "Williams", "Cardiff"),
    ("Fatima", "Ali", "London"), ("Finn", "O'Brien", "Remote"),
    ("Sana", "Hussain", "London"), ("Kieran", "Murphy", "Edinburgh"),
    ("Maya", "Singh", "London"), ("Declan", "Kelly", "Leeds"),
    ("Amina", "Hassan", "London"), ("Dylan", "Byrne", "Manchester"),
    ("Riya", "Desai", "London"), ("Owen", "Rees", "Bristol"),
    ("Nadia", "Rahman", "London"), ("Caleb", "Chapman", "Remote"),
    ("Ananya", "Reddy", "London"), ("Josh", "Doyle", "Glasgow"),
    ("Layla", "Ahmad", "London"), ("Aiden", "Walsh", "Liverpool"),
    ("Meera", "Joshi", "London"), ("Kyle", "Duffy", "Manchester"),
    ("Isha", "Kapoor", "Remote"), ("Ross", "Gallagher", "Edinburgh"),
    ("Neha", "Bhat", "London"), ("Aaron", "Lynch", "Birmingham"),
    ("Tanvi", "Mehta", "London"), ("Craig", "Doherty", "Leeds"),
    ("Diya", "Nair", "London"), ("Lewis", "Quinn", "Bristol"),
    ("Kavya", "Iyer", "London"), ("Stuart", "Ryan", "Remote"),
    ("Simran", "Gill", "London"), ("Jack", "Neill", "Manchester"),
    ("Alisha", "Chowdhury", "London"), ("Marcus", "Lawson", "Cambridge"),
    ("Tanya", "Mishra", "London"), ("Eoin", "Collins", "Edinburgh"),
    ("Nikita", "Verma", "Remote"), ("Cameron", "Fraser", "Glasgow"),
    ("Shreya", "Agarwal", "London"), ("Luca", "Romano", "London"),
    ("Pooja", "Saxena", "London"), ("Jay", "Brennan", "Manchester"),
    ("Aditi", "Rao", "London"), ("Conor", "Fitzgerald", "Birmingham"),
    ("Zainab", "Mirza", "London"), ("Patrick", "Nolan", "Leeds"),
    ("Divya", "Sharma", "London"), ("Sean", "Maguire", "Remote"),
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
