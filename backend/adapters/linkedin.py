from datetime import datetime

from .base import AdapterCandidate, AdapterRole, AdapterStatus, BaseAdapter


class LinkedInAdapter(BaseAdapter):
    """Mock LinkedIn Recruiter adapter.

    LinkedIn is a professional network — rich in:
    - Skills with endorsement counts
    - Headline and summary
    - Education details
    - Connections and recommendations
    - Less granular work history dates, more skills/social proof
    """

    name = "linkedin"
    display_name = "LinkedIn Recruiter"
    adapter_type = "social"

    MOCK_CANDIDATES = [
        {
            "profileId": "LI-3001",
            "headline": "Senior Backend Engineer at Revolut | Python, FastAPI, Distributed Systems",
            "firstName": "James",
            "lastName": "Hartley",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/jameshartley-dev",
            "summary": "Passionate about building scalable financial infrastructure. 8 years in backend engineering, last 3 in fintech. I love solving hard problems at the intersection of reliability and speed.",
            "skills": [
                {"name": "Python", "endorsements": 42},
                {"name": "FastAPI", "endorsements": 18},
                {"name": "PostgreSQL", "endorsements": 35},
                {"name": "Distributed Systems", "endorsements": 28},
                {"name": "Docker", "endorsements": 31},
                {"name": "AWS", "endorsements": 25},
                {"name": "Redis", "endorsements": 20},
                {"name": "Kafka", "endorsements": 15},
            ],
            "positions": [
                {"company": "Revolut", "title": "Senior Backend Engineer", "isCurrent": True},
                {"company": "Monzo", "title": "Backend Engineer", "isCurrent": False},
                {"company": "ThoughtWorks", "title": "Software Consultant", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Edinburgh", "degree": "BSc Computer Science", "year": 2016},
            ],
            "connectionsCount": 1250,
            "recommendationsCount": 8,
        },
        {
            "profileId": "LI-3002",
            "headline": "Data Platform Lead | Building next-gen data infrastructure",
            "firstName": "Ben",
            "lastName": "Cooper",
            "email": "ben.cooper.dev@outlook.com",
            "location": "Bristol, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/bencooper-data",
            "summary": "Data engineer turned platform lead. Built data platforms at OVO Energy from zero to processing 2B events/month. Passionate about clean data, real-time streaming, and enabling data-driven decisions.",
            "skills": [
                {"name": "Apache Spark", "endorsements": 38},
                {"name": "Kafka", "endorsements": 30},
                {"name": "Python", "endorsements": 45},
                {"name": "dbt", "endorsements": 22},
                {"name": "Snowflake", "endorsements": 25},
                {"name": "Airflow", "endorsements": 28},
                {"name": "AWS", "endorsements": 20},
                {"name": "Data Modeling", "endorsements": 15},
            ],
            "positions": [
                {"company": "OVO Energy", "title": "Lead Data Engineer", "isCurrent": True},
                {"company": "Just Eat", "title": "Senior Data Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Bath", "degree": "MEng Computer Science", "year": 2017},
            ],
            "connectionsCount": 980,
            "recommendationsCount": 6,
        },
        {
            "profileId": "LI-3003",
            "headline": "Staff Engineer at Thought Machine | Distributed Systems, Go, Cloud Native",
            "firstName": "Rachel",
            "lastName": "Stewart",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/rachelstewart-eng",
            "summary": "10+ years building distributed systems. Currently designing core banking infrastructure used by 20+ banks globally. Believer in remote-first engineering culture and technical excellence.",
            "skills": [
                {"name": "Go", "endorsements": 55},
                {"name": "Kubernetes", "endorsements": 48},
                {"name": "Distributed Systems", "endorsements": 52},
                {"name": "gRPC", "endorsements": 30},
                {"name": "PostgreSQL", "endorsements": 35},
                {"name": "Terraform", "endorsements": 28},
                {"name": "System Design", "endorsements": 40},
            ],
            "positions": [
                {"company": "Thought Machine", "title": "Staff Software Engineer", "isCurrent": True},
                {"company": "Google", "title": "Senior Software Engineer", "isCurrent": False},
                {"company": "Palantir", "title": "Software Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "Imperial College London", "degree": "MEng Computing", "year": 2014},
            ],
            "connectionsCount": 2100,
            "recommendationsCount": 14,
        },
        {
            "profileId": "LI-3004",
            "headline": "ML Engineer | NLP, LLMs, RAG | Making AI practical",
            "firstName": "Mohammed",
            "lastName": "Hassan",
            "email": "mohammed.hassan.tech@gmail.com",
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/mohassan-ml",
            "summary": "Applied ML engineer focused on making LLMs useful in production. Building document understanding systems processing 100K+ documents. Previously at Faculty AI working on government and enterprise AI.",
            "skills": [
                {"name": "Python", "endorsements": 40},
                {"name": "Machine Learning", "endorsements": 35},
                {"name": "NLP", "endorsements": 32},
                {"name": "LLMs", "endorsements": 20},
                {"name": "PyTorch", "endorsements": 28},
                {"name": "LangChain", "endorsements": 12},
                {"name": "RAG", "endorsements": 8},
                {"name": "Vector Databases", "endorsements": 10},
            ],
            "positions": [
                {"company": "Eigen Technologies", "title": "ML Engineer", "isCurrent": True},
                {"company": "Faculty AI", "title": "Data Scientist", "isCurrent": False},
            ],
            "education": [
                {"school": "UCL", "degree": "MSc Machine Learning", "year": 2020},
                {"school": "University of Manchester", "degree": "BSc Mathematics", "year": 2018},
            ],
            "connectionsCount": 850,
            "recommendationsCount": 5,
        },
        {
            "profileId": "LI-3005",
            "headline": "Principal ML Engineer at DeepMind | NeurIPS, ICML published",
            "firstName": "Mei",
            "lastName": "Zhang",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/meizhang-ml",
            "summary": "Research scientist transitioning to applied ML leadership. Published at NeurIPS, ICML, EMNLP. Expert in NLP and recommendation systems. Looking for product-focused ML roles where research meets real users.",
            "skills": [
                {"name": "Machine Learning", "endorsements": 75},
                {"name": "Deep Learning", "endorsements": 68},
                {"name": "NLP", "endorsements": 60},
                {"name": "Python", "endorsements": 55},
                {"name": "PyTorch", "endorsements": 50},
                {"name": "Recommendation Systems", "endorsements": 35},
                {"name": "Research", "endorsements": 45},
                {"name": "TensorFlow", "endorsements": 40},
            ],
            "positions": [
                {"company": "DeepMind", "title": "Principal ML Engineer", "isCurrent": True},
                {"company": "Microsoft Research", "title": "Research Scientist", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Oxford", "degree": "DPhil Computer Science (NLP)", "year": 2018},
                {"school": "Peking University", "degree": "BSc Computer Science", "year": 2014},
            ],
            "connectionsCount": 3200,
            "recommendationsCount": 22,
        },
        {
            "profileId": "LI-3006",
            "headline": "Senior Product Manager at Wise | Payments, B2B, Growth",
            "firstName": "Emma",
            "lastName": "Williams",
            "email": "emma.williams.pm@gmail.com",
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/emmawilliams-pm",
            "summary": "Product manager who thinks in systems. Growing Wise Business from 0 to 150% YoY. Previously GoCardless. I bridge the gap between complex payment infrastructure and delightful user experiences.",
            "skills": [
                {"name": "Product Management", "endorsements": 40},
                {"name": "Agile", "endorsements": 35},
                {"name": "User Research", "endorsements": 25},
                {"name": "SQL", "endorsements": 20},
                {"name": "A/B Testing", "endorsements": 22},
                {"name": "Payments", "endorsements": 18},
                {"name": "B2B SaaS", "endorsements": 15},
            ],
            "positions": [
                {"company": "Wise", "title": "Senior Product Manager", "isCurrent": True},
                {"company": "GoCardless", "title": "Product Manager", "isCurrent": False},
                {"company": "Accenture", "title": "Business Analyst", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Warwick", "degree": "BSc Economics", "year": 2016},
            ],
            "connectionsCount": 1500,
            "recommendationsCount": 10,
        },
        {
            "profileId": "LI-3007",
            "headline": "Senior Frontend Engineer at Monzo | Design Systems, Accessibility, React",
            "firstName": "George",
            "lastName": "Papadopoulos",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/georgepapadopoulos-fe",
            "summary": "Frontend engineer passionate about design systems and accessibility. Leading Monzo's component library used by 15 teams. Every user deserves a beautiful, accessible experience.",
            "skills": [
                {"name": "React", "endorsements": 50},
                {"name": "TypeScript", "endorsements": 45},
                {"name": "CSS", "endorsements": 38},
                {"name": "Accessibility", "endorsements": 30},
                {"name": "Design Systems", "endorsements": 28},
                {"name": "Storybook", "endorsements": 20},
                {"name": "Vue.js", "endorsements": 15},
            ],
            "positions": [
                {"company": "Monzo", "title": "Senior Frontend Engineer", "isCurrent": True},
                {"company": "Farfetch", "title": "Frontend Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "King's College London", "degree": "BSc Computer Science", "year": 2018},
            ],
            "connectionsCount": 920,
            "recommendationsCount": 7,
        },
        {
            "profileId": "LI-3008",
            "headline": "VP Engineering at Improbable | Scaling engineering orgs",
            "firstName": "Freya",
            "lastName": "Larsson",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/freyalarsson-eng",
            "summary": "Engineering leader who builds high-performing teams. Scaled Improbable's engineering from 20 to 60+. Previously built and led distributed systems teams at Spotify. Looking for CTO or VP Eng at growth-stage startups.",
            "skills": [
                {"name": "Engineering Management", "endorsements": 60},
                {"name": "Distributed Systems", "endorsements": 45},
                {"name": "Technical Leadership", "endorsements": 55},
                {"name": "Scaling Organizations", "endorsements": 35},
                {"name": "System Design", "endorsements": 40},
                {"name": "Java", "endorsements": 30},
                {"name": "Kotlin", "endorsements": 20},
            ],
            "positions": [
                {"company": "Improbable", "title": "VP Engineering", "isCurrent": True},
                {"company": "Spotify", "title": "Engineering Manager", "isCurrent": False},
                {"company": "King (Activision)", "title": "Senior Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "KTH Royal Institute of Technology", "degree": "MSc Computer Science", "year": 2012},
            ],
            "connectionsCount": 4500,
            "recommendationsCount": 30,
        },
        {
            "profileId": "LI-3009",
            "headline": "Senior Data Scientist at Ocado | Optimization, Forecasting, PhD",
            "firstName": "Olivia",
            "lastName": "Shaw",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/oliviashaw-ds",
            "summary": "Applying statistical methods to real-world logistics problems. PhD in Statistics from Imperial, now making grocery deliveries more efficient. Python, PyTorch, Bayesian methods.",
            "skills": [
                {"name": "Python", "endorsements": 38},
                {"name": "Machine Learning", "endorsements": 35},
                {"name": "Statistics", "endorsements": 42},
                {"name": "Optimization", "endorsements": 30},
                {"name": "PyTorch", "endorsements": 25},
                {"name": "Bayesian Methods", "endorsements": 20},
                {"name": "R", "endorsements": 28},
            ],
            "positions": [
                {"company": "Ocado Technology", "title": "Senior Data Scientist", "isCurrent": True},
                {"company": "Sainsbury's", "title": "Data Scientist", "isCurrent": False},
            ],
            "education": [
                {"school": "Imperial College London", "degree": "PhD Statistics", "year": 2019},
                {"school": "University of Cambridge", "degree": "BA Mathematics", "year": 2015},
            ],
            "connectionsCount": 680,
            "recommendationsCount": 4,
        },
        {
            "profileId": "LI-3010",
            "headline": "Head of Product at Cazoo | B2C, Marketplace, Data-Driven PM",
            "firstName": "Daniel",
            "lastName": "Wright",
            "email": "dan.wright.pm@outlook.com",
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/danielwright-product",
            "summary": "Product leader with deep marketplace and e-commerce experience. Built Cazoo's vehicle browsing and purchasing experience. Previously at ASOS. Looking for VP Product at a mission-driven company.",
            "skills": [
                {"name": "Product Strategy", "endorsements": 45},
                {"name": "Product Management", "endorsements": 50},
                {"name": "Marketplace", "endorsements": 25},
                {"name": "E-commerce", "endorsements": 30},
                {"name": "Data-Driven Decision Making", "endorsements": 35},
                {"name": "A/B Testing", "endorsements": 20},
                {"name": "SQL", "endorsements": 15},
            ],
            "positions": [
                {"company": "Cazoo", "title": "Head of Product", "isCurrent": True},
                {"company": "ASOS", "title": "Senior Product Manager", "isCurrent": False},
                {"company": "Trainline", "title": "Product Manager", "isCurrent": False},
            ],
            "education": [
                {"school": "London School of Economics", "degree": "MSc Management", "year": 2015},
                {"school": "Durham University", "degree": "BA Economics", "year": 2013},
            ],
            "connectionsCount": 2800,
            "recommendationsCount": 18,
        },
        {
            "profileId": "LI-3011",
            "headline": "Backend Engineer at Gymshark | Go, Microservices, E-commerce",
            "firstName": "Ravi",
            "lastName": "Patel",
            "email": "ravi.patel.dev@hotmail.com",
            "location": "Birmingham, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/ravipatel-go",
            "summary": "Building e-commerce infrastructure that handles Black Friday traffic. Go microservices at scale. Previously government digital services at Kainos.",
            "skills": [
                {"name": "Go", "endorsements": 25},
                {"name": "Python", "endorsements": 30},
                {"name": "Kubernetes", "endorsements": 20},
                {"name": "PostgreSQL", "endorsements": 22},
                {"name": "gRPC", "endorsements": 12},
                {"name": "Redis", "endorsements": 18},
                {"name": "Terraform", "endorsements": 15},
            ],
            "positions": [
                {"company": "Gymshark", "title": "Backend Engineer", "isCurrent": True},
                {"company": "Kainos", "title": "Software Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "Aston University", "degree": "BSc Computer Science", "year": 2019},
            ],
            "connectionsCount": 520,
            "recommendationsCount": 3,
        },
        {
            "profileId": "LI-3012",
            "headline": "Senior SRE at Booking.com | High Availability, Incident Management",
            "firstName": "Jack",
            "lastName": "Morrison",
            "email": None,
            "location": "Manchester, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/jackmorrison-sre",
            "summary": "Keeping search working at 5M+ QPS. SRE with passion for reliability, observability, and chaos engineering. Building resilient systems at Booking.com Manchester.",
            "skills": [
                {"name": "Kubernetes", "endorsements": 40},
                {"name": "AWS", "endorsements": 35},
                {"name": "Terraform", "endorsements": 30},
                {"name": "Prometheus", "endorsements": 25},
                {"name": "Go", "endorsements": 20},
                {"name": "Python", "endorsements": 28},
                {"name": "SRE", "endorsements": 35},
                {"name": "Incident Management", "endorsements": 22},
            ],
            "positions": [
                {"company": "Booking.com", "title": "Senior SRE", "isCurrent": True},
                {"company": "THG (The Hut Group)", "title": "Platform Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Sheffield", "degree": "BEng Software Engineering", "year": 2017},
            ],
            "connectionsCount": 780,
            "recommendationsCount": 6,
        },
        {
            "profileId": "LI-3013",
            "headline": "Product Designer at Figma | UX Research, Design Systems, Accessibility",
            "firstName": "Zara",
            "lastName": "Hussain",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/zarahussain-design",
            "summary": "Senior IC designer at Figma London. Crafting tools that designers love. Background in UX research, design systems, and accessibility. Ready to be a founding designer at the right startup.",
            "skills": [
                {"name": "UX Design", "endorsements": 45},
                {"name": "UI Design", "endorsements": 40},
                {"name": "Design Systems", "endorsements": 35},
                {"name": "User Research", "endorsements": 30},
                {"name": "Figma", "endorsements": 50},
                {"name": "Accessibility", "endorsements": 25},
                {"name": "Prototyping", "endorsements": 28},
            ],
            "positions": [
                {"company": "Figma", "title": "Product Designer", "isCurrent": True},
                {"company": "Bumble", "title": "UX Designer", "isCurrent": False},
                {"company": "Deloitte Digital", "title": "Junior Designer", "isCurrent": False},
            ],
            "education": [
                {"school": "Goldsmiths, University of London", "degree": "MA Design", "year": 2018},
            ],
            "connectionsCount": 1100,
            "recommendationsCount": 9,
        },
        {
            "profileId": "LI-3014",
            "headline": "Engineering Manager at Spotify | Building inclusive engineering teams",
            "firstName": "Aisha",
            "lastName": "Khan",
            "email": None,
            "location": "London, England, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/aishakhan-em",
            "summary": "Engineering manager leading 3 squads at Spotify London. Passionate about growing engineers, building inclusive teams, and delivering great music experiences. Java/Kotlin background.",
            "skills": [
                {"name": "Engineering Management", "endorsements": 35},
                {"name": "Java", "endorsements": 40},
                {"name": "Kotlin", "endorsements": 25},
                {"name": "Microservices", "endorsements": 30},
                {"name": "Team Building", "endorsements": 28},
                {"name": "Agile", "endorsements": 32},
            ],
            "positions": [
                {"company": "Spotify", "title": "Engineering Manager", "isCurrent": True},
                {"company": "Skyscanner", "title": "Senior Engineer", "isCurrent": False},
                {"company": "ThoughtWorks", "title": "Software Developer", "isCurrent": False},
            ],
            "education": [
                {"school": "University of Glasgow", "degree": "BSc Computing Science", "year": 2015},
            ],
            "connectionsCount": 1800,
            "recommendationsCount": 12,
        },
        {
            "profileId": "LI-3015",
            "headline": "Data Engineer at Admiral | Insurance Analytics, dbt, BigQuery",
            "firstName": "Hannah",
            "lastName": "Griffiths",
            "email": "hannah.griffiths@outlook.com",
            "location": "Cardiff, Wales, United Kingdom",
            "linkedinUrl": "https://linkedin.com/in/hannahgriffiths-data",
            "summary": "Data engineer building the analytics foundation for insurance pricing. dbt, BigQuery, Airflow. Previously at Confused.com processing 2M quotes/day.",
            "skills": [
                {"name": "Python", "endorsements": 20},
                {"name": "SQL", "endorsements": 25},
                {"name": "dbt", "endorsements": 15},
                {"name": "BigQuery", "endorsements": 12},
                {"name": "Airflow", "endorsements": 10},
                {"name": "Data Modeling", "endorsements": 8},
            ],
            "positions": [
                {"company": "Admiral", "title": "Data Engineer", "isCurrent": True},
                {"company": "Confused.com", "title": "Junior Data Engineer", "isCurrent": False},
            ],
            "education": [
                {"school": "Cardiff University", "degree": "BSc Mathematics", "year": 2020},
            ],
            "connectionsCount": 380,
            "recommendationsCount": 2,
        },
    ]

    async def fetch_candidates(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AdapterCandidate]:
        now = datetime.utcnow()
        candidates = []
        for raw in self.MOCK_CANDIDATES[:limit]:
            candidates.append(AdapterCandidate(
                external_id=raw["profileId"],
                raw_data=raw,
                adapter_name=self.name,
                fetched_at=now,
            ))
        return candidates

    async def fetch_roles(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AdapterRole]:
        # LinkedIn profiles don't have role postings in this context
        return []

    async def get_status(self) -> AdapterStatus:
        return AdapterStatus(
            adapter_name=self.name,
            connected=True,
            last_sync=datetime.utcnow(),
            records_available=len(self.MOCK_CANDIDATES),
        )
