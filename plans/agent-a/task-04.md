# Agent A — Task 04: Adapter Interfaces + Mocks

## Mission
Create the abstract base adapter class defining the interface for external recruitment data sources, implement three mock adapters (Bullhorn, HubSpot, LinkedIn) that return realistic UK-market candidate records, and build an adapter registry for discovery and management.

## Context
Day 2 task, depends on Task 01 (contracts). Adapters are the data ingestion boundary — they simulate pulling candidate data from external ATS/CRM/social systems. Each adapter returns data in its own format (not canonical). The normalization step (Task 05) maps adapter output to canonical `Candidate` format. Mock data must be realistic enough for demo credibility with recruitment professionals.

## Prerequisites
- Task 01 complete (contracts in `backend/contracts/`)
- Python environment with dependencies installed

## Checklist
- [ ] Create `backend/adapters/__init__.py`
- [ ] Create `backend/adapters/base.py` with abstract `BaseAdapter` class
- [ ] Create `backend/adapters/registry.py` with adapter registry pattern
- [ ] Create `backend/adapters/bullhorn.py` with 18 realistic UK candidates (ATS focus)
- [ ] Create `backend/adapters/hubspot.py` with 16 realistic UK candidates (CRM focus)
- [ ] Create `backend/adapters/linkedin.py` with 15 realistic UK candidates (profile focus)
- [ ] Each adapter returns candidates in its own native format (not canonical)
- [ ] Include `fetch_roles()` on Bullhorn adapter (ATS has roles)
- [ ] Include `get_status()` on all adapters for health monitoring
- [ ] Write tests for adapter instantiation, data shape, registry lookup
- [ ] Commit

## Implementation Details

### Abstract Base Adapter (`backend/adapters/base.py`)

```python
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel
from typing import Any


class AdapterStatus(BaseModel):
    """Health status returned by adapters."""
    adapter_name: str
    connected: bool
    last_sync: datetime | None = None
    records_available: int = 0
    error: str | None = None


class AdapterCandidate(BaseModel):
    """Raw candidate record as returned by an adapter.

    Each adapter returns its own field set. Not all fields are present
    in every adapter — that's the point. Normalization handles mapping.
    """
    external_id: str
    raw_data: dict[str, Any]  # adapter-specific fields
    adapter_name: str
    fetched_at: datetime


class AdapterRole(BaseModel):
    """Raw role record as returned by an adapter."""
    external_id: str
    raw_data: dict[str, Any]
    adapter_name: str
    fetched_at: datetime


class BaseAdapter(ABC):
    """Abstract base class for all recruitment data adapters.

    Each adapter connects to an external system (Bullhorn, HubSpot,
    LinkedIn) and returns raw records in that system's native format.
    The normalization pipeline (Task 05) maps these to canonical format.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter identifier, e.g. 'bullhorn', 'hubspot', 'linkedin'."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable adapter name for UI display."""
        ...

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Type category: 'ats', 'crm', 'social'."""
        ...

    @abstractmethod
    async def fetch_candidates(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AdapterCandidate]:
        """Fetch candidate records from the external system.

        Args:
            since: Only fetch records modified after this datetime.
            limit: Maximum number of records to return.

        Returns:
            List of raw adapter candidate records.
        """
        ...

    @abstractmethod
    async def fetch_roles(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AdapterRole]:
        """Fetch role/job records from the external system.

        Not all adapters have roles (e.g., LinkedIn profiles don't).
        Return empty list if not applicable.
        """
        ...

    @abstractmethod
    async def get_status(self) -> AdapterStatus:
        """Return current adapter health status."""
        ...
```

### Adapter Registry (`backend/adapters/registry.py`)

```python
from .base import BaseAdapter, AdapterStatus
import logging

logger = logging.getLogger("recruittech.adapters")


class AdapterRegistry:
    """Registry for managing adapter instances.

    Provides discovery, lookup, and health checking for all
    registered adapters.

    Usage:
        registry = AdapterRegistry()
        registry.register(BullhornAdapter())
        registry.register(HubSpotAdapter())
        registry.register(LinkedInAdapter())

        adapter = registry.get("bullhorn")
        candidates = await adapter.fetch_candidates()
    """

    def __init__(self):
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        """Register an adapter instance."""
        if adapter.name in self._adapters:
            logger.warning(f"Adapter '{adapter.name}' already registered, replacing")
        self._adapters[adapter.name] = adapter
        logger.info(f"Registered adapter: {adapter.name} ({adapter.display_name})")

    def get(self, name: str) -> BaseAdapter:
        """Get adapter by name. Raises KeyError if not found."""
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not registered. Available: {list(self._adapters.keys())}")
        return self._adapters[name]

    def list_all(self) -> list[BaseAdapter]:
        """Return all registered adapters."""
        return list(self._adapters.values())

    def list_names(self) -> list[str]:
        """Return names of all registered adapters."""
        return list(self._adapters.keys())

    async def get_all_statuses(self) -> list[AdapterStatus]:
        """Get health status of all registered adapters."""
        statuses = []
        for adapter in self._adapters.values():
            try:
                status = await adapter.get_status()
                statuses.append(status)
            except Exception as e:
                statuses.append(AdapterStatus(
                    adapter_name=adapter.name,
                    connected=False,
                    error=str(e),
                ))
        return statuses


# Global registry instance — initialized at app startup
adapter_registry = AdapterRegistry()


def init_adapters() -> AdapterRegistry:
    """Initialize and register all mock adapters.

    Called during FastAPI lifespan startup.
    """
    from .bullhorn import BullhornAdapter
    from .hubspot import HubSpotAdapter
    from .linkedin import LinkedInAdapter

    adapter_registry.register(BullhornAdapter())
    adapter_registry.register(HubSpotAdapter())
    adapter_registry.register(LinkedInAdapter())

    logger.info(f"Initialized {len(adapter_registry.list_names())} adapters")
    return adapter_registry
```

### Bullhorn Mock Adapter (`backend/adapters/bullhorn.py`)

```python
from datetime import datetime, timedelta
from .base import BaseAdapter, AdapterCandidate, AdapterRole, AdapterStatus


class BullhornAdapter(BaseAdapter):
    """Mock Bullhorn ATS adapter.

    Bullhorn is an ATS (Applicant Tracking System) — rich in:
    - Detailed work history with dates
    - Candidate status in pipeline
    - Associated job orders
    - Skill tags and certifications
    """

    name = "bullhorn"
    display_name = "Bullhorn ATS"
    adapter_type = "ats"

    # 18 realistic UK-market candidates with ATS-style data
    MOCK_CANDIDATES = [
        {
            "candidateId": "BH-1001",
            "firstName": "James",
            "lastName": "Hartley",
            "email": "james.hartley@gmail.com",
            "phone": "+44 7700 100001",
            "address": {"city": "London", "postcode": "EC2A 4NE"},
            "status": "Available",
            "skillList": "Python, Django, FastAPI, PostgreSQL, Redis, Docker, AWS",
            "certifications": ["AWS Solutions Architect Associate"],
            "employmentHistory": [
                {"company": "Revolut", "title": "Senior Backend Engineer", "startDate": "2021-03-01", "endDate": None, "description": "Led payments microservices team. Python/FastAPI, PostgreSQL, Kafka. Reduced payment processing latency by 40%."},
                {"company": "Monzo", "title": "Backend Engineer", "startDate": "2018-06-01", "endDate": "2021-02-28", "description": "Built real-time transaction processing. Go and Python. Scaled to 5M daily transactions."},
                {"company": "ThoughtWorks", "title": "Software Consultant", "startDate": "2016-01-01", "endDate": "2018-05-31", "description": "Client-facing consulting across fintech and retail. Java, Python, microservices architecture."},
            ],
            "salary": {"desired": 95000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Recruiter Referral",
            "dateAdded": "2025-11-15T10:30:00Z",
        },
        {
            "candidateId": "BH-1002",
            "firstName": "Priya",
            "lastName": "Sharma",
            "email": "priya.sharma.dev@outlook.com",
            "phone": "+44 7700 100002",
            "address": {"city": "Manchester", "postcode": "M1 3HZ"},
            "status": "Available",
            "skillList": "Python, Machine Learning, TensorFlow, PyTorch, Scikit-learn, SQL, Spark",
            "certifications": ["Google Professional ML Engineer"],
            "employmentHistory": [
                {"company": "AstraZeneca", "title": "Senior ML Engineer", "startDate": "2022-01-01", "endDate": None, "description": "Drug discovery ML pipelines. Built model serving infrastructure handling 10K predictions/hour."},
                {"company": "BBC", "title": "Data Scientist", "startDate": "2019-09-01", "endDate": "2021-12-31", "description": "Recommendation engine for iPlayer. A/B testing framework, NLP for content classification."},
                {"company": "University of Manchester", "title": "Research Associate", "startDate": "2017-09-01", "endDate": "2019-08-31", "description": "NLP research, published 3 papers on transformer architectures."},
            ],
            "salary": {"desired": 90000, "currency": "GBP"},
            "noticePeriod": "3 months",
            "source": "LinkedIn Application",
            "dateAdded": "2025-10-20T14:15:00Z",
        },
        {
            "candidateId": "BH-1003",
            "firstName": "Tom",
            "lastName": "Richardson",
            "email": "tom.richardson@protonmail.com",
            "phone": "+44 7700 100003",
            "address": {"city": "Bristol", "postcode": "BS1 5UH"},
            "status": "Placed",
            "skillList": "TypeScript, React, Next.js, Node.js, GraphQL, PostgreSQL, Tailwind CSS",
            "certifications": [],
            "employmentHistory": [
                {"company": "Deliveroo", "title": "Senior Frontend Engineer", "startDate": "2020-04-01", "endDate": None, "description": "Led rider app redesign. React Native, TypeScript, GraphQL. 30% improvement in order completion."},
                {"company": "Funding Circle", "title": "Full Stack Developer", "startDate": "2017-09-01", "endDate": "2020-03-31", "description": "Borrower onboarding platform. React, Node.js, PostgreSQL. PCI compliance implementation."},
            ],
            "salary": {"desired": 85000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Direct Application",
            "dateAdded": "2025-09-05T09:00:00Z",
        },
        {
            "candidateId": "BH-1004",
            "firstName": "Sarah",
            "lastName": "Chen",
            "email": "sarah.chen@gmail.com",
            "phone": "+44 7700 100004",
            "address": {"city": "London", "postcode": "SW1A 1AA"},
            "status": "Available",
            "skillList": "Java, Spring Boot, Kubernetes, Terraform, CI/CD, Microservices, AWS, Kafka",
            "certifications": ["AWS DevOps Engineer Professional", "CKA"],
            "employmentHistory": [
                {"company": "HSBC", "title": "Lead Platform Engineer", "startDate": "2021-06-01", "endDate": None, "description": "Platform engineering for trading systems. Kubernetes cluster management, 99.99% uptime SLA."},
                {"company": "Sky", "title": "Senior DevOps Engineer", "startDate": "2018-02-01", "endDate": "2021-05-31", "description": "Streaming platform infrastructure. Terraform, Jenkins, Docker. 200+ microservices deployment pipeline."},
                {"company": "Capgemini", "title": "DevOps Consultant", "startDate": "2015-07-01", "endDate": "2018-01-31", "description": "Multi-client DevOps transformations. Azure, AWS, GCP. Government and financial services."},
            ],
            "salary": {"desired": 105000, "currency": "GBP"},
            "noticePeriod": "3 months",
            "source": "Referral",
            "dateAdded": "2025-12-01T11:00:00Z",
        },
        {
            "candidateId": "BH-1005",
            "firstName": "Oluwaseun",
            "lastName": "Adeyemi",
            "email": "seun.adeyemi@yahoo.co.uk",
            "phone": "+44 7700 100005",
            "address": {"city": "London", "postcode": "E14 5AB"},
            "status": "Available",
            "skillList": "Python, Data Engineering, Airflow, dbt, Snowflake, Spark, AWS Glue, SQL",
            "certifications": ["Snowflake SnowPro Core", "AWS Data Analytics Specialty"],
            "employmentHistory": [
                {"company": "Just Eat Takeaway", "title": "Senior Data Engineer", "startDate": "2022-03-01", "endDate": None, "description": "Real-time data platform. Kafka Streams, Flink, dbt. Processing 50M events/day."},
                {"company": "Starling Bank", "title": "Data Engineer", "startDate": "2019-11-01", "endDate": "2022-02-28", "description": "Built data warehouse from scratch. Snowflake, Airflow, Python. Regulatory reporting automation."},
                {"company": "PwC", "title": "Data Analyst", "startDate": "2017-09-01", "endDate": "2019-10-31", "description": "Financial data analysis for audit clients. SQL, Python, Tableau."},
            ],
            "salary": {"desired": 88000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Job Board",
            "dateAdded": "2026-01-10T16:45:00Z",
        },
        {
            "candidateId": "BH-1006",
            "firstName": "Emma",
            "lastName": "Williams",
            "email": "emma.williams.pm@gmail.com",
            "phone": "+44 7700 100006",
            "address": {"city": "London", "postcode": "WC2N 5DU"},
            "status": "Available",
            "skillList": "Product Management, Agile, Scrum, User Research, A/B Testing, SQL, Jira, Figma",
            "certifications": ["CSPO"],
            "employmentHistory": [
                {"company": "Wise", "title": "Senior Product Manager", "startDate": "2021-09-01", "endDate": None, "description": "Business payments vertical. Grew B2B volume 150% YoY. Led team of 8 engineers + 2 designers."},
                {"company": "GoCardless", "title": "Product Manager", "startDate": "2019-01-01", "endDate": "2021-08-31", "description": "Direct debit payment flows. Reduced merchant onboarding time from 5 days to 2 hours."},
                {"company": "Accenture", "title": "Business Analyst", "startDate": "2016-09-01", "endDate": "2018-12-31", "description": "Digital transformation for retail banking clients. Requirements gathering, process mapping."},
            ],
            "salary": {"desired": 92000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Recruiter Referral",
            "dateAdded": "2026-01-20T09:30:00Z",
        },
        {
            "candidateId": "BH-1007",
            "firstName": "Ravi",
            "lastName": "Patel",
            "email": "ravi.patel.dev@hotmail.com",
            "phone": "+44 7700 100007",
            "address": {"city": "Birmingham", "postcode": "B2 5DB"},
            "status": "Available",
            "skillList": "Python, Go, gRPC, Kubernetes, PostgreSQL, Redis, Terraform, Prometheus",
            "certifications": [],
            "employmentHistory": [
                {"company": "Gymshark", "title": "Backend Engineer", "startDate": "2022-06-01", "endDate": None, "description": "E-commerce platform backend. Go microservices, handling Black Friday traffic 10x spikes."},
                {"company": "Kainos", "title": "Software Engineer", "startDate": "2020-01-01", "endDate": "2022-05-31", "description": "Government digital services (HMRC, NHS). Python, Django, PostgreSQL. GDS standards."},
            ],
            "salary": {"desired": 72000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Direct Application",
            "dateAdded": "2026-02-01T13:00:00Z",
        },
        {
            "candidateId": "BH-1008",
            "firstName": "Fatima",
            "lastName": "Al-Rashidi",
            "email": "fatima.alrashidi@gmail.com",
            "phone": "+44 7700 100008",
            "address": {"city": "London", "postcode": "SE1 7PB"},
            "status": "Available",
            "skillList": "React, TypeScript, Node.js, AWS Lambda, DynamoDB, Serverless, Jest",
            "certifications": ["AWS Solutions Architect Associate"],
            "employmentHistory": [
                {"company": "Checkout.com", "title": "Senior Full Stack Engineer", "startDate": "2021-04-01", "endDate": None, "description": "Merchant dashboard and payment analytics. React, Node.js, serverless architecture."},
                {"company": "Babylon Health", "title": "Full Stack Developer", "startDate": "2019-02-01", "endDate": "2021-03-31", "description": "Patient-facing health app. React Native, Node.js, HIPAA-compliant data handling."},
            ],
            "salary": {"desired": 88000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "LinkedIn Application",
            "dateAdded": "2026-02-05T10:15:00Z",
        },
        {
            "candidateId": "BH-1009",
            "firstName": "David",
            "lastName": "MacGregor",
            "email": "david.macgregor@outlook.com",
            "phone": "+44 7700 100009",
            "address": {"city": "Edinburgh", "postcode": "EH1 1YZ"},
            "status": "Available",
            "skillList": "Scala, Apache Spark, Kafka, Hadoop, Python, SQL, Databricks, Delta Lake",
            "certifications": ["Databricks Certified Associate Developer"],
            "employmentHistory": [
                {"company": "FanDuel", "title": "Senior Data Engineer", "startDate": "2021-01-01", "endDate": None, "description": "Real-time betting data pipeline. Spark Structured Streaming, Kafka, Delta Lake. Sub-second latency."},
                {"company": "Standard Life Aberdeen", "title": "Data Engineer", "startDate": "2018-06-01", "endDate": "2020-12-31", "description": "Investment portfolio analytics platform. Scala, Spark, Hadoop. Regulatory data lineage."},
            ],
            "salary": {"desired": 82000, "currency": "GBP"},
            "noticePeriod": "3 months",
            "source": "Job Board",
            "dateAdded": "2026-01-25T14:00:00Z",
        },
        {
            "candidateId": "BH-1010",
            "firstName": "Lucy",
            "lastName": "O'Brien",
            "email": "lucy.obrien@icloud.com",
            "phone": "+44 7700 100010",
            "address": {"city": "London", "postcode": "N1 6AH"},
            "status": "Available",
            "skillList": "Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, Terraform",
            "certifications": [],
            "employmentHistory": [
                {"company": "Multiverse", "title": "Backend Engineer", "startDate": "2023-01-01", "endDate": None, "description": "Ed-tech apprenticeship platform. Python/FastAPI, PostgreSQL, event-driven architecture."},
                {"company": "Bloom & Wild", "title": "Junior Developer", "startDate": "2021-06-01", "endDate": "2022-12-31", "description": "E-commerce backend. Django, Celery, PostgreSQL. Subscription management system."},
            ],
            "salary": {"desired": 60000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Recruiter Referral",
            "dateAdded": "2026-02-10T11:30:00Z",
        },
        {
            "candidateId": "BH-1011",
            "firstName": "Mohammed",
            "lastName": "Hassan",
            "email": "mohammed.hassan.tech@gmail.com",
            "phone": "+44 7700 100011",
            "address": {"city": "London", "postcode": "E1 6AN"},
            "status": "Available",
            "skillList": "Python, Machine Learning, NLP, LLMs, RAG, LangChain, Vector Databases, OpenAI API",
            "certifications": [],
            "employmentHistory": [
                {"company": "Eigen Technologies", "title": "ML Engineer", "startDate": "2022-09-01", "endDate": None, "description": "Document understanding using LLMs. Built RAG pipeline processing 100K documents. Fine-tuned models for legal NLP."},
                {"company": "Faculty AI", "title": "Data Scientist", "startDate": "2020-06-01", "endDate": "2022-08-31", "description": "Government and enterprise AI projects. NLP, computer vision, MLOps. Published internal research on few-shot learning."},
            ],
            "salary": {"desired": 85000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Direct Application",
            "dateAdded": "2026-02-15T09:00:00Z",
        },
        {
            "candidateId": "BH-1012",
            "firstName": "Charlotte",
            "lastName": "Turner",
            "email": "charlotte.turner@gmail.com",
            "phone": "+44 7700 100012",
            "address": {"city": "Leeds", "postcode": "LS1 4AP"},
            "status": "Available",
            "skillList": "Product Management, Data Analytics, SQL, Python, Mixpanel, Amplitude, Tableau",
            "certifications": [],
            "employmentHistory": [
                {"company": "NHS Digital", "title": "Product Manager", "startDate": "2022-01-01", "endDate": None, "description": "NHS App features. COVID pass, prescriptions, appointments. 30M registered users. GDS service assessments."},
                {"company": "Sky Betting & Gaming", "title": "Associate Product Manager", "startDate": "2020-03-01", "endDate": "2021-12-31", "description": "Bet builder feature. Data-driven feature development, A/B testing, user research."},
            ],
            "salary": {"desired": 70000, "currency": "GBP"},
            "noticePeriod": "3 months",
            "source": "Job Board",
            "dateAdded": "2026-02-18T15:30:00Z",
        },
        {
            "candidateId": "BH-1013",
            "firstName": "Alex",
            "lastName": "Novak",
            "email": "alex.novak@protonmail.com",
            "phone": "+44 7700 100013",
            "address": {"city": "London", "postcode": "WC1E 7HU"},
            "status": "Available",
            "skillList": "Rust, C++, Systems Programming, WebAssembly, Linux, Performance Engineering",
            "certifications": [],
            "employmentHistory": [
                {"company": "Cloudflare", "title": "Systems Engineer", "startDate": "2021-08-01", "endDate": None, "description": "Edge compute runtime. Rust, WebAssembly, V8. Sub-millisecond cold start optimization."},
                {"company": "Arm", "title": "Software Engineer", "startDate": "2018-09-01", "endDate": "2021-07-31", "description": "CPU simulator tooling. C++, LLVM, performance profiling. Neoverse platform."},
            ],
            "salary": {"desired": 110000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Referral",
            "dateAdded": "2026-02-20T10:00:00Z",
        },
        {
            "candidateId": "BH-1014",
            "firstName": "Amara",
            "lastName": "Okafor",
            "email": "amara.okafor@gmail.com",
            "phone": "+44 7700 100014",
            "address": {"city": "London", "postcode": "EC1V 2NX"},
            "status": "Available",
            "skillList": "Python, Django, REST APIs, PostgreSQL, Celery, Docker, AWS, Stripe API",
            "certifications": [],
            "employmentHistory": [
                {"company": "Paddle", "title": "Backend Engineer", "startDate": "2023-02-01", "endDate": None, "description": "Billing and subscription platform. Python/Django, PostgreSQL, Stripe integration. PCI-DSS compliance."},
                {"company": "Tray.io", "title": "Software Engineer", "startDate": "2021-03-01", "endDate": "2023-01-31", "description": "Integration platform backend. Python, REST APIs, webhook delivery system."},
                {"company": "Makers Academy", "title": "Junior Developer (Bootcamp)", "startDate": "2020-09-01", "endDate": "2021-02-28", "description": "Full stack web development bootcamp. Ruby, JavaScript, TDD practices."},
            ],
            "salary": {"desired": 68000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "LinkedIn Application",
            "dateAdded": "2026-02-22T08:45:00Z",
        },
        {
            "candidateId": "BH-1015",
            "firstName": "George",
            "lastName": "Papadopoulos",
            "email": "george.papa@outlook.com",
            "phone": "+44 7700 100015",
            "address": {"city": "London", "postcode": "SW7 2AZ"},
            "status": "Available",
            "skillList": "React, Vue.js, TypeScript, CSS, Accessibility, Design Systems, Storybook, Figma",
            "certifications": [],
            "employmentHistory": [
                {"company": "Monzo", "title": "Senior Frontend Engineer", "startDate": "2022-01-01", "endDate": None, "description": "Design system lead. Built component library used across 15 product teams. WCAG 2.1 AA compliance."},
                {"company": "Farfetch", "title": "Frontend Engineer", "startDate": "2019-06-01", "endDate": "2021-12-31", "description": "Luxury e-commerce checkout. React, performance optimization, internationalization for 20+ markets."},
            ],
            "salary": {"desired": 85000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Recruiter Referral",
            "dateAdded": "2026-03-01T12:00:00Z",
        },
        {
            "candidateId": "BH-1016",
            "firstName": "Sophie",
            "lastName": "Bennett",
            "email": "sophie.bennett.data@gmail.com",
            "phone": "+44 7700 100016",
            "address": {"city": "Cambridge", "postcode": "CB2 1TN"},
            "status": "Available",
            "skillList": "Python, R, Statistics, Machine Learning, Clinical Trials, Bioinformatics, SQL",
            "certifications": ["PhD Computational Biology"],
            "employmentHistory": [
                {"company": "Illumina", "title": "Senior Bioinformatician", "startDate": "2021-04-01", "endDate": None, "description": "Genomics data pipeline. Python, Nextflow, AWS Batch. Variant calling and annotation."},
                {"company": "Cancer Research UK", "title": "Research Data Scientist", "startDate": "2018-10-01", "endDate": "2021-03-31", "description": "Clinical trial data analysis. R, Python, survival analysis. Published 5 peer-reviewed papers."},
            ],
            "salary": {"desired": 78000, "currency": "GBP"},
            "noticePeriod": "3 months",
            "source": "Job Board",
            "dateAdded": "2026-03-05T14:30:00Z",
        },
        {
            "candidateId": "BH-1017",
            "firstName": "Jack",
            "lastName": "Morrison",
            "email": "jack.morrison.sre@gmail.com",
            "phone": "+44 7700 100017",
            "address": {"city": "Manchester", "postcode": "M2 4WU"},
            "status": "Available",
            "skillList": "Kubernetes, Terraform, AWS, GCP, Python, Go, Prometheus, Grafana, Datadog, SRE",
            "certifications": ["CKA", "AWS DevOps Engineer Professional"],
            "employmentHistory": [
                {"company": "Booking.com", "title": "Senior SRE", "startDate": "2020-09-01", "endDate": None, "description": "Search infrastructure reliability. 5M+ QPS. Incident management, capacity planning, chaos engineering."},
                {"company": "The Hut Group (THG)", "title": "Platform Engineer", "startDate": "2018-01-01", "endDate": "2020-08-31", "description": "E-commerce platform. Kubernetes migration, CI/CD pipelines, infrastructure as code."},
            ],
            "salary": {"desired": 95000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Direct Application",
            "dateAdded": "2026-03-10T09:15:00Z",
        },
        {
            "candidateId": "BH-1018",
            "firstName": "Hannah",
            "lastName": "Griffiths",
            "email": "hannah.griffiths@outlook.com",
            "phone": "+44 7700 100018",
            "address": {"city": "Cardiff", "postcode": "CF10 1EP"},
            "status": "Available",
            "skillList": "Python, FastAPI, SQL, Data Modelling, ETL, Airflow, dbt, BigQuery",
            "certifications": [],
            "employmentHistory": [
                {"company": "Admiral", "title": "Data Engineer", "startDate": "2022-06-01", "endDate": None, "description": "Insurance analytics platform. dbt, BigQuery, Airflow. Claims prediction data pipeline."},
                {"company": "Confused.com", "title": "Junior Data Engineer", "startDate": "2020-09-01", "endDate": "2022-05-31", "description": "Price comparison data ingestion. Python, SQL, AWS Lambda. Processing 2M quotes/day."},
            ],
            "salary": {"desired": 58000, "currency": "GBP"},
            "noticePeriod": "1 month",
            "source": "Job Board",
            "dateAdded": "2026-03-12T11:00:00Z",
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
            if since:
                added = datetime.fromisoformat(raw["dateAdded"].replace("Z", "+00:00"))
                if added <= since:
                    continue
            candidates.append(AdapterCandidate(
                external_id=raw["candidateId"],
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
        # Bullhorn has job orders — return a few mock roles
        now = datetime.utcnow()
        mock_roles = [
            {
                "jobOrderId": "JO-5001",
                "title": "Senior Python Developer",
                "description": "Fintech startup needs a senior Python dev. FastAPI, PostgreSQL, AWS. London hybrid.",
                "clientCorporation": "NovaPay",
                "skillList": "Python, FastAPI, PostgreSQL, AWS, Docker",
                "salary": {"min": 80000, "max": 100000, "currency": "GBP"},
                "location": "London",
                "remotePolicy": "hybrid",
            },
            {
                "jobOrderId": "JO-5002",
                "title": "ML Engineer",
                "description": "Healthtech company building clinical NLP. PyTorch, transformers, MLOps.",
                "clientCorporation": "MedAnalytics",
                "skillList": "Python, PyTorch, NLP, MLOps, Docker, Kubernetes",
                "salary": {"min": 75000, "max": 95000, "currency": "GBP"},
                "location": "Manchester",
                "remotePolicy": "remote",
            },
        ]
        return [
            AdapterRole(
                external_id=r["jobOrderId"],
                raw_data=r,
                adapter_name=self.name,
                fetched_at=now,
            )
            for r in mock_roles[:limit]
        ]

    async def get_status(self) -> AdapterStatus:
        return AdapterStatus(
            adapter_name=self.name,
            connected=True,
            last_sync=datetime.utcnow(),
            records_available=len(self.MOCK_CANDIDATES),
        )
```

### HubSpot Mock Adapter (`backend/adapters/hubspot.py`)

```python
from datetime import datetime
from .base import BaseAdapter, AdapterCandidate, AdapterRole, AdapterStatus


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

    # 16 realistic UK-market candidates with CRM-style contact data
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
```

### LinkedIn Mock Adapter (`backend/adapters/linkedin.py`)

```python
from datetime import datetime
from .base import BaseAdapter, AdapterCandidate, AdapterRole, AdapterStatus


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

    # 15 realistic UK-market candidates with LinkedIn-style profile data
    MOCK_CANDIDATES = [
        {
            "profileId": "LI-3001",
            "headline": "Senior Backend Engineer at Revolut | Python, FastAPI, Distributed Systems",
            "firstName": "James",
            "lastName": "Hartley",
            "email": None,  # LinkedIn often doesn't share email
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
```

### Tests (`backend/tests/test_adapters.py`)

```python
import pytest
from adapters.base import BaseAdapter, AdapterCandidate, AdapterStatus
from adapters.bullhorn import BullhornAdapter
from adapters.hubspot import HubSpotAdapter
from adapters.linkedin import LinkedInAdapter
from adapters.registry import AdapterRegistry, init_adapters


@pytest.mark.asyncio
async def test_bullhorn_fetch_candidates():
    adapter = BullhornAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 18
    assert all(isinstance(c, AdapterCandidate) for c in candidates)
    assert all(c.adapter_name == "bullhorn" for c in candidates)
    # Verify ATS-specific fields exist
    assert "employmentHistory" in candidates[0].raw_data
    assert "skillList" in candidates[0].raw_data


@pytest.mark.asyncio
async def test_hubspot_fetch_candidates():
    adapter = HubSpotAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 16
    assert all(c.adapter_name == "hubspot" for c in candidates)
    # Verify CRM-specific fields exist
    assert "properties" in candidates[0].raw_data
    assert "engagement_score" in candidates[0].raw_data["properties"]


@pytest.mark.asyncio
async def test_linkedin_fetch_candidates():
    adapter = LinkedInAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 15
    assert all(c.adapter_name == "linkedin" for c in candidates)
    # Verify profile-specific fields exist
    assert "skills" in candidates[0].raw_data
    assert "endorsements" in candidates[0].raw_data["skills"][0]


@pytest.mark.asyncio
async def test_bullhorn_has_roles():
    adapter = BullhornAdapter()
    roles = await adapter.fetch_roles()
    assert len(roles) > 0


@pytest.mark.asyncio
async def test_hubspot_no_roles():
    adapter = HubSpotAdapter()
    roles = await adapter.fetch_roles()
    assert roles == []


@pytest.mark.asyncio
async def test_linkedin_no_roles():
    adapter = LinkedInAdapter()
    roles = await adapter.fetch_roles()
    assert roles == []


@pytest.mark.asyncio
async def test_adapter_status():
    for AdapterClass in [BullhornAdapter, HubSpotAdapter, LinkedInAdapter]:
        adapter = AdapterClass()
        status = await adapter.get_status()
        assert isinstance(status, AdapterStatus)
        assert status.connected is True
        assert status.records_available > 0


def test_registry():
    registry = AdapterRegistry()
    registry.register(BullhornAdapter())
    registry.register(HubSpotAdapter())
    registry.register(LinkedInAdapter())
    assert len(registry.list_names()) == 3
    assert registry.get("bullhorn").name == "bullhorn"
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_init_adapters():
    registry = init_adapters()
    assert "bullhorn" in registry.list_names()
    assert "hubspot" in registry.list_names()
    assert "linkedin" in registry.list_names()
```

## Outputs
- `backend/adapters/__init__.py`
- `backend/adapters/base.py`
- `backend/adapters/registry.py`
- `backend/adapters/bullhorn.py`
- `backend/adapters/hubspot.py`
- `backend/adapters/linkedin.py`
- `backend/tests/test_adapters.py`

## Acceptance Criteria
1. All three adapters instantiate and implement `BaseAdapter` interface
2. `BullhornAdapter.fetch_candidates()` returns 18 records with work history
3. `HubSpotAdapter.fetch_candidates()` returns 16 records with engagement data
4. `LinkedInAdapter.fetch_candidates()` returns 15 records with skills/endorsements
5. `BullhornAdapter.fetch_roles()` returns at least 2 roles
6. HubSpot and LinkedIn return empty role lists
7. All adapters return healthy status from `get_status()`
8. Registry can register, lookup, and list all adapters
9. Some candidates intentionally overlap across adapters (James Hartley, Ben Cooper, etc.) for dedup testing
10. `python -m pytest tests/test_adapters.py -v` — all tests pass

## Handoff Notes
- **To Task 05:** Adapters return `AdapterCandidate` with `raw_data` dict. Each adapter has different field names/structure. Normalization must handle: Bullhorn `skillList` (comma-separated string), HubSpot `properties.tags` (array), LinkedIn `skills` (array of {name, endorsements}). Several candidates appear across multiple adapters to test dedup (e.g., James Hartley in all three, Ben Cooper in HubSpot + LinkedIn, Emma Williams in Bullhorn + LinkedIn).
- **To Task 06:** Overlap candidates for dedup testing: James Hartley (all 3 adapters, same email), Ben Cooper (HubSpot + LinkedIn, same email), Mohammed Hassan (Bullhorn + LinkedIn, same email), Ravi Patel (Bullhorn + LinkedIn, same email), George Papadopoulos (Bullhorn + LinkedIn, no shared email — fuzzy match needed).
- **Decision:** Each adapter returns raw data in its own format, not canonical. This is intentional — it tests the normalization pipeline's ability to handle heterogeneous data.
