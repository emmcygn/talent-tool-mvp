from datetime import datetime

from .base import AdapterCandidate, AdapterRole, AdapterStatus, BaseAdapter


class HubSpotAdapter(BaseAdapter):
    """Mock HubSpot CRM adapter.

    HubSpot is a CRM — rich in:
    - Contact/engagement data (emails sent, meetings, deal stage)
    - Company associations
    - Pipeline stage history
    - Less detailed work history, more relationship data
    """

    name = "hubspot"
    display_name = "HubSpot CRM"
    adapter_type = "crm"

    MOCK_CANDIDATES = [
        {
            "contactId": "HS-2001",
            "properties": {
                "firstname": "James",
                "lastname": "Hartley",
                "email": "james.hartley@gmail.com",
                "phone": "+44 7700 100001",
                "city": "London",
                "jobtitle": "Senior Backend Engineer",
                "company": "Revolut",
                "industry": "Fintech",
                "notes": "Strong Python/FastAPI background. Previously at Monzo. Looking for principal-level roles. Met at London Python meetup.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-02-20T14:00:00Z",
                "engagement_score": 85,
                "deal_stage": "qualified",
                "tags": ["python", "fintech", "senior", "london"],
            },
        },
        {
            "contactId": "HS-2002",
            "properties": {
                "firstname": "Aisha",
                "lastname": "Khan",
                "email": "aisha.khan.tech@gmail.com",
                "phone": "+44 7700 200002",
                "city": "London",
                "jobtitle": "Engineering Manager",
                "company": "Spotify",
                "industry": "Technology",
                "notes": "Managing 3 squads (15 engineers). Wants to stay in management track. Strong technical background in Java/Kotlin. Spotify London office.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-03-01T10:00:00Z",
                "engagement_score": 72,
                "deal_stage": "new",
                "tags": ["management", "engineering-manager", "java", "london"],
            },
        },
        {
            "contactId": "HS-2003",
            "properties": {
                "firstname": "Ben",
                "lastname": "Cooper",
                "email": "ben.cooper.dev@outlook.com",
                "phone": "+44 7700 200003",
                "city": "Bristol",
                "jobtitle": "Lead Data Engineer",
                "company": "OVO Energy",
                "industry": "Energy/CleanTech",
                "notes": "Built OVO's data platform from scratch. Spark, Kafka, dbt stack. Interested in startups. Available from May.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-02-15T16:30:00Z",
                "engagement_score": 90,
                "deal_stage": "qualified",
                "tags": ["data-engineering", "spark", "startup-interested", "bristol"],
            },
        },
        {
            "contactId": "HS-2004",
            "properties": {
                "firstname": "Rachel",
                "lastname": "Stewart",
                "email": "rachel.stewart@protonmail.com",
                "phone": "+44 7700 200004",
                "city": "London",
                "jobtitle": "Staff Software Engineer",
                "company": "Thought Machine",
                "industry": "Fintech/Banking",
                "notes": "Core banking platform. Go, Kubernetes, distributed systems. 10 years experience. Wants remote-first.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-10T09:00:00Z",
                "engagement_score": 95,
                "deal_stage": "proposal",
                "tags": ["golang", "distributed-systems", "staff-engineer", "remote"],
            },
        },
        {
            "contactId": "HS-2005",
            "properties": {
                "firstname": "Chris",
                "lastname": "Dunkley",
                "email": "chris.dunkley@gmail.com",
                "phone": "+44 7700 200005",
                "city": "Manchester",
                "jobtitle": "Senior Frontend Developer",
                "company": "AutoTrader",
                "industry": "E-commerce/Automotive",
                "notes": "React expert, accessibility specialist. Led design system at AutoTrader. Considering contract work.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-01-28T11:15:00Z",
                "engagement_score": 65,
                "deal_stage": "new",
                "tags": ["react", "accessibility", "design-systems", "manchester"],
            },
        },
        {
            "contactId": "HS-2006",
            "properties": {
                "firstname": "Mei",
                "lastname": "Zhang",
                "email": "mei.zhang.ml@gmail.com",
                "phone": "+44 7700 200006",
                "city": "London",
                "jobtitle": "Principal ML Engineer",
                "company": "DeepMind",
                "industry": "AI/Research",
                "notes": "Moving from research to applied ML. Wants product-focused role. Expert in NLP and recommendation systems. Published at NeurIPS.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-05T13:45:00Z",
                "engagement_score": 88,
                "deal_stage": "qualified",
                "tags": ["ml", "nlp", "principal", "deepmind", "research-to-industry"],
            },
        },
        {
            "contactId": "HS-2007",
            "properties": {
                "firstname": "Daniel",
                "lastname": "Wright",
                "email": "dan.wright.pm@outlook.com",
                "phone": "+44 7700 200007",
                "city": "London",
                "jobtitle": "Head of Product",
                "company": "Cazoo",
                "industry": "E-commerce/Automotive",
                "notes": "Post-Cazoo restructure, looking for VP Product or Head of Product role. B2C and marketplace experience. Strong on data-driven PM.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-02-28T10:30:00Z",
                "engagement_score": 78,
                "deal_stage": "qualified",
                "tags": ["product", "head-of", "marketplace", "b2c", "london"],
            },
        },
        {
            "contactId": "HS-2008",
            "properties": {
                "firstname": "Sian",
                "lastname": "Evans",
                "email": "sian.evans@icloud.com",
                "phone": "+44 7700 200008",
                "city": "Cardiff",
                "jobtitle": "DevOps Engineer",
                "company": "DVLA",
                "industry": "Government/Public Sector",
                "notes": "Government digital services background. Terraform, AWS, Python. Wants to move to private sector. Open to London relocation.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-02-10T14:00:00Z",
                "engagement_score": 55,
                "deal_stage": "new",
                "tags": ["devops", "terraform", "government", "relocating"],
            },
        },
        {
            "contactId": "HS-2009",
            "properties": {
                "firstname": "Tariq",
                "lastname": "Mahmood",
                "email": "tariq.mahmood@yahoo.co.uk",
                "phone": "+44 7700 200009",
                "city": "Birmingham",
                "jobtitle": "Full Stack Developer",
                "company": "PureGym",
                "industry": "Health & Fitness",
                "notes": "TypeScript, React, Node.js. Membership platform. 4 years experience. Looking for higher seniority role at a tech company.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-01-20T09:30:00Z",
                "engagement_score": 60,
                "deal_stage": "new",
                "tags": ["typescript", "fullstack", "birmingham", "growth-minded"],
            },
        },
        {
            "contactId": "HS-2010",
            "properties": {
                "firstname": "Olivia",
                "lastname": "Shaw",
                "email": "olivia.shaw.data@gmail.com",
                "phone": "+44 7700 200010",
                "city": "London",
                "jobtitle": "Senior Data Scientist",
                "company": "Ocado Technology",
                "industry": "E-commerce/Logistics",
                "notes": "Demand forecasting and route optimization. PhD Statistics from Imperial. Python, PyTorch, Bayesian methods.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-12T11:00:00Z",
                "engagement_score": 82,
                "deal_stage": "qualified",
                "tags": ["data-science", "phd", "optimization", "london"],
            },
        },
        {
            "contactId": "HS-2011",
            "properties": {
                "firstname": "Liam",
                "lastname": "Kelly",
                "email": "liam.kelly@protonmail.com",
                "phone": "+44 7700 200011",
                "city": "Dublin",
                "jobtitle": "Security Engineer",
                "company": "Intercom",
                "industry": "SaaS",
                "notes": "Application security, pen testing, SOC 2 compliance. Willing to relocate to London. 7 years experience.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-02-05T15:00:00Z",
                "engagement_score": 50,
                "deal_stage": "new",
                "tags": ["security", "appsec", "soc2", "relocating-london"],
            },
        },
        {
            "contactId": "HS-2012",
            "properties": {
                "firstname": "Zara",
                "lastname": "Hussain",
                "email": "zara.hussain@gmail.com",
                "phone": "+44 7700 200012",
                "city": "London",
                "jobtitle": "Product Designer",
                "company": "Figma",
                "industry": "Design Tools/SaaS",
                "notes": "Senior IC designer at Figma London. UX research, design systems, accessibility. Wants to join early-stage startup as founding designer.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-08T10:00:00Z",
                "engagement_score": 75,
                "deal_stage": "qualified",
                "tags": ["design", "ux", "figma", "startup-interested", "founding"],
            },
        },
        {
            "contactId": "HS-2013",
            "properties": {
                "firstname": "Nathan",
                "lastname": "Brooks",
                "email": "nathan.brooks.eng@outlook.com",
                "phone": "+44 7700 200013",
                "city": "London",
                "jobtitle": "Senior iOS Engineer",
                "company": "Deliveroo",
                "industry": "Food Delivery/E-commerce",
                "notes": "Swift, SwiftUI, Combine. Led rider app team. Interested in fintech or health tech mobile roles.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-02-25T13:30:00Z",
                "engagement_score": 68,
                "deal_stage": "new",
                "tags": ["ios", "swift", "mobile", "fintech-interested"],
            },
        },
        {
            "contactId": "HS-2014",
            "properties": {
                "firstname": "Chloe",
                "lastname": "Adams",
                "email": "chloe.adams@gmail.com",
                "phone": "+44 7700 200014",
                "city": "London",
                "jobtitle": "Site Reliability Engineer",
                "company": "Snyk",
                "industry": "Developer Tools/Security",
                "notes": "SRE at Snyk, previously AWS. Go, Kubernetes, Terraform. Incident response expertise. Wants a lead SRE role.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-15T09:45:00Z",
                "engagement_score": 80,
                "deal_stage": "qualified",
                "tags": ["sre", "golang", "kubernetes", "lead-aspirant"],
            },
        },
        {
            "contactId": "HS-2015",
            "properties": {
                "firstname": "Isaac",
                "lastname": "Thompson",
                "email": "isaac.thompson@yahoo.co.uk",
                "phone": "+44 7700 200015",
                "city": "Newcastle",
                "jobtitle": "Backend Developer",
                "company": "Sage",
                "industry": "Enterprise Software/Fintech",
                "notes": "C#/.NET background, learning Go. Accounting software. 5 years experience. Wants to move to a tech-first company. Remote preferred.",
                "lifecyclestage": "lead",
                "last_engagement": "2026-01-15T11:00:00Z",
                "engagement_score": 45,
                "deal_stage": "new",
                "tags": ["dotnet", "golang", "fintech", "remote", "newcastle"],
            },
        },
        {
            "contactId": "HS-2016",
            "properties": {
                "firstname": "Freya",
                "lastname": "Larsson",
                "email": "freya.larsson@gmail.com",
                "phone": "+44 7700 200016",
                "city": "London",
                "jobtitle": "VP Engineering",
                "company": "Improbable",
                "industry": "Gaming/Metaverse",
                "notes": "VP Eng managing 40+ engineers across 5 teams. Scaling org from 20 to 60. Wants CTO or VP Eng at Series A/B. Strong technical background in distributed systems.",
                "lifecyclestage": "opportunity",
                "last_engagement": "2026-03-18T10:00:00Z",
                "engagement_score": 92,
                "deal_stage": "proposal",
                "tags": ["vp-engineering", "leadership", "scaling", "series-a-b"],
            },
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
                external_id=raw["contactId"],
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
        # HubSpot CRM doesn't have job postings — return empty
        return []

    async def get_status(self) -> AdapterStatus:
        return AdapterStatus(
            adapter_name=self.name,
            connected=True,
            last_sync=datetime.utcnow(),
            records_available=len(self.MOCK_CANDIDATES),
        )
