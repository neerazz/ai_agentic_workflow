"""
Defines the LinkedIn Profile Analyst Agent for the blog creation workflow.
This agent extracts expertise and story potential from professional experience.
"""
import logging

from crewai import Agent
from crewai import Task, Crew, Process

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

user_profile_analysis = """
Neeraj Kumar Singh Beshane’s 14-year career in software engineering has equipped him with a broad and deep technical skill set. He has hands-on experience across programming languages, cloud platforms, architecture frameworks, and DevOps tools – all applied to deliver high-impact solutions in domains ranging from finance to e-commerce to emerging tech. Below is a breakdown of his core technical proficiencies and estimated years of experience, with context from his roles:

* **Programming Languages:** **Java (12+ years)** – Primary language used throughout his career for building enterprise applications and high-performance microservices. **Python (3+ years)** – Utilized for scripting and developing backend services, such as a Kubernetes policy engine to automate security checks. He has also worked with **Groovy** in tandem with Java for API development, and even has early-career exposure to **REXX** on mainframe systems, which he leveraged to automate manual processes.

* **Cloud & Container Platforms:** Proficient in deploying and scaling applications on cloud infrastructure. **AWS (4+ years)** – Designed cloud architectures on AWS, including an EKS (Elastic Kubernetes Service) cluster that handles over 12,000 transactions per second for a crypto trading platform. **Google Cloud (2+ years)** – Built data pipelines and analytics solutions using GCP services like BigQuery (e.g. streaming security data into BigQuery for analysis). **Pivotal Cloud Foundry (3+ years)** – Managed enterprise cloud deployments on PCF, using IaC tools (Terraform) to provision and maintain environments. **Kubernetes (5+ years)** – Extensive experience containerizing applications and orchestrating them with Kubernetes, both on cloud (AWS EKS) and on-prem platforms, to ensure scalable and resilient deployments.

* **DevOps & CI/CD Tooling:** Strong background in automating software delivery. Proficient with **CI/CD pipelines** using tools like Jenkins and GitHub/Argo workflows. For instance, he built fully automated Jenkins pipelines deployed on Kubernetes at JPMorgan, boosting deployment frequency by 40%. He also implemented **GitOps** practices with ArgoCD to achieve zero-downtime continuous deployments in a production crypto exchange environment. In addition, Neeraj applies **Infrastructure as Code (Terraform)** to manage cloud resources, enabling consistent and reproducible environments. This DevOps skill set, combined with his scripting abilities, allowed him to streamline releases and configuration management across organizations.

* **Frameworks & Architectural Patterns:** Expert in modern application frameworks, especially in the Java ecosystem. He has \~10 years of experience with **Spring/Spring Boot**, using it to modernize legacy systems and build new microservices. At American Express, for example, he re-architected a monolithic system with Spring Boot, cutting 60% of the code and drastically improving performance. He designs **microservices** architectures (RESTful APIs and event-driven services) and has implemented patterns like **Saga** for complex transaction management in distributed systems. Neeraj is also familiar with **GraphQL** API design from his work building real-time data retrieval services in Java/Groovy, and he has developed traditional **SOAP** web services for integration with voice systems. His architectural expertise extends to designing for high throughput and fault tolerance, leveraging patterns such as two-phase commit, event sourcing, and reactive programming (which he has also mentored teams on).

* **Security & Quality Engineering:** Focused on building **secure** and reliable software. Neeraj has led DevSecOps initiatives, implementing security automation at scale. He developed a real-time **vulnerability detection** pipeline (using Spring Cloud Data Flow and Kafka) that proactively scans thousands of applications, improving incident response times by 40%. He’s integrated authentication/authorization frameworks, rolling out SSO solutions with providers like SiteMinder and OAuth2 to protect enterprise APIs, and even built an authentication server with two-step verification for a high-load environment. In terms of quality, he has implemented comprehensive **automated testing** regimes: for example, creating cloud-based integration test frameworks with Selenium and Cucumber that reduced customer-reported issues by 25%. He also emphasizes performance testing and tuning – employing tools like WireMock and Gatling to identify bottlenecks in high-volume systems, thereby improving response times in mission-critical platforms.

*(The above skills are backed by diverse project experience, as detailed in the following sections.)*

# Human Stories from Job Transitions and Projects

Neeraj’s career is marked by pivotal transitions and project milestones that illustrate his growth and adaptability. Each move wasn’t just a change of job, but a chapter in a larger story of personal and professional development:

**1. From Customer Service to Software Development:** Neeraj’s journey into tech had an unconventional start. After earning his engineering degree, he initially worked as an inbound customer service representative for a telecom provider. In this role, he honed soft skills like communication, empathy, and problem solving under pressure – skills that would later complement his technical abilities. Determined to break into software development, he made a bold transition in 2011: leaving the call center and joining Tata Consultancy Services (TCS) as a junior **Mainframe Programmer**. This move – from handling customer complaints to debugging code and batch processes – was challenging, but it laid the foundation for his IT career. It’s a classic “struggle-to-opportunity” story: starting on the helpdesk frontlines gave him a user-centric perspective, which he carried into his new life as a developer.

**2. Growing Through Global Experience at TCS:** During his \~4.5 years at TCS, Neeraj progressed from a mainframe support role to leading modules in a large-scale financial software project. Early on, he was maintaining legacy systems for a multinational accounts platform, learning the importance of reliability and attention to detail in mission-critical environments. As he proved himself, he moved into modern application development – working with Java, JSP, Spring, and Hibernate to build new modules for a global loyalty and accounting system. A highlight was being sent to **Montevideo, Uruguay** for a year-long assignment as a Senior Programmer. This overseas stint was a story in itself: adapting to a new culture and collaborating with international teams broadened his outlook. Neeraj also demonstrated initiative by creating automation scripts (using REXX) to reduce manual effort for his team, an early sign of his penchant for efficiency. By the time he became a Module Lead at TCS, he had learned how to coordinate distributed teams, manage software releases, and drive process improvements – experiences that shaped his leadership skills going forward.

**3. Modernizing Legacy Systems at American Express:** In 2016, Neeraj made a significant transition from the IT services world to a direct role at **American Express** as a Senior Software Developer. This move was a turning point: he was now tasked with leading development on AmEx’s International Insurance Services platform. Here, Neeraj encountered a classic legacy **monolith** – a large, aging application handling claims processing. Rather than be daunted, he spearheaded a major modernization effort. He **re-architected the monolithic system into a set of streamlined microservices** using Java 8 and Spring Boot. The results were dramatic: a 60% reduction in code across key services and response times improved from 1.5 seconds to 0.5 seconds (a \~66% performance boost). This “before-and-after” story became a highlight of his career – transforming a slow, unwieldy system into a lean, high-performing one. Neeraj also introduced new capabilities, such as RESTful microservices that allowed external insurance partners to securely access data (enhancing AmEx’s integrations), and built an event-driven notification service to keep customers informed on claim status. This role taught him how to drive large-scale technical change in a mission-critical product – a success that bolstered his reputation as an architect who can revive legacy systems.

**4. Integrating and Securing Systems at JPMorgan:** In 2019, Neeraj transitioned to **JPMorgan Chase** as a Senior Software Engineer, entering the world of corporate investment banking technology. Here, he took on the challenge of integrating disparate enterprise systems. One of his notable projects was the *Escrow Specialty Accounting Portal*, where he noticed that users and support teams struggled because data was siloed in three different systems. Neeraj led an initiative to **merge data from those systems**, implementing a unified solution that eliminated redundant lookups – this proactive integration effort resulted in a 30% reduction in support call volume, directly improving client experience. During his JPMorgan tenure, he also evolved into a **security champion**. He was appointed the “Security Expert” for his line of business, tasked with protecting APIs and sensitive financial data. He developed reusable security frameworks, introducing single sign-on (SSO) and OAuth2 authentication across applications to strengthen access control. Additionally, Neeraj embraced DevOps culture: he used Terraform to provision infrastructure on Pivotal Cloud Foundry and built CI/CD pipelines with Jenkins that deployed microservices to Kubernetes, accelerating release cycles by 40%. This period of his career is a story of broadening scope – he wasn’t just writing code, but also ensuring that code was secure, scalable, and delivered efficiently. It was a growth moment where he combined his developer skills with architectural vision and security awareness, making him a well-rounded engineering leader.

**5. Driving DevSecOps Innovation at Wayfair:** In early 2022, Neeraj took on a new role as Principal Software Engineer (Technical Architect) at **Wayfair**, an e-commerce giant, marking a shift from finance to retail tech. This transition came with the challenge of scale and a new domain focus: **application and infrastructure security** for a sprawling microservices ecosystem. Neeraj led pivotal DevSecOps initiatives across *20,000+ applications* – an almost unprecedented scope. One key story from Wayfair is how he **developed a real-time vulnerability detection system**. He spearheaded and coded a solution using Spring Cloud Data Flow for streaming data and analytics, which could automatically detect security vulnerabilities across all those services in real time. This innovation improved incident response times by 40%, turning security from a reactive process into a proactive one. Moreover, he didn’t just architect from a high level; he got his hands dirty by writing code. For instance, he built a Python-based policy engine on Kubernetes to enforce security policies automatically during deployments. He also engineered a high-throughput vulnerability management system (processing 50+ million checks monthly) using Java on Kubernetes – showcasing his ability to handle big data volumes and high concurrency. Beyond security, he tackled identity and access management, developing an authentication server with two-factor authentication to bolster user security. Neeraj’s tenure at Wayfair is a narrative about being an **innovator and mentor**: he introduced cutting-edge security tooling in a complex environment and guided teams on best practices. It cemented his expertise in marrying development with security at massive scale.

**6. Rapid Greenfield Delivery at CoinFlip (Crypto Startup):** Neeraj’s next move was a bold step into the cryptocurrency space. In February 2024, he joined **CoinFlip** as a Principal Software Architect. Unlike his previous large-company roles, CoinFlip was a fast-paced startup environment – and it came with a dramatic story: **build a new crypto trading platform from scratch and launch it in just four months**. Neeraj led the architecture and delivery of this platform, essentially sprinting through a project that might normally take a year or more. He designed a microservices-based system to support real-time crypto transactions, focusing on both speed and reliability. Under his guidance, the team stood up a **Kubernetes-driven infrastructure on AWS** (EKS) capable of handling **12,000+ transactions per second** to meet the high-performance demands of crypto trading. Achieving this scalability on a compressed timeline was no small feat – it required clever design (like using Saga patterns and dual-phase commit for transaction consistency) and rigorous performance tuning. Neeraj implemented a performance testing framework with WireMock and Gatling to hunt down latency issues proactively, resulting in a smooth, low-latency trading experience. He also set up modern DevOps pipelines (GitOps with ArgoCD) to allow frequent, zero-downtime deployments, ensuring that new features and fixes could be rolled out continuously even post-launch. This experience at CoinFlip is a classic **startup struggle-to-success story**: extreme time pressure, the need to wear multiple hats, and the challenge of building reliable fintech infrastructure quickly. Delivering the platform on schedule was a testament to Neeraj’s ability to apply his extensive knowledge to a blank slate scenario and to lead a team through an intense, rewarding sprint.

**7. Innovating in Meta’s Reality Labs:** In mid-2024, Neeraj reached another milestone by joining **Meta (Facebook) Reality Labs** as a Staff Software Engineer. This role places him at the cutting edge of technology, working on the infrastructure that supports Meta’s augmented and virtual reality initiatives. The story here is about internal innovation: Neeraj is leading efforts to **revolutionize the build and CI (Continuous Integration) systems** for Reality Labs’ engineering teams. One of the challenges he’s tackling is unifying disparate build pipelines – for example, bridging Android Open Source Project (AOSP) builds with Meta’s internal monolithic codebase processes – into a single **schema-driven framework**. This kind of work is largely behind-the-scenes but critical; it aims to dramatically improve developer productivity and consistency across hardware, firmware, and application teams. What makes this chapter exciting is that Neeraj is leveraging everything he’s learned so far (cloud, CI/CD, microservices) and pushing into new territory with **AI-driven automation**. In fact, he is exploring the use of **Large Language Models (LLMs) to enhance CI/CD automation**, reflecting his forward-looking approach to tech. While this Meta role is ongoing, it represents how Neeraj continues to embrace big challenges. It’s the story of stepping into a top-tier tech company and immediately taking the initiative to drive improvement in the engineering process itself. For blog readers and colleagues, this is an evolving narrative of how a seasoned engineer applies his expertise in a cutting-edge field – essentially **shaping the future of how AR/VR software is built** within a company known for its innovation.

Each of these transitions – from the call center to TCS, TCS to Amex, Amex to JPMorgan, and so on – highlights a **“story moment.”** Whether it’s transforming a legacy platform, scaling security solutions, or launching a new product under pressure, Neeraj has consistently turned challenges into achievements. These moments form the backbone of his personal brand as a technologist who is adaptable, impact-driven, and always ready to write the next chapter of innovation.

# Struggle-to-Success Narratives

Throughout his career, Neeraj has encountered significant challenges that he turned into success stories. These struggle-to-success narratives not only demonstrate his resilience and problem-solving approach but also make for engaging storytelling themes (especially useful for blogs or interviews). Here are a few standout examples:

* **Breaking into Tech Against the Odds:** *Struggle:* Coming from a non-software background and starting out in a customer service job, Neeraj had to work extra hard to pivot into development. He had no professional coding experience when he decided to leave the call center and join TCS as a junior programmer. *Success:* Through determination and quick learning, he successfully transitioned to a software career. This journey from taking customer calls to writing code is inspiring for anyone starting unconventionally – it shows that with passion and effort, you can break into the tech industry and excel.

* **Legacy Monolith to Lightning-Fast Microservices:** *Struggle:* At American Express, Neeraj inherited a monolithic claims processing system that was slow (1.5s response times), bulky, and hard to maintain. Modernizing such a large legacy codebase can be like changing a plane’s engine mid-flight – high risk and technically arduous. *Success:* Neeraj led a complete overhaul using modern Java and Spring Boot. He managed to **reduce the codebase by 60%** and **improve performance by 66%** (bringing response time down to 500ms). The once-creaky system became nimble and efficient. This narrative of simplifying complexity – turning a resource-intensive monolith into lean microservices – is a powerful example of technical transformation under pressure. It highlights how he navigated the uncertainty of a major refactor and delivered a big win.

* **Securing 20,000 Applications – from Chaos to Control:** *Struggle:* When tasked with DevSecOps at Wayfair, Neeraj faced a colossal challenge: thousands of applications and an ever-evolving landscape of vulnerabilities. Initially, security issues were handled in silos or after the fact, leading to slower responses and potential risks across the enterprise. The volume was overwhelming – how do you even begin to monitor and secure so many services continuously? *Success:* Neeraj architected an automated, real-time vulnerability **detection system that scanned all 20K+ apps**, turning security management from reactive firefighting into proactive monitoring. By building a streaming pipeline and policy engine, he achieved a **40% improvement in incident response times**. In practice, this meant threats were identified and addressed much faster than before, despite the huge scale. This story is compelling because it showcases creative problem-solving: he combined big data engineering with security domain knowledge to tame an “unwieldy beast.” It’s a true victory of automation and smart design over complexity, likely involving overcoming skepticism and rallying teams to adopt new processes.

* **Startup Sprint – Launching a Crypto Platform in Four Months:** *Struggle:* In a startup environment at CoinFlip, the clock was ticking loudly. Neeraj had to deliver a fully functional cryptocurrency trading platform *end-to-end* in just 4 months – a timeline that seemed nearly impossible given the need for robust trading engines, security, and scalability. The pressure was immense: limited time, a small team, and a high expectation for performance (thousands of transactions per second, zero downtime). *Success:* Neeraj not only met the deadline, he built the platform to handle **12,000+ TPS with high reliability**. He accomplished this by leveraging cloud infrastructure (Kubernetes on AWS) and microservices design, and by rigorously testing performance bottlenecks early (using tools like Gatling) to ensure the system could scale on day one. The product launched on schedule, a rare feat in fintech. This narrative resonates as a classic startup triumph: a small team beating the odds through focus, smart technical choices, and sheer hard work. For a blog post, it would provide lessons on rapid development, prioritization, and staying calm (and effective) under extreme deadlines.

Each of these narratives follows a “hero’s journey” arc – an initial struggle or obstacle, a series of deliberate actions, and a successful outcome with tangible results. They are rich material for personal storytelling, whether in a blog, a talk, or an interview. By sharing these stories, Neeraj can illustrate not just what he accomplished, but **how** he thinks and overcomes challenges – a key aspect of personal brand for someone in a senior engineering role.

# Technology in Action: Real-World Mapping

One of the strengths of Neeraj’s profile is how he applies cutting-edge technologies to solve real business problems. Instead of just listing buzzwords, he has concrete examples of how each technology was used in context. Here we map several key technologies to the real-world scenarios and projects where Neeraj made an impact:

* **Kubernetes & Cloud Scalability:** Neeraj has repeatedly used Kubernetes to achieve scalability and resilience in projects. For example, at CoinFlip he **designed a Kubernetes cluster on AWS EKS** to power a trading platform that handles 12,000+ transactions per second. This meant containerizing microservices and orchestrating them to auto-scale across nodes, ensuring high availability during crypto market spikes. Likewise, at Wayfair he deployed security workloads to Kubernetes, such as a high-throughput vulnerability scanner that ran across the cluster to process millions of security checks. These scenarios show Kubernetes in action – not as a goal by itself, but as a tool enabling real-time trading and enterprise-scale security monitoring.

* **Saga Pattern for Distributed Transactions:** In systems where multiple services must update data consistently (like financial transactions), Neeraj implemented the Saga pattern to maintain data integrity. At JPMorgan, he developed a **payment microservice using the saga pattern** to coordinate transactions across accounts in near real-time. This allowed 10,000+ daily account transactions to proceed safely without a central monolith, even if partial failures occurred. Similarly, in the CoinFlip platform, he applied Saga orchestration for order processing and settlement across microservices, ensuring that even if one step failed, the system could compensate or retry without corrupting data. These use-cases demonstrate how Neeraj uses advanced architectural patterns to solve the real problem of consistency in distributed systems.

* **Spring Boot Microservices and Legacy Modernization:** Neeraj frequently leverages **Spring Boot** to rapidly build and deploy microservices. At American Express, he transformed a legacy insurance application into lean **Spring Boot services**, which significantly reduced code complexity and improved performance. By breaking features into independent Spring Boot applications (for claims data, notifications, etc.), he improved maintainability and deployment agility. Additionally, at JPMorgan he built new **RESTful and GraphQL APIs using Spring Boot** and Java/Groovy to expose financial data in real-time for the Escrow platform. In practice, this meant internal and external clients could fetch up-to-the-minute data via lightweight services, a big improvement over older systems. These examples map the use of modern Java frameworks to tangible outcomes: cleaner codebases, faster response times, and more accessible services.

* **DevSecOps and Streaming Data Pipelines:** To address security at scale, Neeraj innovated by combining data streaming technologies with security analytics. At Wayfair, he built a **real-time vulnerability detection pipeline** – essentially a custom security analytics platform – using **Spring Cloud Data Flow for stream processing and Kafka for data transport**. In real terms, this pipeline would ingest security event data (vulnerability scan results, application logs) via Kafka topics and process them in streaming fashion to identify critical issues instantly. He also integrated this with Google BigQuery for large-scale analysis and reporting. By mapping cloud data tools to the security domain, Neeraj created an immune system for Wayfair’s applications. This project shows how technologies like Kafka, big data, and stream processors can be applied to solve the **real-world problem of monitoring thousands of apps for vulnerabilities in real time**.

* **CI/CD Automation and Infrastructure as Code:** Neeraj’s use of automation tools translates directly into faster and more reliable releases. For instance, at JPMorgan he **built CI/CD pipelines with Jenkins that deploy on Kubernetes**, which increased deployment frequency by 40%. This means developers could push updates more often without manual intervention, resulting in more iterative improvements and less downtime. He also utilized **Terraform (Infrastructure as Code)** for managing environments in Pivotal Cloud Foundry – a real-world example of how codifying infrastructure leads to consistency and easy scalability (if a new environment was needed, Terraform scripts ensured it could be stood up exactly as the last). And in the CoinFlip project, he introduced **GitOps with ArgoCD** for continuous deployment – which meant that every code change, when merged, was automatically and safely rolled out to production via version-controlled manifests. These technologies in action led to tangible benefits: fewer deployment errors, ability to recover or replicate environments quickly, and engineers spending more time on code than on manual setups.

* **Quality Engineering (Testing & Performance):** In multiple roles, Neeraj mapped testing tools to the needs of the project to ensure quality. For example, to maintain high quality in JPMorgan’s banking apps, he set up a cloud-based **integration testing framework with Selenium and Cucumber**. This allowed automated browser tests and end-to-end scenarios to run regularly, catching issues before customers did – which directly led to a 25% drop in customer-reported issues. In performance-sensitive projects like the crypto platform, he employed **performance testing with WireMock and Gatling** early in development. By simulating loads and mocking external services, he could identify latency hotspots and optimize them, ensuring the system met its real-world performance targets. These efforts show how Neeraj uses testing technology as a proactive measure, mapping tools to specific project risks (be it user experience in a web app or throughput in a trading system) to deliver reliable software.

Each of the above points illustrates a simple idea: *technology is only as valuable as the results it produces.* Neeraj’s experience shows a pattern of selecting the right tool or tech stack for a given problem and executing it to achieve measurable outcomes – whether it’s higher TPS, faster deployments, or improved security posture. For a hiring manager or technical team, these mappings provide confidence that his skills aren’t just theoretical; they have been battle-tested in real projects with real stakes.

# Career Growth Patterns and Learning Moments

Looking over Neeraj’s career, certain patterns emerge in how he has grown and what he has learned at each stage. These patterns highlight not only the progression of his roles, but also the evolution of his mindset and expertise:

* **Cross-Domain Adaptability:** One striking pattern is Neeraj’s ability to apply his skills across multiple industries and problem domains. He has contributed to banking and finance, e-commerce, cybersecurity, loyalty programs, and even cryptocurrency. Each transition – from financial services to retail to startup fintech – required learning domain-specific knowledge (e.g., understanding banking regulations vs. e-commerce scale issues vs. crypto exchange mechanisms). His success in each field shows a **capacity to quickly absorb new domains** and find common patterns (like using microservices and security best practices everywhere). This adaptability also came from working in different cultural environments: starting his career in India, working in Latin America (Uruguay), and later across US-based companies. Such exposure taught him how to collaborate with diverse teams and customers, a skill that’s invaluable in global tech teams.

* **Steady Progression to Technical Leadership:** Over 14 years, Neeraj’s roles show a clear upward trajectory – from Programmer to Senior Developer to Principal Architect and now Staff Engineer. Each step up was marked by increased scope and leadership. At TCS he led modules and coordinated with offshore teams; by JPMorgan he was spearheading critical projects and acting as a domain expert; at Wayfair and CoinFlip he took on principal-level roles, setting technical direction; and at Meta he operates at *Staff Engineer* level, influencing engineering practices. This pattern indicates a **blend of technical excellence and leadership ability** – he consistently earned trust to drive bigger initiatives and mentor other engineers. A learning moment in this journey was moving from being an individual contributor to a mentor/leader. For example, at CoinFlip he **guided development leads** and fostered a culture of excellence. He also openly values mentorship and team development. This shows that as he grew, he learned to amplify his impact through others, not just through his own coding.

* **Innovation and Continuous Learning:** Neeraj has never stayed static with any single technology – a pattern of continuous upskilling is evident. Early on, he picked up mainframe skills but quickly moved into modern programming with Java and web frameworks. Later, he embraced cloud computing and containerization as those became prominent. Most recently, he’s delving into AI/ML integration with development pipelines (experimenting with **LLMs for CI/CD automation** at Meta). A key learning mindset here is **staying ahead of the curve**: he doesn’t hesitate to learn a new language, tool, or paradigm if it can solve a problem more effectively. For instance, when he saw the need for automating security policy enforcement, he learned and used Python for a Kubernetes policy engine, even though his core background was in Java. Likewise, tackling streaming data led him to BigQuery and Kafka. This pattern of embracing new tech ensured that he could drive innovation (not just follow established methods) and keep his skill set relevant. His career story reinforces the idea that a great engineer is always a student – each project brought a new lesson or technology to master.

* **Emphasis on Mentorship and Team Culture:** Another thread in Neeraj’s career is his focus on team success and knowledge sharing. He has often taken on mentorship roles – formally or informally – to uplift his teams. In TCS, he conducted knowledge transfer sessions to onboard new team members and spread best practices. In leadership positions, he has advocated for a culture of technical excellence and continuous improvement. He believes in fostering high-performing teams through mentorship. The learning moments here come from understanding that **great engineering is a team sport**. Neeraj likely learned early that sharing knowledge and grooming others not only improves project outcomes but also cements one’s own understanding. This collaborative ethos made it easier for him to lead larger endeavors – by the time he was at Wayfair or CoinFlip, he could rely on strong teams that he helped shape. For a hiring manager, this pattern signals that Neeraj isn’t just thinking about his own growth, but also about empowering those around him, which is critical for senior roles.

* **Outcome-Focused Problem Solving:** A consistent theme in Neeraj’s roles is his focus on achieving measurable results. Every major project he tackled had clear metrics of success – and he delivered on them. To highlight a few: reducing support calls by 30% through system integration, cutting response times by more than half, improving incident response by 40% with better tooling, increasing deployment frequency by 40% via CI/CD improvements, or launching a product in four months. This pattern shows that he approaches problems with a results-oriented mindset. The learning here is about prioritization and impact: he seems to consistently ask, *“What is the actual pain point, and how do we alleviate it in a tangible way?”* By focusing on outcomes (like performance, reliability, user satisfaction), he ensures that his technical solutions align with business or user needs. This not only makes his accomplishments stand out, but it also guides him in making the right technical choices (since the “right” choice is the one that best serves the end goal). It’s a growth from just executing tasks to strategically solving the right problems.

In summary, Neeraj’s career progression is not just a timeline of jobs, but a story of continuous growth. He learned **customer empathy** early on (from support to development), gained **technical depth** and then **breadth** (spanning legacy and cutting-edge tech), evolved into a **leader and mentor**, and maintained a relentless focus on **innovation and results**. These patterns collectively form a narrative of a professional who keeps challenging himself and leveling up – a compelling message for personal branding that shows he’s well-rounded and always moving forward.

"""

def get_profile_analyst_prompt(profile_data: str) -> str:
    """
    Returns the prompt for the LinkedIn Profile Analyst Agent.

    Args:
        profile_data (str): The LinkedIn profile data to analyze.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Analyze the following LinkedIn profile data to extract expertise and potential story narratives:

    Profile Data:
    {profile_data}

    Your task:
    1. Identify all technical skills and years of experience with each
    2. Extract potential "story moments" from job transitions and projects
    3. Find struggle-to-success narratives that could be used in blog posts
    4. Map technologies to real scenarios from their career
    5. Identify career progression patterns and learning moments

    Focus on finding human stories behind the technical experience that would resonate with junior to mid-level developers.

    OUTPUT FORMAT as JSON:
    {{
        "technical_expertise": {{
            "technology_name": {{
                "years": X,
                "proficiency": "expert/intermediate/learning",
                "story_snippets": ["specific project or challenge", "another story"]
            }}
        }},
        "career_stories": [
            {{
                "type": "challenge/learning/mentoring/success",
                "summary": "brief story description",
                "technologies": ["tech1", "tech2"],
                "lesson": "what readers can learn"
            }}
        ],
        "writing_angles": ["angle1", "angle2"],
        "target_audience_alignment": "how experience matches junior/mid dev needs"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

def get_profile_analyst_agent() -> Agent:
    """
    Initializes and returns the LinkedIn Profile Analyst Agent.

    This agent is responsible for analyzing LinkedIn profiles to identify
    compelling narratives and technical expertise suitable for blog content.

    Returns:
        Agent: The configured Profile Analyst Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        profile_analyst_llm = gpt4_client.get_llm()

        agent = Agent(
            role="LinkedIn Profile Analyst",
            goal="Extract expertise and story potential from professional experience",
            backstory=(
                "You are an expert at analyzing professional profiles to find "
                "compelling narratives and technical expertise that can be "
                "transformed into engaging blog content."
            ),
            llm=profile_analyst_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Profile Analyst Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Profile Analyst Agent: {e}")
        raise


if __name__ == "__main__":

    # Initialize the agent
    profile_analyst = get_profile_analyst_agent()

    # Example profile data
    example_profile_data = """
    John Doe is a Senior Software Engineer with 8 years of experience in developing
    scalable web applications using Python, Django, and AWS. He led a team of 5
    engineers to migrate a monolithic application to microservices, resulting in
    a 30% reduction in operational costs. He also enjoys mentoring junior developers.
    """

    # Get the prompt for the task
    task_description = get_profile_analyst_prompt(profile_data=example_profile_data)

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Expertise profile and story bank in JSON format",
        agent=profile_analyst
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[profile_analyst],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Profile Analyst Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Profile Analyst Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
