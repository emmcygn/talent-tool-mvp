from datetime import datetime

from .base import AdapterCandidate, AdapterRole, AdapterStatus, BaseAdapter


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
