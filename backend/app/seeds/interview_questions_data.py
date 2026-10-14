"""
Curated Seed Question Bank for Phase 7.4: Database-Driven Interview Preparation.

Contains 110 high-quality, non-duplicated questions across 6 role families:
1. General HR & Behavioural (20 questions)
2. Data Analyst (18 questions)
3. Data Scientist (18 questions)
4. AI/ML Engineer (18 questions)
5. Full-Stack Developer (18 questions)
6. General Software Engineering & Project Discussion (18 questions)
"""

from typing import Any

CURATED_INTERVIEW_QUESTIONS: list[dict[str, Any]] = [
    # =========================================================================
    # 1. GENERAL HR & BEHAVIOURAL (20 questions)
    # =========================================================================
    {
        "identifier": "hr-beh-tell-me-about-yourself-01",
        "question_text": "Tell me about yourself and why you are interested in this career path.",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Communication", "Self-Awareness", "Career Goals"],
        "expected_points": [
            "Succinct elevator pitch summarizing academic or professional background",
            "Key technical or domain interests and major milestone projects",
            "Clear motivation connecting past experiences with current career objectives",
            "Professional forward-looking conclusion explaining interest in the role"
        ],
        "rubric": {
            "criteria": ["Conciseness & Structure", "Relevant Highlights", "Motivation & Enthusiasm"],
            "key_concepts": ["background", "education", "passion", "project", "experience", "goal", "role"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Use the Present-Past-Future model. Briefly explain your current focus and studies/work, highlight 1-2 pivotal projects or achievements that sparked your passion, and conclude with why this specific opportunity aligns with your growth trajectory.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-star-conflict-resolution-02",
        "question_text": "Describe a situation where you had a disagreement with a team member on a technical decision. How did you resolve it?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Conflict Resolution", "Collaboration", "Emotional Intelligence"],
        "expected_points": [
            "Context of the technical disagreement without placing personal blame",
            "Active listening and objective evaluation of both perspectives",
            "Use of objective benchmarks, proofs-of-concept, or team consensus to decide",
            "Positive outcome and maintenance of a strong working relationship"
        ],
        "rubric": {
            "criteria": ["STAR Method Application", "Empathy & Objectivity", "Constructive Resolution"],
            "key_concepts": ["situation", "disagreement", "perspective", "listen", "compromise", "data", "outcome"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Structure via STAR (Situation, Task, Action, Result). Emphasize separating ego from ideas, testing hypotheses or creating small prototypes to gather data, and respecting team decisions.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-handling-tight-deadlines-03",
        "question_text": "Tell me about a time when you were facing an aggressive deadline and realized you might not finish everything on time. What steps did you take?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Time Management", "Prioritization", "Communication"],
        "expected_points": [
            "Proactive identification of the bottleneck before the deadline arrived",
            "Transparent communication with stakeholders, mentors, or team members",
            "Triage and prioritization of core Must-Have features vs Nice-to-Have scope",
            "Reflections on post-mortem planning or mitigation for future projects"
        ],
        "rubric": {
            "criteria": ["Early Communication", "Ruthless Prioritization", "Delivery Ownership"],
            "key_concepts": ["deadline", "prioritize", "communicate", "scope", "stakeholder", "mvp", "result"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Detail how you communicated early rather than hiding the risk. Explain how you descoped non-critical elements to protect core functionality and how the final deliverable was successfully met.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-learning-new-technology-04",
        "question_text": "How do you approach learning a completely unfamiliar technology, framework, or domain when assigned to a new project?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Continuous Learning", "Adaptability", "Problem Solving"],
        "expected_points": [
            "Structured learning methodology: official documentation, starter tutorials, and sample repos",
            "Hands-on experimentation with a minimal working prototype",
            "Leveraging community resources, issue trackers, and asking targeted questions to peers",
            "Documenting findings and patterns for future reference"
        ],
        "rubric": {
            "criteria": ["Systematic Approach", "Hands-on Mindset", "Resourcefulness"],
            "key_concepts": ["documentation", "prototype", "experiment", "community", "practice", "learn"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Share a concrete example of a tool you recently mastered. Walk through your step-by-step process: reading docs, building a proof-of-concept, learning edge cases, and applying it productively.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-handling-critical-feedback-05",
        "question_text": "Can you give an example of receiving critical feedback on your work? How did you respond, and what changes did you make?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Receptiveness", "Professional Growth", "Resilience"],
        "expected_points": [
            "Specific instance of receiving constructive criticism on code, analysis, or design",
            "Non-defensive attitude and willingness to understand the underlying concern",
            "Actionable steps taken immediately to address the issue",
            "Long-term behavioral or technical improvement resulting from the feedback"
        ],
        "rubric": {
            "criteria": ["Humility & Receptivity", "Actionable Follow-through", "Sustained Growth"],
            "key_concepts": ["feedback", "critique", "listen", "improve", "adjust", "learn", "growth"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Avoid blaming others. Detail what the critique was (e.g. lack of unit test coverage, code readability, or slide clarity), how you welcomed the guidance, and how your subsequent work incorporated those standards.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-greatest-weakness-06",
        "question_text": "What do you consider to be an area of weakness or growth for you, and what concrete steps are you taking to improve?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Self-Awareness", "Integrity", "Self-Improvement"],
        "expected_points": [
            "Genuine, authentic weakness (not a cliché humblebrag like 'I work too hard')",
            "Explanation of how this area has impacted past work in minor ways",
            "Proactive system, habit, or strategy implemented to overcome it",
            "Evidence of recent progress or measurable improvement"
        ],
        "rubric": {
            "criteria": ["Authenticity", "Action Plan", "Measurable Progress"],
            "key_concepts": ["weakness", "growth", "habit", "improve", "system", "progress", "practice"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Pick a real professional skill (e.g. over-engineering initial prototypes, reluctance to ask for help early, or public presentation jitters). Explain the system you put in place to manage it (e.g. timeboxing spikes, drafting bullet summaries, seeking 10-minute check-ins).",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-project-failure-learnings-07",
        "question_text": "Tell me about a project that did not go as planned or failed. What was the root cause and what did you learn?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Accountability", "Post-Mortem Analysis", "Resilience"],
        "expected_points": [
            "Clear explanation of project goals and where expectations diverged",
            "Honest root cause analysis (e.g., misaligned requirements, technical oversight, lack of validation)",
            "Accountability taken without deflecting blame to teammates",
            "Concrete lessons learned that altered your subsequent engineering practices"
        ],
        "rubric": {
            "criteria": ["Ownership", "Root Cause Insight", "Practical Lessons"],
            "key_concepts": ["failure", "root cause", "assumption", "mistake", "lesson", "prevent", "improve"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Discuss an initiative where assumptions failed or architecture crumbled under real conditions. Focus heavily on the retrospection: what preventative habits, checks, or validation steps you instituted forever after.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-navigating-ambiguity-08",
        "question_text": "Describe a scenario where you were given vague or ambiguous requirements. How did you proceed to deliver successfully?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Autonomy", "Requirement Scoping", "Stakeholder Alignment"],
        "expected_points": [
            "Identification of ambiguous or missing specifications",
            "Proactive initiative to ask clarifying questions or draft an initial RFC/spec proposal",
            "Creation of rapid mockups or wireframes to align visual and functional expectations",
            "Iterative validation and regular check-ins with users or supervisors"
        ],
        "rubric": {
            "criteria": ["Initiative & Autonomy", "Clarification Strategy", "Iterative Alignment"],
            "key_concepts": ["ambiguous", "requirements", "clarify", "proposal", "prototype", "validate", "align"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Outline how you didn't freeze or wait passively. Describe how you wrote down your working assumptions, shared a lightweight proposal with options A and B, gathered feedback, and built incrementally.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-team-collaboration-diversity-09",
        "question_text": "How do you foster an inclusive and productive collaboration when working with people from diverse disciplines and backgrounds?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Teamwork", "Inclusivity", "Cross-Functional Collaboration"],
        "expected_points": [
            "Appreciation of diverse viewpoints (engineering, design, product, business)",
            "Adapting communication style to match non-technical or cross-functional partners",
            "Creating space for junior or quieter voices to contribute in meetings",
            "Establishing shared goals and clear documentation accessible to all"
        ],
        "rubric": {
            "criteria": ["Communication Empathy", "Inclusivity", "Cross-Functional Bridge"],
            "key_concepts": ["collaboration", "diverse", "perspective", "listen", "communication", "respect", "team"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Give examples of working across functions (e.g. designers, data engineers, product managers). Focus on breaking down technical jargon, establishing clear asynchronous documentation, and actively inviting feedback from everyone.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-prioritizing-multiple-tasks-10",
        "question_text": "When multiple urgent tasks or requests arrive at the same time, how do you decide what to work on first?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Prioritization", "Organization", "Task Management"],
        "expected_points": [
            "Framework for assessing urgency vs impact (e.g. Eisenhower matrix or business impact)",
            "Checking dependencies that might unblock other team members",
            "Communication with managers or requesters regarding realistic timelines and trade-offs",
            "Maintaining focus and avoiding multitasking inefficiencies"
        ],
        "rubric": {
            "criteria": ["Impact Assessment", "Dependency Awareness", "Clear Communication"],
            "key_concepts": ["priority", "impact", "urgency", "blocker", "communicate", "timeline", "tradeoff"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Explain your criteria: critical bug vs feature, who is blocked, and business SLA. Emphasize that when everything is urgent, you communicate trade-offs rather than silently overpromising and failing.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-mentoring-helping-peers-11",
        "question_text": "Describe a time when you helped a classmate or junior teammate overcome a challenging problem. What was your approach?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Mentorship", "Knowledge Sharing", "Patience"],
        "expected_points": [
            "Guiding the peer through problem diagnosis rather than merely writing the solution for them",
            "Asking probing questions to help them uncover the underlying mental model",
            "Patience and validation to build confidence",
            "Documenting the solution or pattern so the broader team benefits"
        ],
        "rubric": {
            "criteria": ["Empowerment Over Dictation", "Patience", "Knowledge Documentation"],
            "key_concepts": ["guide", "debug", "concept", "explain", "patience", "empower", "learn"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Highlight teaching the problem-solving mindset: showing them how to read error traces, isolate variables, and verify assumptions rather than typing the answer for them.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-ethical-dilemma-data-integrity-12",
        "question_text": "If you discovered a subtle bug or data integrity issue right before a major release that no one else noticed, what would you do?",
        "category": "HR/Behavioural",
        "difficulty": "Advanced",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Integrity", "Accountability", "Quality Assurance"],
        "expected_points": [
            "Immediate triage to assess the severity, blast radius, and security/data implications",
            "Transparent escalation to lead engineer, product manager, or release team",
            "Providing a concise summary of the issue along with viable mitigation options",
            "Commitment to doing what is right for end users and data integrity over superficial deadlines"
        ],
        "rubric": {
            "criteria": ["High Integrity", "Severity Triage", "Proactive Mitigation Options"],
            "key_concepts": ["integrity", "triage", "escalate", "risk", "mitigation", "data", "release"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Never sweep an issue under the rug. State that you would document reproduction steps, calculate risk, present options (hotfix vs release rollback vs feature flag disable), and uphold product reliability.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-staying-motivated-repetitive-tasks-13",
        "question_text": "Not every engineering or analytical task is glamorous. How do you stay motivated and deliver high quality during repetitive or mundane tasks?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Work Ethic", "Automation Mindset", "Consistency"],
        "expected_points": [
            "Recognizing how routine tasks contribute to overall system reliability and user trust",
            "Looking for opportunities to automate, script, or streamline the repetitive workflow",
            "Maintaining rigorous quality standards and peer review checklist discipline",
            "Setting personal micro-goals to maintain focus and efficiency"
        ],
        "rubric": {
            "criteria": ["Reliability Mindset", "Automation Drive", "Quality Consistency"],
            "key_concepts": ["automate", "script", "quality", "reliability", "discipline", "detail", "purpose"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Explain that mundane tasks (writing migration scripts, cleaning messy data, writing unit tests) are the backbone of stable software. Mention automating repetitive parts with scripts to improve efficiency.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-long-term-career-vision-14",
        "question_text": "Where do you see yourself in 3 to 5 years, and how does this entry-level or junior role fit into that trajectory?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Career Planning", "Ambition", "Commitment"],
        "expected_points": [
            "Realistic yet ambitious vision of technical depth and leadership growth",
            "Desire to transition from mentored execution to independent architectural ownership",
            "Concrete articulation of the skills this specific role builds",
            "Commitment to contributing long-term value to the organization"
        ],
        "rubric": {
            "criteria": ["Realistic Ambition", "Value Alignment", "Progression Path"],
            "key_concepts": ["growth", "skills", "depth", "ownership", "mentor", "impact", "trajectory"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Emphasize mastering core fundamentals in years 1-2, taking end-to-end ownership of major services or pipelines in years 3-4, and beginning to mentor new hires in year 5.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-handling-stressful-incidents-15",
        "question_text": "Describe a high-pressure situation, such as a production outage or exam crunch, and how you maintained composure to solve the problem.",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Stress Management", "Incident Response", "Composure"],
        "expected_points": [
            "Remaining calm, objective, and avoiding panic during critical alerts",
            "Methodical isolation of the symptom using logs, metrics, or recent deployments",
            "Prioritizing mitigation (restoring service) before deep root cause investigation",
            "Clear stakeholder communication during the incident and a thorough blameless post-mortem after"
        ],
        "rubric": {
            "criteria": ["Composure Under Pressure", "Systematic Debugging", "Blameless Post-Mortem"],
            "key_concepts": ["calm", "outage", "metrics", "isolate", "mitigate", "post-mortem", "restore"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Walk through how you calmed the emotional temperature, focused on observability data, rolled back or patched the breaking change, and later held a blameless post-mortem to ensure it never recurs.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-persuading-skeptical-stakeholders-16",
        "question_text": "How do you convince a manager or client to adopt an architectural change or refactor when they are hesitant to allocate time for it?",
        "category": "HR/Behavioural",
        "difficulty": "Advanced",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Persuasion", "Business Acumen", "Technical Debt"],
        "expected_points": [
            "Translating technical debt into business language: development velocity, downtime risk, and maintainability cost",
            "Gathering quantifiable data (e.g., bug counts, deployment latency, customer-reported issues)",
            "Proposing an incremental, low-risk rollout plan rather than a risky multi-month rewrite",
            "Demonstrating ROI with a small proof-of-concept"
        ],
        "rubric": {
            "criteria": ["Business Translation", "Quantitative Evidence", "Incremental Migration"],
            "key_concepts": ["business", "risk", "velocity", "debt", "metrics", "incremental", "roi"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Frame technical debt in terms business stakeholders care about: developer hours spent fixing recurring regressions, server cost, or churn risk. Propose tackling it incrementally in 10-15% sprint budgets.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-cultural-values-alignment-17",
        "question_text": "What type of team culture enables you to perform at your best, and what do you do to contribute positively to team morale?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Culture Fit", "Team Dynamics", "Positivity"],
        "expected_points": [
            "Appreciation for psychological safety, open discourse, and blameless problem solving",
            "Valuing high engineering craft and continuous code review culture",
            "Active contributions to team morale: celebrating peer wins, sharing useful articles, being approachable",
            "Respecting asynchronous workflows and work-life balance"
        ],
        "rubric": {
            "criteria": ["Psychological Safety", "Constructive Contribution", "Self-Awareness"],
            "key_concepts": ["psychological safety", "openness", "celebrate", "feedback", "support", "culture", "morale"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): State that you thrive in an environment of high accountability paired with high psychological safety—where people question code without questioning character and celebrate team accomplishments.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-handling-competing-opinions-18",
        "question_text": "When two senior team members give you conflicting advice on how to build a feature, how do you handle it without causing friction?",
        "category": "HR/Behavioural",
        "difficulty": "Intermediate",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Diplomacy", "Decision Making", "Alignment"],
        "expected_points": [
            "Synthesizing the pros and cons of both approaches objectively",
            "Bringing both parties into a joint discussion or shared thread with a comparison document",
            "Focusing the evaluation on project constraints (latency, timeline, maintainability)",
            "Documenting the agreed decision in an ADR (Architectural Decision Record)"
        ],
        "rubric": {
            "criteria": ["Diplomacy", "Objective Evaluation", "Documented Alignment"],
            "key_concepts": ["tradeoff", "document", "pros and cons", "joint discussion", "adr", "consensus", "align"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Rather than playing messenger between seniors, create a 1-page comparison table highlighting performance, maintenance, and delivery timelines, then invite them to a brief sync to agree on the best fit for project constraints.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-delivering-bad-news-19",
        "question_text": "Have you ever had to deliver disappointing news to a manager, client, or team lead? How did you approach the conversation?",
        "category": "HR/Behavioural",
        "difficulty": "Advanced",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Executive Communication", "Transparency", "Problem Solving"],
        "expected_points": [
            "Delivering the news promptly without sugarcoating or delaying",
            "Clear explanation of what happened and why",
            "Coming with prepared solution alternatives or recovery plans, not just problems",
            "Follow-up milestones to track recovery"
        ],
        "rubric": {
            "criteria": ["Timely Candor", "Prepared Alternatives", "Accountability"],
            "key_concepts": ["transparency", "prompt", "solution", "alternatives", "recovery", "ownership", "plan"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Never wait until the 11th hour. State the facts clearly, present 2-3 actionable remediation paths, and ask for their strategic input on the preferred recovery trajectory.",
        "is_active": True,
    },
    {
        "identifier": "hr-beh-why-this-company-20",
        "question_text": "Why do you want to join our organization specifically, and how do our mission and products resonate with you?",
        "category": "HR/Behavioural",
        "difficulty": "Beginner",
        "role_tags": ["General", "All Roles"],
        "is_general": True,
        "skill_tags": ["Company Research", "Motivation", "Strategic Fit"],
        "expected_points": [
            "Demonstrated research into the company's real products, engineering blog, or business challenges",
            "Connection between personal values or career curiosities and the company's mission",
            "Excitement about specific engineering problems the team is solving",
            "Thoughtful questions demonstrating genuine long-term interest"
        ],
        "rubric": {
            "criteria": ["Company Specificity", "Authentic Alignment", "Enthusiasm"],
            "key_concepts": ["product", "mission", "research", "engineering", "challenge", "values", "impact"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Connect specific technological or domain problems the company tackles with your personal interests. Mention a recent blog post, feature release, or tech stack detail that genuinely intrigued you.",
        "is_active": True,
    },

    # =========================================================================
    # 2. DATA ANALYST (18 questions)
    # =========================================================================
    {
        "identifier": "da-tech-sql-joins-and-nulls-01",
        "question_text": "Explain the practical differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN. How do NULL values affect aggregations like COUNT() and AVG()?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["SQL", "Relational Databases", "Data Aggregation"],
        "expected_points": [
            "Accurate definitions and visual/set mental model of INNER vs LEFT vs FULL OUTER JOINs",
            "Handling of non-matching rows and resulting NULL placeholders in outer joins",
            "Behavior of COUNT(column) which ignores NULLs vs COUNT(*) which counts all rows",
            "Behavior of AVG() which ignores NULL values rather than treating them as 0"
        ],
        "rubric": {
            "criteria": ["Join Accuracy", "Null Handling in Functions", "Practical SQL Examples"],
            "key_concepts": ["inner join", "left join", "full outer", "null", "count(*)", "count(col)", "avg"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Define each join set: INNER returns matching rows in both tables; LEFT returns all left rows plus matching right rows (NULLs for unmatched); FULL OUTER returns all rows from both. Point out that COUNT(col) excludes NULLs, and AVG() calculates sum/non-null count, which can skew business numbers if NULL represents zero.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-window-functions-02",
        "question_text": "What are SQL window functions? Explain the difference between ROW_NUMBER(), RANK(), and DENSE_RANK() with an example scenario.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist", "Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["SQL", "Window Functions", "Analytics"],
        "expected_points": [
            "Definition of window functions calculating across sets of rows without collapsing them like GROUP BY",
            "ROW_NUMBER() provides strictly unique sequential integers regardless of ties",
            "RANK() assigns same rank to ties and skips subsequent numbers (e.g. 1, 2, 2, 4)",
            "DENSE_RANK() assigns same rank to ties without skipping numbers (e.g. 1, 2, 2, 3)",
            "Syntax structure: OVER (PARTITION BY ... ORDER BY ...)"
        ],
        "rubric": {
            "criteria": ["Partition Concept", "Ranking Differentiation", "Syntax Knowledge"],
            "key_concepts": ["partition by", "order by", "row_number", "rank", "dense_rank", "ties", "window"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Contrast window functions with GROUP BY: window functions retain row identity. Walk through identical scores: with values [100, 90, 90, 80], ROW_NUMBER gives 1,2,3,4; RANK gives 1,2,2,4; DENSE_RANK gives 1,2,2,3.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-ab-testing-fundamentals-03",
        "question_text": "How do you design and evaluate an A/B test for a product feature? What are sample size determination, p-values, and statistical power?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["A/B Testing", "Statistics", "Hypothesis Testing"],
        "expected_points": [
            "Formulating clear null (H0) and alternative (H1) hypotheses with a primary business metric",
            "Sample size calculation based on baseline conversion, Minimum Detectable Effect (MDE), alpha, and power",
            "Explanation of p-value as probability of observing results as extreme given H0 is true",
            "Statistical power (1 - beta) to avoid Type II false negatives",
            "Checking for test threats: sample ratio mismatch (SRM), seasonality, or novelty effects"
        ],
        "rubric": {
            "criteria": ["Hypothesis Formulation", "Statistical Rigor", "Threats & Practicalities"],
            "key_concepts": ["null hypothesis", "p-value", "significance", "power", "sample size", "mde", "srm"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Describe the lifecycle: Define metric (e.g. checkout conversion), calculate sample size upfront using power=0.80 and alpha=0.05, split traffic randomly, check for SRM, run until planned duration, and interpret confidence intervals alongside business context.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-data-cleaning-outliers-04",
        "question_text": "When you receive a messy dataset with missing values and extreme outliers, how do you systematically diagnose and clean it?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Data Cleaning", "Data Quality", "EDA", "Python/Pandas"],
        "expected_points": [
            "Exploratory data profiling: distributions, summary statistics, missingness mechanisms (MCAR, MAR, MNAR)",
            "Strategies for missing data: imputation (median/mode/KNN) vs removal based on business impact",
            "Outlier detection techniques: IQR method (1.5*IQR), z-scores, boxplots",
            "Distinguishing data entry errors from legitimate extreme business events",
            "Documenting all cleaning transformations reproducibly in code"
        ],
        "rubric": {
            "criteria": ["Exploratory Profiling", "Outlier Techniques", "Reproducibility"],
            "key_concepts": ["missing values", "imputation", "outliers", "iqr", "distribution", "profile", "pandas"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Begin with profiling (df.describe(), missing heatmaps). For missing values, never blindly drop rows without checking bias. For outliers, check IQR and z-scores, verify if they represent fraud or high-value whales before truncating or winsorizing.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-bi-dashboard-design-05",
        "question_text": "What principles do you follow when designing an executive BI dashboard in tools like Tableau, Power BI, or Looker to ensure high user adoption?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst"],
        "is_general": False,
        "skill_tags": ["Business Intelligence", "Tableau", "Power BI", "Data Visualization"],
        "expected_points": [
            "Starting with user requirements and identifying the single primary decision the dashboard informs",
            "Visual hierarchy: high-level KPI summary cards at top, trend breakdowns in middle, granular details at bottom",
            "Selecting appropriate chart types (e.g. line charts for time series, bar charts for categorical comparison)",
            "Avoiding visual clutter, chartjunk, and misuse of pie charts or saturated colors",
            "Optimizing dashboard query performance and load latency"
        ],
        "rubric": {
            "criteria": ["User-Centric Design", "Visual Hierarchy", "Performance & Governance"],
            "key_concepts": ["kpi", "visual hierarchy", "actionable", "tableau", "power bi", "chartjunk", "adoption"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Keep it actionable: 'So what?' for every visual. Use the 5-second rule—executives should grasp headline health instantly. Use consistent palettes, clear filters, and pre-aggregate queries in the warehouse for snappy rendering.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-cohort-analysis-retention-06",
        "question_text": "How do you construct and interpret a customer retention cohort analysis? What business insights does it reveal?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Cohort Analysis", "Retention", "Customer Analytics", "SQL"],
        "expected_points": [
            "Definition of cohorts grouped by acquisition month/week",
            "Tracking repeated activity or purchases across subsequent periods (Period 0, Period 1, Period 2...)",
            "Visualizing the retention heatmap or triangle matrix to spot retention decay curves",
            "Differentiating between cohort degradation (product issue) and seasonal changes",
            "SQL query design using min acquisition date joined back to subsequent transactions"
        ],
        "rubric": {
            "criteria": ["Cohort Methodology", "SQL Implementation Logic", "Business Insight"],
            "key_concepts": ["cohort", "retention", "acquisition", "decay curve", "churn", "period", "heatmap"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Group users by signup cohort date. Count distinct active users in subsequent periods to calculate retention percentages. Flat curves indicate strong product-market fit; steep drops suggest onboarding friction.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-data-warehousing-schemas-07",
        "question_text": "Explain the difference between a Star Schema and a Snowflake Schema in data warehousing. When would you prefer one over the other?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist", "Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["Data Warehousing", "Dimensional Modeling", "Data Architecture"],
        "expected_points": [
            "Star schema: central fact table surrounded by denormalized dimension tables",
            "Snowflake schema: dimension tables are normalized into sub-dimension tables",
            "Star schema advantages: simpler queries, fewer joins, faster analytical query execution in modern columnar stores",
            "Snowflake schema advantages: reduced data redundancy, easier dimension updates",
            "Modern trends favoring denormalized Star schemas in Snowflake/BigQuery/Redshift"
        ],
        "rubric": {
            "criteria": ["Architectural Accuracy", "Normalization Trade-offs", "Modern Warehouse Context"],
            "key_concepts": ["star schema", "snowflake schema", "fact table", "dimension", "denormalized", "joins", "warehouse"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Star schema centers around facts (e.g. sales) with direct links to denormalized dimensions (customer, product). Snowflake normalizes dimensions (product links to category). In modern analytics (BigQuery/Snowflake), Star is preferred for simplicity and fast scans.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-funnel-conversion-dropoff-08",
        "question_text": "How do you identify and diagnose where users are dropping off in a multi-step user registration or checkout funnel?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst"],
        "is_general": False,
        "skill_tags": ["Funnel Analysis", "Conversion Rate", "Product Analytics"],
        "expected_points": [
            "Mapping discrete sequential funnel stages with distinct tracking events",
            "Calculating step-by-step conversion and drop-off percentages",
            "Segmenting drop-off data by browser, device, traffic channel, or geography to isolate technical glitches",
            "Correlating drop-offs with form validation errors or page load latency",
            "Recommending UX fixes based on data findings"
        ],
        "rubric": {
            "criteria": ["Event Tracking Model", "Segmentation Diagnostics", "Actionable Recommendations"],
            "key_concepts": ["funnel", "conversion", "drop-off", "segmentation", "events", "checkout", "ux"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Step 1: define the event pipeline (Land -> AddToCart -> Checkout -> Pay). Step 2: calculate drop-off rate per step. Step 3: segment by device/browser to check for bugs. Step 4: inspect form error logs on the highest drop-off screen.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-handling-imbalanced-distributions-09",
        "question_text": "Why can calculating the arithmetic mean be misleading for skewed business data like salaries or customer spend? What alternatives do you use?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Statistics", "Descriptive Statistics", "Data Distribution"],
        "expected_points": [
            "Arithmetic mean is sensitive to extreme outliers and right/left-skewed distributions",
            "Median as a robust measure of central tendency that is resistant to outliers",
            "Percentiles (e.g., p25, p50, p75, p90, p99) for comprehensive distribution understanding",
            "Interquartile range (IQR) and geometric mean for multiplicative distributions",
            "Providing visual histograms alongside summary metrics"
        ],
        "rubric": {
            "criteria": ["Statistical Intuition", "Robust Metrics Selection", "Communication Clarity"],
            "key_concepts": ["mean", "median", "skewed", "outliers", "percentiles", "p95", "robust"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): In skewed distributions, a few high spenders pull the mean upward, misleading stakeholders into believing typical customers spend more than they do. Use median (p50) and percentile brackets (p10, p90) to tell the true story.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-sql-cte-vs-subquery-10",
        "question_text": "What is a Common Table Expression (CTE) in SQL, and when would you use it over nested subqueries or temporary tables?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist", "Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["SQL", "Query Optimization", "Database Architecture"],
        "expected_points": [
            "Definition of CTE using the WITH clause as a temporary, readable result set",
            "Dramatic readability and maintainability improvement over deeply nested subqueries",
            "Reusability: referencing the same CTE multiple times within a single query",
            "Support for recursive queries (e.g., organizational hierarchies or graphs)",
            "Performance considerations: optimizer materialization vs inlining depending on database engine"
        ],
        "rubric": {
            "criteria": ["CTE Syntax & Concept", "Subquery Comparison", "Practical Use Cases"],
            "key_concepts": ["with clause", "cte", "subquery", "readability", "recursive", "temp table", "maintainability"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): CTEs (`WITH x AS (...)`) break complex multi-step pipelines into modular, top-down reading blocks. Use CTEs for clean code and readability, subqueries for simple inline filters, and temp tables when caching heavy intermediate results used in separate queries.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-data-governance-pii-11",
        "question_text": "How do you ensure data privacy and PII protection when extracting and analyzing customer records for business reporting?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Data Governance", "PII", "Compliance", "Security"],
        "expected_points": [
            "Identifying Personally Identifiable Information (PII): names, emails, IPs, phone numbers, payment details",
            "Anonymization and pseudonymization techniques: hashing with salt, masking, tokenization",
            "Access control principles: least privilege, role-based access control (RBAC)",
            "Aggregating reporting at a cohort or group level to prevent re-identification",
            "Compliance with data regulations such as GDPR or CCPA"
        ],
        "rubric": {
            "criteria": ["PII Identification", "Anonymization Techniques", "Security Protocols"],
            "key_concepts": ["pii", "anonymization", "masking", "gdpr", "rbac", "privacy", "hashing"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Never pull raw PII into analytics notebooks. Use salted hashes for user tracking, mask sensitive strings, drop unused identifiers, and present only aggregated statistics in dashboards.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-interpreting-correlation-vs-causation-12",
        "question_text": "Explain the classic pitfall of confusing correlation with causation in business data. Provide a scenario and explain how you would prove causality.",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Causal Inference", "Statistics", "Critical Thinking"],
        "expected_points": [
            "Definition: two variables moving together does not imply one causes the other",
            "Role of confounding variables / third-variable problems",
            "Reverse causality possibility",
            "Gold standard for establishing causality: randomized controlled trials (A/B testing)",
            "Quasi-experimental methods if randomized experiments are impossible (e.g. difference-in-differences, instrumental variables)"
        ],
        "rubric": {
            "criteria": ["Conceptual Precision", "Confounder Identification", "Causal Proving Method"],
            "key_concepts": ["correlation", "causation", "confounder", "experiment", "a/b test", "bias", "spurious"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Scenario: Users who read 5 help articles have higher renewal rates. Is it the articles causing renewal, or are highly motivated users just reading more? To prove causality, run an A/B test nudging a random cohort toward articles.",
        "is_active": True,
    },
    {
        "identifier": "da-proj-stakeholder-presentation-13",
        "question_text": "Walk me through an analytical project where you had to explain complex data findings to non-technical business leaders. How did you structure your narrative?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Data Storytelling", "Stakeholder Communication", "Presentation"],
        "expected_points": [
            "Context and commercial objective of the analysis",
            "Leading with the bottom line (Minto Pyramid principle): recommendations first, followed by supporting evidence",
            "Translating statistical jargon into business dollars, percentages, or user retention metrics",
            "Interactive Q&A handling and transparent disclosure of data limitations",
            "Tangible business action taken as a result"
        ],
        "rubric": {
            "criteria": ["Executive Narrative", "Jargon Translation", "Impact & Action"],
            "key_concepts": ["storytelling", "stakeholder", "executive", "recommendation", "impact", "narrative", "decision"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Describe how you framed the talk around their goals, used simple visual metaphors rather than complex regression formulas, and provided 2-3 clear actionable choices with predicted business impact.",
        "is_active": True,
    },
    {
        "identifier": "da-proj-investigating-metric-drop-14",
        "question_text": "Suppose a company's weekly active users (WAU) dropped by 12% over the last week. Walk me through your step-by-step triage investigation.",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Root Cause Analysis", "Triage", "Product Analytics"],
        "expected_points": [
            "Data validation first: verifying if telemetry/tracking pipeline broke or ingestion was delayed",
            "Segmentation by platform, operating system, geography, user type (new vs returning), and app version",
            "Checking external factors: holidays, competitor moves, outages, search engine index updates",
            "Correlating with internal changes: recent deployments, feature rollouts, login issues",
            "Formulating a summary incident report with recommended remediation"
        ],
        "rubric": {
            "criteria": ["Data Integrity Check First", "Systematic Dimension Breakdown", "External vs Internal Causes"],
            "key_concepts": ["triage", "pipeline", "segmentation", "deployment", "external", "root cause", "telemetry"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Rule 1: check the instrument before assuming the plane is crashing (did the tracking table fail to load?). Rule 2: segment across dimensions (iOS vs Android, country). Rule 3: inspect releases and server logs during the drop window.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-excel-advanced-modeling-15",
        "question_text": "What advanced functions in Excel or Google Sheets (e.g. XLOOKUP, INDEX/MATCH, Dynamic Arrays, Pivot Tables) do you rely on for rapid prototyping?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Analyst"],
        "is_general": False,
        "skill_tags": ["Excel", "Google Sheets", "Financial Modeling"],
        "expected_points": [
            "Advantages of XLOOKUP or INDEX/MATCH over legacy VLOOKUP (left lookups, insertion resilience)",
            "Dynamic array formulas like FILTER, UNIQUE, and SORT",
            "Pivot tables with calculated fields for multi-dimensional slicing",
            "Data validation and error handling (IFERROR) to prevent model breakage"
        ],
        "rubric": {
            "criteria": ["Function Mastery", "Model Robustness", "Efficiency"],
            "key_concepts": ["xlookup", "index/match", "pivot table", "filter", "unique", "excel", "formula"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Explain that modern spreadsheets are powerful for quick sanity checks. XLOOKUP avoids column index breakage when columns are inserted, while FILTER and UNIQUE dynamically build ad-hoc summary slices.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-data-pipeline-sla-16",
        "question_text": "How do you detect when an automated daily ETL pipeline is delayed, and how do you prevent downstream business reports from displaying partial data?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Analyst", "Data Scientist", "Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["ETL", "Data Quality", "Airflow", "Data Reliability"],
        "expected_points": [
            "Data freshness checks and SLA alerts (e.g., in Airflow or dbt tests)",
            "Atomic data loads: loading into a staging table and swapping partition/view only after validation succeeds",
            "Data quality assertions (row count thresholds, null checks, uniqueness constraints)",
            "Dashboard banner warnings or pausing dashboard refresh when data is stale"
        ],
        "rubric": {
            "criteria": ["Atomic Loading", "Automated Assertions", "User Notification"],
            "key_concepts": ["etl", "pipeline", "sla", "staging", "dbt", "data quality", "freshness"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Use staging tables and atomic view swaps or partition replacement. Run automated dbt/Great Expectations tests verifying minimum row counts and zero null primary keys before flipping the production view.",
        "is_active": True,
    },
    {
        "identifier": "da-proj-defining-north-star-metric-17",
        "question_text": "How would you help a product team define their 'North Star Metric'? What criteria make a metric effective rather than vanity?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Data Analyst"],
        "is_general": False,
        "skill_tags": ["Product Strategy", "KPIs", "Metrics Framework"],
        "expected_points": [
            "Definition of North Star Metric as the single key metric capturing core customer value delivery",
            "Criteria: reflects customer value, correlates with long-term revenue, and is measurable/actionable",
            "Guarding against gaming or vanity metrics (e.g. pageviews vs engaged active minutes)",
            "Complementary counter-metrics to protect quality (e.g., speed paired with defect rate)"
        ],
        "rubric": {
            "criteria": ["Value Alignment", "Vanity vs Actionable", "Counter-Metrics"],
            "key_concepts": ["north star", "vanity metric", "customer value", "counter metric", "actionable", "retention"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): A good North Star (e.g. Spotify: time spent listening) captures user value delivery. Always pair it with guardrail counter-metrics (e.g., unsubscribe rate) to prevent teams from gaming the primary target.",
        "is_active": True,
    },
    {
        "identifier": "da-tech-sql-optimization-large-tables-18",
        "question_text": "What strategies do you use to optimize slow-running SQL queries on multi-million row analytical tables?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Analyst", "Data Scientist", "Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["SQL", "Query Optimization", "Performance Tuning"],
        "expected_points": [
            "Analyzing EXPLAIN / EXPLAIN ANALYZE execution plans to locate bottlenecks and sequential scans",
            "Pruning partitions and filtering early in WHERE clauses before performing heavy joins",
            "Indexing strategies: B-tree, composite indexes, and index selectivity",
            "Avoiding SELECT * and unindexed wildcard functions (e.g. WHERE LOWER(email) = ... without functional index)",
            "Pre-aggregating frequently accessed summary tables"
        ],
        "rubric": {
            "criteria": ["Execution Plan Literacy", "Partition Pruning", "Index Strategy"],
            "key_concepts": ["explain analyze", "indexes", "partition", "sequential scan", "filter early", "aggregation"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Start with EXPLAIN ANALYZE to identify full table scans and high-cost joins. Filter on partitioned date ranges early, index join keys, avoid functions on indexed columns in the WHERE clause, and only select required columns.",
        "is_active": True,
    },

    # =========================================================================
    # 3. DATA SCIENTIST (18 questions)
    # =========================================================================
    {
        "identifier": "ds-tech-bias-variance-tradeoff-01",
        "question_text": "Explain the bias-variance tradeoff in supervised machine learning. How do overfitting and underfitting manifest, and how do you diagnose them?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Machine Learning", "Model Evaluation", "Supervised Learning"],
        "expected_points": [
            "Bias as error from erroneous model assumptions (leading to underfitting)",
            "Variance as error from sensitivity to small fluctuations in training data (leading to overfitting)",
            "Diagnosing via learning curves comparing training error vs cross-validation/test error",
            "Techniques to reduce variance: regularization (L1/L2), pruning, more training data, bagging/ensembles",
            "Techniques to reduce bias: increasing model complexity, adding features, boosting"
        ],
        "rubric": {
            "criteria": ["Theoretical Accuracy", "Diagnostic Curves", "Remediation Techniques"],
            "key_concepts": ["bias", "variance", "overfitting", "underfitting", "regularization", "cross-validation", "tradeoff"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): High bias means both training and test error are high (underfitting). High variance means training error is low but test error is significantly higher (overfitting). Explain balancing complexity via regularization and cross-validation.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-precision-recall-f1-auc-02",
        "question_text": "In a highly imbalanced classification problem (e.g. 1% fraud detection), why is accuracy misleading? How do you choose between Precision, Recall, and ROC-AUC?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Data Scientist", "AI/ML Engineer", "Data Analyst"],
        "is_general": False,
        "skill_tags": ["Model Evaluation", "Classification", "Imbalanced Data"],
        "expected_points": [
            "Accuracy paradox: predicting the majority class yields 99% accuracy while detecting 0 fraud cases",
            "Precision = TP / (TP + FP): focus on minimizing false alarms",
            "Recall = TP / (TP + FN): focus on capturing all positive fraud cases",
            "Business trade-off context: cost of a missed fraudster vs cost of annoying a legitimate customer",
            "PR-AUC (Precision-Recall AUC) being superior to ROC-AUC when positive class is extremely rare"
        ],
        "rubric": {
            "criteria": ["Metric Definitions", "Business Cost Mapping", "PR-AUC vs ROC-AUC"],
            "key_concepts": ["precision", "recall", "f1-score", "imbalanced", "roc-auc", "pr-auc", "confusion matrix"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Outline the confusion matrix. For fraud, missing a fraudster (False Negative) has massive financial consequences, so optimize for high Recall, while monitoring Precision to keep customer friction acceptable. Recommend PR curves over ROC curves for extreme skew.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-linear-regression-assumptions-03",
        "question_text": "What are the core Gauss-Markov assumptions of Ordinary Least Squares (OLS) Linear Regression? How do you test for heteroscedasticity and multicollinearity?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist"],
        "is_general": False,
        "skill_tags": ["Statistics", "Linear Regression", "Econometrics"],
        "expected_points": [
            "Assumptions: Linearity, exogeneity (zero conditional mean of errors), homoscedasticity, no autocorrelation, no multicollinearity, normal residuals",
            "Heteroscedasticity: non-constant variance of errors, diagnosed via residual vs fitted plots or Breusch-Pagan test",
            "Multicollinearity: correlated independent variables inflating coefficient variance, tested using Variance Inflation Factor (VIF > 5 or 10)",
            "Remedies: robust standard errors, log transformations, ridge regression, or dropping redundant collinear features"
        ],
        "rubric": {
            "criteria": ["Assumptions Completeness", "Diagnostic Tests (VIF/Breusch-Pagan)", "Remediation Knowledge"],
            "key_concepts": ["ols", "homoscedasticity", "heteroscedasticity", "multicollinearity", "vif", "residuals", "gauss-markov"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): List the core assumptions. Heteroscedasticity leads to invalid p-values; fix it with robust standard errors or target transformation. Multicollinearity inflates standard errors; diagnose with VIF and resolve using PCA or L2 regularization.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-cross-validation-leakage-04",
        "question_text": "What is data leakage in machine learning, and how can it subtly occur during preprocessing and cross-validation pipelines?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Data Leakage", "Cross-Validation", "Scikit-Learn"],
        "expected_points": [
            "Definition of data leakage: test/future information contaminating the training set",
            "Subtle examples: fitting scalers, imputer, or target encoders on the entire dataset prior to train/test split",
            "Temporal leakage: random shuffling of time-series data instead of using time-based rolling splits",
            "Target leakage: features derived from post-target events (e.g. account closure date predicting churn)",
            "Prevention: strict use of Scikit-Learn Pipelines that fit only on train folds"
        ],
        "rubric": {
            "criteria": ["Leakage Types", "Preprocessing Sequence", "Pipeline Mitigation"],
            "key_concepts": ["data leakage", "target leakage", "pipeline", "cross-validation", "temporal split", "fit_transform"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Explain that fitting a standard scaler or imputer before splitting leaks distribution parameters (mean/variance) to the model. Use `sklearn.pipeline.Pipeline` so all transformations are fitted purely inside each CV fold.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-regularization-l1-l2-05",
        "question_text": "Compare L1 (Lasso) and L2 (Ridge) regularization mathematically and conceptually. Why does L1 regularization produce sparse models?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Machine Learning", "Regularization", "Feature Selection"],
        "expected_points": [
            "Penalty formulas: L1 adds absolute weight penalties (lambda * sum(|w|)); L2 adds squared weight penalties (lambda * sum(w^2))",
            "Geometric intuition: L1 constraint boundary is diamond-shaped with sharp corners on axes; L2 boundary is a smooth hypersphere/circle",
            "L1 yields exact zero coefficients (feature selection / sparsity)",
            "L2 shrinks correlated weights together towards zero but retains all features",
            "ElasticNet combining both penalties"
        ],
        "rubric": {
            "criteria": ["Mathematical Formulation", "Geometric Intuition", "Practical Selection"],
            "key_concepts": ["l1", "l2", "lasso", "ridge", "sparsity", "penalty", "weights", "shrinkage"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Explain the geometric contours: the loss ellipses intersect the L1 diamond constraint at the axes where coefficients are exactly zero, performing feature selection. L2 circular constraint intersects off-axis, shrinking weights smoothly.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-random-forest-vs-xgboost-06",
        "question_text": "Compare Random Forests and Gradient Boosted Trees (XGBoost/LightGBM). How do their aggregation mechanisms and training approaches differ?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Ensemble Methods", "Tree Models", "XGBoost", "Random Forest"],
        "expected_points": [
            "Random Forest uses Bagging (Bootstrap Aggregating) with deep, independent, unpruned trees trained in parallel",
            "Gradient Boosting uses Boosting: shallow trees trained sequentially, each fitting the pseudo-residuals of previous trees",
            "RF primarily reduces variance; Boosting reduces both bias and variance",
            "XGBoost incorporates 2nd-order Taylor expansions, tree pruning, and built-in L1/L2 regularization",
            "Hyperparameter sensitivity: XGBoost is more prone to overfitting if learning rate and depth are not tuned"
        ],
        "rubric": {
            "criteria": ["Bagging vs Boosting", "Parallel vs Sequential", "Residual Optimization"],
            "key_concepts": ["random forest", "xgboost", "bagging", "boosting", "residuals", "gradient", "ensemble"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): RF builds deep trees in parallel on bootstrapped samples and averages their votes to reduce variance. Gradient Boosting builds trees sequentially to minimize the gradient of the loss function, requiring careful tuning of learning rate.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-clustering-kmeans-dbscan-07",
        "question_text": "When segmenting customers, how do you decide between K-Means and DBSCAN? How do you determine the optimal number of clusters?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist"],
        "is_general": False,
        "skill_tags": ["Unsupervised Learning", "Clustering", "Customer Segmentation"],
        "expected_points": [
            "K-Means assumes spherical, equally sized clusters and requires pre-specifying k; sensitive to outliers",
            "DBSCAN finds arbitrarily shaped clusters based on density (eps and min_samples) and detects noise/outliers automatically",
            "Determining k in K-Means: Elbow method (inertia) and Silhouette analysis",
            "DBSCAN parameter tuning using k-distance graphs",
            "Feature scaling requirement: essential because distance metrics (Euclidean) are scale-dependent"
        ],
        "rubric": {
            "criteria": ["Algorithm Comparison", "Cluster Validation (Silhouette/Elbow)", "Sensitivity to Density/Outliers"],
            "key_concepts": ["k-means", "dbscan", "silhouette", "elbow method", "density", "clusters", "outliers"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Use K-Means when data has uniform density and you want balanced groups. Use DBSCAN if shapes are irregular or you want noise rejection. Scale features first, and validate K-Means using Silhouette coefficients.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-feature-importance-shap-08",
        "question_text": "What are the limitations of MDI (Mean Decrease in Impurity) feature importance in tree models, and how do SHAP values provide better interpretability?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Explainable AI", "SHAP", "Feature Importance"],
        "expected_points": [
            "MDI bias: favors continuous variables and high-cardinality categorical features; computed on train data",
            "Permutation importance as an alternative, but struggles with collinear features",
            "SHAP (Shapley Additive exPlanations) grounded in cooperative game theory",
            "Fair attribution of marginal contribution across all feature coalitions",
            "SHAP provides both global importance and local per-prediction explanations with directionality (+/-)"
        ],
        "rubric": {
            "criteria": ["MDI Flaws", "Shapley Value Foundation", "Local vs Global Interpretability"],
            "key_concepts": ["mdi", "impurity", "shap", "shapley values", "interpretability", "game theory", "local explanation"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): MDI artificially inflates high-cardinality features and ignores feature interactions. SHAP computes exact marginal contributions across all subsets of features, showing not just importance but whether a feature pushes predictions higher or lower.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-handling-imbalanced-resampling-09",
        "question_text": "Compare SMOTE (Synthetic Minority Over-sampling Technique) with class-weight adjustment for training classifiers on imbalanced datasets.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Imbalanced Data", "SMOTE", "Classification"],
        "expected_points": [
            "SMOTE generates synthetic examples along line segments connecting k-nearest neighbors in minority class",
            "Class-weight adjustment penalizes mistakes on minority class proportionally in the loss function without creating new data",
            "Risk of SMOTE in high-dimensional or noisy data: creating synthetic points in overlapping majority noise regions",
            "Class weighting is computationally cheaper, preserves genuine data distribution, and avoids memory explosion",
            "Threshold moving / tuning prediction threshold as a practical alternative"
        ],
        "rubric": {
            "criteria": ["SMOTE Mechanism", "Loss Modification Trade-off", "Threshold Tuning"],
            "key_concepts": ["smote", "class weight", "imbalanced", "synthetic", "cost-sensitive", "knn", "threshold"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Prefer cost-sensitive learning (class_weight='balanced') first: it alters loss penalties without hallucinating synthetic points in noisy feature spaces. Often, tuning the decision threshold on predicted probabilities achieves better real-world calibration.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-time-series-stationarity-10",
        "question_text": "What does it mean for a time series to be stationary? Why is stationarity required for ARIMA, and how do you achieve it?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Scientist"],
        "is_general": False,
        "skill_tags": ["Time Series", "ARIMA", "Forecasting", "Statistics"],
        "expected_points": [
            "Stationarity definition: constant mean, constant variance, and autocovariance depending only on lag (no seasonality/trend)",
            "Why required: statistical properties must remain constant over time for future forecast validity",
            "Statistical test: Augmented Dickey-Fuller (ADF) test (H0: unit root present)",
            "Transformations to achieve stationarity: differencing (d), seasonal differencing (D), and log/power transforms for variance stability",
            "ARIMA components: Autoregressive (p), Integrated differencing (d), Moving Average (q)"
        ],
        "rubric": {
            "criteria": ["Stationarity Conditions", "ADF Hypothesis Test", "Differencing Operations"],
            "key_concepts": ["stationarity", "arima", "differencing", "adf test", "autocorrelation", "variance", "trend"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): A stationary series has stable statistical parameters over time. If non-stationary, run the ADF test; apply log transform to stabilize expanding variance, and first-order or seasonal differencing to eliminate trends.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-pca-dimensionality-reduction-11",
        "question_text": "How does Principal Component Analysis (PCA) work under the hood? What are the key considerations when applying it to real-world data?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Dimensionality Reduction", "Linear Algebra", "PCA"],
        "expected_points": [
            "Eigen-decomposition of the covariance matrix or Singular Value Decomposition (SVD)",
            "Principal components represent orthogonal axes maximizing data variance",
            "Critical prerequisite: standardizing features (zero mean, unit variance) because PCA is scale-sensitive",
            "Deciding number of components via explained variance ratio scree plot (e.g. 90-95% variance explained)",
            "Trade-off: significant dimensionality and multicollinearity reduction vs loss of feature interpretability"
        ],
        "rubric": {
            "criteria": ["Linear Algebra Concept", "Standardization Requirement", "Interpretability Trade-off"],
            "key_concepts": ["pca", "covariance", "eigenvalues", "svd", "orthogonal", "variance explained", "standardize"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): PCA finds orthogonal directions of maximum variance via covariance matrix decomposition. You must standardize inputs first, otherwise high-magnitude features dominate the principal components. Note that new components are linear combinations, losing natural business names.",
        "is_active": True,
    },
    {
        "identifier": "ds-proj-churn-prediction-system-12",
        "question_text": "Describe how you would design an end-to-end customer churn prediction model, from problem formulation and feature engineering to deployment and business intervention.",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["End-to-End ML", "Feature Engineering", "System Design"],
        "expected_points": [
            "Defining churn window clearly (e.g. 30 days of inactivity) without temporal leakage",
            "Feature engineering: RFM (recency, frequency, monetary), customer support tickets, feature usage velocity",
            "Model training with proper temporal cross-validation",
            "Probability calibration (Brier score, isotonic/Platt scaling) for actionable risk tiers",
            "Integration with CRM/retention marketing triggers with cost-benefit intervention matrix"
        ],
        "rubric": {
            "criteria": ["Rigorous Problem Definition", "Feature Ingenuity", "Business Actionability"],
            "key_concepts": ["churn", "rfm", "temporal split", "calibration", "intervention", "lifecycle", "features"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Formulate churn as predicting whether an active user will churn within the next 30 days. Extract rolling behavioral features (e.g. change in weekly logins over 14 vs 60 days). Calibrate output probabilities so customer success can target high-value/high-risk users efficiently.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-model-drift-monitoring-13",
        "question_text": "What is the difference between data drift (covariate shift) and concept drift in production ML? How do you detect and monitor them?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["MLOps", "Model Monitoring", "Data Drift"],
        "expected_points": [
            "Data drift: P(X) changes while P(Y|X) remains constant (input distributions shift)",
            "Concept drift: P(Y|X) changes (the relationship between inputs and target alters, e.g. consumer habits post-COVID)",
            "Detection statistical tests: Kolmogorov-Smirnov (KS) test for numericals, Chi-squared or PSI (Population Stability Index) for categoricals",
            "Monitoring ground truth lag: handling situations where true labels arrive days or months late",
            "Automated retraining triggers and model rollback strategies"
        ],
        "rubric": {
            "criteria": ["Drift Definitions", "Statistical Drift Metrics (PSI/KS)", "Operational Mitigation"],
            "key_concepts": ["data drift", "concept drift", "covariate shift", "psi", "ks test", "monitoring", "retraining"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Data drift is input distribution shift P(X); concept drift is target relationship shift P(Y|X). Measure PSI on incoming production features daily. When PSI > 0.25, alert the team to evaluate drift and trigger validation on updated ground truth.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-bayesian-vs-frequentist-14",
        "question_text": "Explain the philosophical and practical differences between Bayesian and Frequentist statistics. When would you prefer a Bayesian approach?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist"],
        "is_general": False,
        "skill_tags": ["Statistics", "Bayesian Methods", "Probability"],
        "expected_points": [
            "Frequentist treats parameters as fixed unknown constants, probability as long-run frequency of repeatable events",
            "Bayesian treats parameters as random variables with probability distributions, updating prior beliefs with likelihood via Bayes' Theorem",
            "Interpretability of credible intervals (direct probability that parameter is within range) vs confidence intervals",
            "When Bayesian is preferred: small sample sizes where informative domain priors exist, hierarchical modeling, multi-armed bandits"
        ],
        "rubric": {
            "criteria": ["Philosophical Distinction", "Interval Interpretation", "Appropriate Use Cases"],
            "key_concepts": ["bayesian", "frequentist", "prior", "posterior", "likelihood", "credible interval", "bayes theorem"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Frequentists define probability as long-run frequencies of infinite trials; Bayesians quantify degrees of belief. Bayesian shines when you have valuable prior domain knowledge (e.g. historical conversion rates) or need continuous updating as in multi-armed bandits.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-nlp-tokenization-embeddings-15",
        "question_text": "How do text representations evolve from Bag-of-Words and TF-IDF to dense word embeddings (Word2Vec) and contextual transformers (BERT)?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["NLP", "Embeddings", "Transformers"],
        "expected_points": [
            "Bag-of-Words & TF-IDF: sparse, high-dimensional, ignore word order and semantic synonymy",
            "Word2Vec / GloVe: dense fixed-dimensional vectors capturing semantic similarity (cosine), but single static vector per word regardless of context",
            "Contextual Embeddings (BERT): self-attention captures polysemy (e.g. 'bank' of a river vs financial 'bank')",
            "Subword tokenization (BPE/WordPiece) handling out-of-vocabulary words"
        ],
        "rubric": {
            "criteria": ["Sparse to Dense Evolution", "Contextuality & Polysemy", "Attention Advantage"],
            "key_concepts": ["tf-idf", "word2vec", "embeddings", "bert", "attention", "polysemy", "contextual"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Walk through sparsity to density: TF-IDF is sparse and order-blind. Word2Vec maps semantics into vector geometry ('king' - 'man' + 'woman' = 'queen') but gives 'apple' one vector. BERT uses bi-directional self-attention to generate dynamic context-aware vectors.",
        "is_active": True,
    },
    {
        "identifier": "ds-proj-recommender-collaborative-filtering-16",
        "question_text": "How would you design a hybrid movie or product recommendation engine? Compare collaborative filtering with content-based approaches and explain cold-start handling.",
        "category": "Project-Based",
        "difficulty": "Advanced",
        "role_tags": ["Data Scientist", "AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Recommender Systems", "Matrix Factorization", "Collaborative Filtering"],
        "expected_points": [
            "Collaborative filtering (user-user, item-item, matrix factorization via SVD): relies on behavioral co-interactions without needing domain metadata",
            "Content-based filtering: relies on item attributes/tags/embeddings matched against user preference vectors",
            "Cold start problem: new users or items with zero historical interaction logs",
            "Hybrid solutions: using content metadata or onboarding questionnaires for new items/users, transitioning to collaborative filtering as interactions accumulate"
        ],
        "rubric": {
            "criteria": ["CF vs Content-Based", "Matrix Factorization", "Cold-Start Strategies"],
            "key_concepts": ["collaborative filtering", "content-based", "matrix factorization", "cold start", "svd", "embeddings"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Collaborative filtering captures unexpected cross-domain affinity through user interaction matrices. For new items/users (cold start), fall back to content-based attribute matching and popular trending baselines until enough clicks are logged.",
        "is_active": True,
    },
    {
        "identifier": "ds-tech-logistic-regression-odds-ratio-17",
        "question_text": "Explain the sigmoid function and the concept of log-odds in Logistic Regression. How do you interpret a model coefficient of 0.40?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist", "Data Analyst"],
        "is_general": False,
        "skill_tags": ["Statistics", "Logistic Regression", "Mathematics"],
        "expected_points": [
            "Sigmoid function maps real numbers to (0, 1) probability range: 1 / (1 + e^(-z))",
            "Log-odds (logit) formulation: ln(p / (1 - p)) = beta0 + beta1*x",
            "Interpretation of beta: one-unit increase in x multiplies the odds of the positive outcome by exp(beta)",
            "For beta = 0.40: exp(0.40) ≈ 1.49, meaning approximately a 49% increase in the odds of the outcome, holding all other variables constant"
        ],
        "rubric": {
            "criteria": ["Sigmoid Formulation", "Log-Odds vs Odds", "Correct Coefficient Calculation"],
            "key_concepts": ["sigmoid", "logit", "log-odds", "odds ratio", "exponential", "logistic regression"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Logistic regression models log-odds linearly. Because log-odds are non-intuitive, exponentiate the coefficient: e^(0.40) ≈ 1.49. Thus, a 1-unit increase in X multiplies the odds by 1.49 (a 49% increase in odds, not absolute probability).",
        "is_active": True,
    },
    {
        "identifier": "ds-proj-evaluating-model-business-roi-18",
        "question_text": "How do you translate a 2% improvement in model F1-score or AUC into tangible business value and financial ROI for executives?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Data Scientist"],
        "is_general": False,
        "skill_tags": ["Business Translation", "ROI", "Executive Communication"],
        "expected_points": [
            "Mapping true positives, false positives, true negatives, and false negatives to direct financial costs and revenues",
            "Calculating net profit delta: (additional detected fraud saved - cost of customer friction calls)",
            "Presenting expected value framework rather than abstract statistical percentages",
            "Considering latency, engineering maintenance, and compute costs against model gain"
        ],
        "rubric": {
            "criteria": ["Financial Mapping", "Cost-Benefit Matrix", "Executive Perspective"],
            "key_concepts": ["roi", "business value", "financial", "cost matrix", "expected value", "net profit"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Translate confusion matrix counts into dollars: (New True Positives * Revenue Saved) - (New False Positives * Review Cost). If a 2% gain in F1 catches 500 more fraudulent transactions worth $200 each, it delivers $100,000 in monthly value.",
        "is_active": True,
    },

    # =========================================================================
    # 4. AI/ML ENGINEER (18 questions)
    # =========================================================================
    {
        "identifier": "ml-tech-transformer-self-attention-01",
        "question_text": "Explain the Multi-Head Self-Attention mechanism in the Transformer architecture. What roles do the Query, Key, and Value matrices play?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Deep Learning", "Transformers", "PyTorch"],
        "expected_points": [
            "Formula: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V",
            "Q (Query) represents what the current token is looking for; K (Key) represents what each token offers; V (Value) holds the actual representation content",
            "Scaling by sqrt(d_k) prevents dot products from growing excessively large, avoiding vanishing gradients in softmax",
            "Multi-head projection allows the model to jointly attend to information from different representation subspaces and positions simultaneously"
        ],
        "rubric": {
            "criteria": ["Attention Formula", "Q, K, V Roles", "Scaling Factor & Multi-Head Purpose"],
            "key_concepts": ["query", "key", "value", "softmax", "dot-product", "scale", "multi-head", "transformer"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): State the formula. Q and K dot-product measures token similarity; softmax yields normalized attention weights; multiplying by V outputs the weighted sum of representations. Multi-head attention projects into multiple subspaces, allowing simultaneous tracking of syntax, semantics, and coreferences.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-rag-pipeline-chunking-eval-02",
        "question_text": "How do you design a robust Retrieval-Augmented Generation (RAG) pipeline? What strategies do you use for chunking, hybrid search, and evaluation?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["RAG", "LLMs", "Vector Databases", "Embeddings"],
        "expected_points": [
            "Document chunking strategies: recursive character splitting with overlap, semantic boundaries, preserving headers",
            "Hybrid search: combining dense vector semantic search (HNSW) with sparse lexical search (BM25) via Reciprocal Rank Fusion (RRF)",
            "Re-ranking with cross-encoders to prioritize top context passages before feeding to LLM context window",
            "RAG evaluation framework (RAGAS / TruLens): Faithfulness, Answer Relevance, Context Precision, and Context Recall",
            "Guarding against hallucination via strict system prompting and source citation enforcement"
        ],
        "rubric": {
            "criteria": ["Chunking Nuance", "Hybrid Search (Dense + Sparse)", "RAG Evaluation Metrics"],
            "key_concepts": ["rag", "chunking", "hybrid search", "bm25", "re-ranking", "faithfulness", "context", "hallucination"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Chunk documents semantically with 10-15% overlap. Index both into a vector DB and BM25 index, merge results with RRF, and pass the top 20 candidates through a cross-encoder re-ranker to pick top 5. Evaluate with RAGAS metrics: Faithfulness (is the answer grounded in context?) and Context Relevance.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-model-quantization-techniques-03",
        "question_text": "Explain model quantization (e.g. FP16, INT8, INT4, AWQ, GGUF). What are Post-Training Quantization (PTQ) and Quantization-Aware Training (QAT)?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Model Optimization", "Quantization", "Model Deployment", "Inference"],
        "expected_points": [
            "Quantization maps high-precision floating point weights (FP32/FP16) to lower-bit integers (INT8/INT4), slashing memory bandwidth and VRAM requirements",
            "Post-Training Quantization (PTQ): quantizing pre-trained weights directly using a calibration dataset without retraining",
            "Quantization-Aware Training (QAT): modeling quantization error during training using fake-quantization nodes so weights adapt, preserving higher accuracy",
            "Weight-only vs weight-and-activation quantization tradeoffs",
            "Modern LLM formats: AWQ (Activation-aware Weight Quantization) and GGUF for efficient edge/CPU/GPU serving"
        ],
        "rubric": {
            "criteria": ["Precision Bitwidth Tradeoffs", "PTQ vs QAT", "Hardware / Inference Benefits"],
            "key_concepts": ["quantization", "fp16", "int8", "ptq", "qat", "awq", "gguf", "vram", "inference"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Quantization reduces memory footprint and increases inference throughput by lowering precision from 16-bit to 8-bit or 4-bit. PTQ is fast and requires only a small calibration set; QAT fine-tunes with simulated quantization noise, yielding better accuracy at low bitwidths.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-vanishing-exploding-gradients-04",
        "question_text": "What causes vanishing and exploding gradients in deep neural networks? How do modern architectures mitigate them?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["AI/ML Engineer", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Deep Learning", "Optimization", "Backpropagation"],
        "expected_points": [
            "Chain rule multiplication of gradients through many layers causing values to exponentially decay to zero or blow up to infinity/NaN",
            "Role of saturating activation functions (Sigmoid, Tanh) whose derivatives are < 0.25",
            "Architectural fixes: Residual connections (ResNet skip connections) providing clean gradient highways",
            "Activation fixes: ReLU, LeakyReLU, GeLU avoiding saturation in positive domain",
            "Normalization: Batch Normalization, Layer Normalization, and proper weight initialization (He/Xavier)",
            "Gradient clipping for exploding gradients"
        ],
        "rubric": {
            "criteria": ["Mathematical Root Cause", "Residual Connection Purpose", "Normalization & Activation Remedies"],
            "key_concepts": ["vanishing gradient", "exploding gradient", "backpropagation", "residual", "normalization", "relu", "clipping"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): In deep networks, repeated multiplication of small weights and sigmoid derivatives shrinks gradients exponentially towards zero. Fix with non-saturating activations (ReLU), residual skip connections (d(x + F(x))/dx = 1 + F'(x)), layer normalization, and gradient clipping.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-peft-lora-fine-tuning-05",
        "question_text": "How does LoRA (Low-Rank Adaptation) work for parameter-efficient fine-tuning (PEFT) of large language models? Why is it computationally superior to full fine-tuning?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["LLMs", "Fine-Tuning", "LoRA", "PEFT"],
        "expected_points": [
            "Freezing base pre-trained weights W_0 and injecting trainable rank decomposition matrices: delta_W = B * A",
            "Dimensions: if W is d x k, A is r x k and B is d x r, where rank r << min(d, k)",
            "Slashing trainable parameters by 99%+, dramatically reducing optimizer state memory (Adam states) in VRAM",
            "Zero inference latency overhead: adapter weights can be merged back into base weights W = W_0 + B*A at deployment",
            "Ability to swap small task-specific adapters dynamically on a single shared base model instance"
        ],
        "rubric": {
            "criteria": ["Low-Rank Decomposition Math", "VRAM Savings Mechanism", "Deployment Weight Merging"],
            "key_concepts": ["lora", "peft", "low-rank", "rank", "freeze", "adapter", "vram", "merge"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Base weights W are frozen. Adaptations are factored into two small low-rank matrices B and A (e.g. rank 8). Instead of updating billions of parameters, you train millions, drastically cutting GPU memory requirements for Adam optimizer states, and merge them back at zero latency cost.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-serving-latency-throughput-06",
        "question_text": "What techniques optimize high-throughput, low-latency LLM serving in production (e.g. vLLM, continuous batching, PagedAttention, KV-caching)?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["LLM Serving", "vLLM", "Inference Optimization", "Systems"],
        "expected_points": [
            "KV Cache: storing previous key-value tensors in attention so past tokens do not need recomputation during autoregressive generation",
            "PagedAttention: partitioning KV cache into non-contiguous virtual memory blocks, eliminating memory fragmentation and enabling memory sharing",
            "Continuous / Iteration-level batching: scheduling incoming requests dynamically at each token step rather than waiting for entire batches to finish",
            "Speculative decoding: small draft model generates candidate tokens verified in parallel by the target LLM",
            "Trade-offs: TTFT (Time to First Token) vs TPOT (Time Per Output Token)"
        ],
        "rubric": {
            "criteria": ["KV Cache Role", "PagedAttention Innovation", "Continuous Batching Advantage"],
            "key_concepts": ["kv cache", "pagedattention", "vllm", "continuous batching", "speculative decoding", "ttft", "tpot"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Autoregressive generation is memory-bandwidth bound. KV caching avoids recomputing past tokens. PagedAttention solves the 60-80% VRAM waste from internal fragmentation by allocating pages dynamically. Continuous batching evicts finished requests immediately, maximizing GPU utilization.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-distributed-training-data-model-parallel-07",
        "question_text": "Explain the differences between Data Parallelism (DDP), Pipeline Parallelism, and Tensor Parallelism (Megatron-LM) when training massive models across multi-GPU clusters.",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Distributed Training", "PyTorch DDP", "DeepSpeed", "HPC"],
        "expected_points": [
            "DDP (Distributed Data Parallel): model is replicated on every GPU; each gets a different data batch, gradients averaged via AllReduce",
            "Tensor Parallelism: splits individual linear layers/weight matrices across GPUs (intra-node fast NVLink)",
            "Pipeline Parallelism: partitions layers sequentially across GPUs (inter-node), managing pipeline bubbles via micro-batches",
            "ZeRO / FSDP (Fully Sharded Data Parallel): shards optimizer states, gradients, and model parameters across GPUs to fit models larger than single GPU memory"
        ],
        "rubric": {
            "criteria": ["DDP vs TP vs PP", "Communication Bottlenecks (NVLink vs Network)", "ZeRO/FSDP Sharding"],
            "key_concepts": ["ddp", "tensor parallelism", "pipeline parallelism", "fsdp", "zero", "allreduce", "nvlink"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): DDP replicates the whole model and splits data. When a model doesn't fit on one GPU, Tensor Parallelism shards matrices across GPUs (requires fast NVLink). Pipeline Parallelism stacks layers across GPUs. FSDP dynamically shards weights and optimizer states, gathering them on-the-fly during forward passes.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-vector-db-indexing-hnsw-ivf-08",
        "question_text": "How do Approximate Nearest Neighbor (ANN) vector search algorithms like HNSW and IVF-PQ balance search latency, memory usage, and recall?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Vector Databases", "ANN", "HNSW", "Embeddings"],
        "expected_points": [
            "Exact k-NN search O(N * D) is computationally intractable for millions of high-dimensional vectors",
            "HNSW (Hierarchical Navigable Small World): multi-layer proximity graph with logarithmic search scaling; high recall and low latency at the cost of high RAM usage",
            "IVF (Inverted File): partitions vector space into Voronoi cells using k-means, searching only nearby centroids",
            "Product Quantization (PQ): compresses vectors into compact codes to slash RAM by 90% with minor recall loss",
            "Hyperparameter tuning: efSearch, M (neighbors per node), and nprobe"
        ],
        "rubric": {
            "criteria": ["HNSW Graph Concept", "IVF-PQ Compression", "Trade-off Triangle (Speed/RAM/Recall)"],
            "key_concepts": ["hnsw", "ivf", "product quantization", "ann", "vector search", "recall", "latency"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Exact search scans all vectors. HNSW builds a skip-list-like hierarchy of graphs, navigating from sparse top layers to dense bottom layers quickly. IVF clusters vectors and inspects only candidate clusters. Pair IVF with PQ compression to fit huge indices into RAM.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-evaluating-generative-llms-09",
        "question_text": "How do you evaluate generative AI outputs when there is no single ground truth? Compare automated LLM-as-a-judge, BLEU/ROUGE, and human evaluations.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["LLM Evaluation", "NLP", "Quality Assurance"],
        "expected_points": [
            "Limitations of n-gram overlap metrics (BLEU/ROUGE): penalize valid paraphrasing and fail to measure factual correctness",
            "LLM-as-a-judge: using powerful models (e.g. GPT-4/Claude) with structured rubrics; challenges: position bias, self-preference, and verbosity bias",
            "Mitigating LLM-judge bias: swapping answer order, blind pairwise comparisons, and calibration against human golden sets",
            "Task-specific deterministic unit tests: JSON schema validity, regex constraint checks, Python execution of generated code",
            "Human evaluation: expert review with strict rubrics and inter-annotator agreement (Cohen's Kappa)"
        ],
        "rubric": {
            "criteria": ["N-gram Metric Flaws", "LLM-as-a-Judge Biases", "Hybrid Evaluation Framework"],
            "key_concepts": ["llm-as-a-judge", "bleu", "rouge", "position bias", "human evaluation", "ragas", "ground truth"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): BLEU/ROUGE are poor for generative text because they reward exact words, not meaning. Use a layered approach: deterministic checks for format, LLM-as-a-judge with order swapping to counter position bias, and regular human spot-audits on high-impact samples.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-feature-stores-feast-10",
        "question_text": "What is an ML Feature Store (e.g. Feast, Hopsworks)? Why does it separate offline training stores from online inference stores?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Feature Store", "MLOps", "Data Architecture"],
        "expected_points": [
            "Eliminating train-serve skew by standardizing feature transformation logic across environments",
            "Offline store (BigQuery, Snowflake, S3): optimized for high-throughput batch queries with point-in-time time-travel joins to prevent data leakage",
            "Online store (Redis, DynamoDB): low-latency key-value lookup (sub-10ms) for real-time model scoring",
            "Feature reusability across multiple models and teams with metadata cataloging and lineage"
        ],
        "rubric": {
            "criteria": ["Train-Serve Skew Elimination", "Online vs Offline Purpose", "Point-in-Time Correctness"],
            "key_concepts": ["feature store", "train-serve skew", "online store", "offline store", "point-in-time", "redis", "feast"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): A feature store guarantees that the exact same feature logic is used during training and real-time serving. Offline store (warehouse) performs historical point-in-time joins without future leakage; online store (Redis) provides single-digit millisecond lookups during live inference.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-onnx-tensorrt-compilation-11",
        "question_text": "How do model compilation and inference engines like ONNX Runtime and NVIDIA TensorRT accelerate deep learning inference on edge devices or GPUs?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Inference Engines", "TensorRT", "ONNX", "Edge AI"],
        "expected_points": [
            "ONNX (Open Neural Network Exchange): framework-agnostic computation graph standard",
            "Layer and tensor fusion: combining consecutive operations (e.g. Conv + BatchNorm + ReLU into a single GPU kernel to avoid VRAM roundtrips)",
            "Kernel auto-tuning: selecting the optimal CUDA execution parameters specifically for the target GPU hardware architecture",
            "Dynamic tensor memory management: reusing intermediate buffer allocations across graph nodes",
            "Precision calibration: automatic mixed-precision (FP16/INT8) kernel selection"
        ],
        "rubric": {
            "criteria": ["Graph Optimization & Operator Fusion", "Kernel Auto-Tuning", "Memory Re-use"],
            "key_concepts": ["onnx", "tensorrt", "operator fusion", "kernel", "cuda", "vram", "acceleration"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): PyTorch runs individual operations step-by-step, incurring GPU kernel launch overhead and intermediate VRAM read/writes. Compilers like TensorRT fuse operations (e.g. GEMM + Bias + Activation) into a single optimized kernel tailored to that GPU's Tensor Cores.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-prompt-injection-guardrails-12",
        "question_text": "How do you protect production LLM applications from prompt injection, jailbreaking, and data leakage?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["AI Safety", "Security", "LLMs", "Guardrails"],
        "expected_points": [
            "Separation of instructions from untrusted user content (e.g. XML delimiters, system prompt isolation)",
            "Input guardrails: classification models or regex filters scanning for injection attempts and toxic content",
            "Output guardrails: verifying schema compliance and screening for leaked system prompts or PII before sending responses",
            "Least privilege execution: ensuring tool-calling / function-calling agents cannot execute arbitrary destructive operations without human-in-the-loop confirmation"
        ],
        "rubric": {
            "criteria": ["Input/Output Separation", "Guardrail Architecture (NeMo/LlamaGuard)", "Principle of Least Privilege"],
            "key_concepts": ["prompt injection", "jailbreak", "guardrails", "system prompt", "least privilege", "sanitization"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Treat user inputs as untrusted. Wrap inputs in strict XML/markdown delimiters, use a lightweight classifier (like Llama Guard) to filter inputs and outputs, and restrict tool capabilities with strict schemas and authorization scopes.",
        "is_active": True,
    },
    {
        "identifier": "ml-proj-computer-vision-detection-pipeline-13",
        "question_text": "Walk through designing an end-to-end real-time object detection pipeline (e.g. YOLO) running on video streams. How do you handle frame drops and varying latency?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Computer Vision", "YOLO", "Video Processing", "Real-Time Systems"],
        "expected_points": [
            "Video ingestion: asynchronous frame capture using multi-threaded queues (decoupling decoding from inference)",
            "Pre-processing: aspect-ratio resizing, normalization, and batching on GPU",
            "Model architecture: single-stage detectors (YOLOv8/v11) with TensorRT export",
            "Post-processing: Non-Maximum Suppression (NMS) and ByteTrack/DeepSORT for multi-object tracking across frames",
            "Handling load spikes: frame-skipping policies (processing every nth frame while tracker interpolates)"
        ],
        "rubric": {
            "criteria": ["Asynchronous Ingestion", "NMS & Tracking Integration", "Frame-Skipping Strategy"],
            "key_concepts": ["yolo", "nms", "tracking", "bytetrack", "async", "frame rate", "latency", "pipeline"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Decouple video decoding from inference using lock-free queues. Run a lightweight tracker (ByteTrack) on high-frequency frames and run the heavy YOLO detector every 3-5 frames to detect new objects, adjusting sampling rate dynamically based on buffer depth.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-loss-functions-classification-14",
        "question_text": "Compare Cross-Entropy Loss, Focal Loss, and Contrastive Loss. When would you replace standard cross-entropy with Focal Loss?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer", "Data Scientist"],
        "is_general": False,
        "skill_tags": ["Loss Functions", "Deep Learning", "Optimization"],
        "expected_points": [
            "Cross-Entropy Loss: standard log-loss measuring divergence between true and predicted probability distributions",
            "Focal Loss: adds a modulating factor (1 - p_t)^gamma to cross-entropy to down-weight easy examples and focus learning on hard, misclassified samples",
            "When to use Focal Loss: extreme class imbalance (e.g. dense object detection like RetinaNet where background examples overwhelm foreground)",
            "Contrastive Loss / InfoNCE: pulls representations of similar pairs closer and pushes dissimilar pairs apart in embedding space (representation learning / CLIP)"
        ],
        "rubric": {
            "criteria": ["Focal Loss Modulating Factor", "Imbalance Application", "Contrastive Representation"],
            "key_concepts": ["cross-entropy", "focal loss", "contrastive loss", "hard negative", "imbalance", "modulating factor"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Standard cross-entropy lets thousands of easy background examples dominate gradient updates. Focal loss applies a modulating factor (1 - p_t)^gamma: if a sample is easy (p_t=0.99), its loss is discounted toward zero, focusing backprop entirely on hard cases.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-synthetic-data-generation-15",
        "question_text": "How do you evaluate and safely use synthetic training data generated by LLMs or diffusion models without causing model collapse?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Synthetic Data", "Data Quality", "Generative AI"],
        "expected_points": [
            "Model collapse phenomenon: training iteratively on synthetic data causes the tail ends of the distribution to disappear, reducing diversity",
            "Filtering and quality gating: using reward models, heuristic sanity checks, and semantic deduplication to discard low-quality synthetic rows",
            "Mixing ratios: maintaining a high proportion of validated human data anchors alongside synthetic augmentations",
            "Diversity metrics: embedding entropy, cluster dispersion, and n-gram perplexity checks"
        ],
        "rubric": {
            "criteria": ["Model Collapse Mechanism", "Filtering & Guardrails", "Human-to-Synthetic Mix Ratio"],
            "key_concepts": ["synthetic data", "model collapse", "diversity", "quality filter", "reward model", "distribution tail"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Model collapse happens when models overfit to high-probability synthetic modes, erasing long-tail nuance. Always anchor datasets with real-world data, aggressively deduplicate embeddings, and use reward models to filter out ungrounded synthetic samples.",
        "is_active": True,
    },
    {
        "identifier": "ml-proj-mlops-ci-cd-pipeline-16",
        "question_text": "What components make up an automated MLOps CI/CD/CT (Continuous Training) pipeline from GitHub pull request to production rollout?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["MLOps", "CI/CD", "Continuous Training", "Docker"],
        "expected_points": [
            "CI: Linting, type checking, unit tests for data transformation logic, and fast integration tests on miniature datasets",
            "CT (Continuous Training): Triggered by new data or performance degradation; pipeline execution in orchestrators like Kubeflow/Airflow",
            "CD (Continuous Delivery): Automated evaluation gating against champion model on golden holdout set before canary/shadow deployment",
            "Artifact registry: versioning code (Git), data (DVC), model weights (MLflow Model Registry), and container images (Docker)",
            "Shadow deployment: routing live production traffic to candidate model without serving its response to users to observe latency and outputs safely"
        ],
        "rubric": {
            "criteria": ["CI vs CT vs CD Breakdown", "Artifact Versioning (Code/Data/Model)", "Shadow / Canary Rollout"],
            "key_concepts": ["mlops", "ci/cd", "continuous training", "mlflow", "dvc", "champion/challenger", "shadow deployment"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Connect code, data, and models. PR tests verify code integrity; training pipelines log metrics to MLflow. If candidate beats champion on holdout benchmarks, deploy to shadow mode to verify real-world throughput and latency before cutting over.",
        "is_active": True,
    },
    {
        "identifier": "ml-tech-flash-attention-optimizations-17",
        "question_text": "What is FlashAttention, and how does it make transformer attention computation significantly faster and more memory efficient?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Deep Learning Systems", "FlashAttention", "GPU Architecture", "CUDA"],
        "expected_points": [
            "Bottleneck in standard attention: writing and reading large N x N attention matrices to and from high-bandwidth GPU memory (HBM)",
            "FlashAttention is IO-aware: tiling inputs into blocks loaded into ultra-fast SRAM on the GPU chip",
            "Online softmax trick: updating softmax running normalizers incrementally without materializing the full N x N matrix",
            "Recomputing attention blocks during backward pass instead of storing all intermediate activations in HBM",
            "Results in linear memory scaling with sequence length and 2-4x speedups"
        ],
        "rubric": {
            "criteria": ["HBM vs SRAM Bottleneck", "Tiling Mechanism", "Online Softmax Math"],
            "key_concepts": ["flashattention", "sram", "hbm", "tiling", "online softmax", "io-aware", "memory bandwidth"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Standard attention is bounded by memory read/writes to GPU HBM, not FLOPs. FlashAttention splits Q, K, V into tiles that fit in fast on-chip SRAM, uses the online softmax formula to compute attention without writing the N x N matrix to HBM, and recomputes on backward pass.",
        "is_active": True,
    },
    {
        "identifier": "ml-proj-speech-audio-pipeline-18",
        "question_text": "How do you build a real-time Speech-to-Text (STT) and Voice AI assistant with low latency (under 500ms response time)?",
        "category": "Project-Based",
        "difficulty": "Advanced",
        "role_tags": ["AI/ML Engineer"],
        "is_general": False,
        "skill_tags": ["Audio AI", "Whisper", "Streaming", "Voice AI"],
        "expected_points": [
            "Streaming audio capture over WebSockets with Voice Activity Detection (VAD) to detect end of speech instantly",
            "Streaming ASR (Automatic Speech Recognition) using Whisper chunking or models like Conformer/FastConformer",
            "Streaming token output from LLM directly into a streaming Text-to-Speech (TTS) synthesizer (e.g. ElevenLabs/Cartesia)",
            "Overlapping pipelines: starting sentence TTS synthesis before the LLM finishes drafting the entire paragraph",
            "Interruption handling: canceling audio playback immediately if VAD detects user speaking again"
        ],
        "rubric": {
            "criteria": ["Streaming Protocol (WebSockets)", "Pipelined Overlap (LLM to TTS)", "Interruption Handling"],
            "key_concepts": ["vad", "streaming", "websockets", "tts", "asr", "whisper", "interruption", "latency"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): To break 500ms glass, never wait for full paragraphs. Use fast VAD to detect pauses; stream audio over WebSockets to ASR; feed LLM output tokens sentence-by-sentence into streaming TTS so the user hears audio while the LLM is still generating.",
        "is_active": True,
    },

    # =========================================================================
    # 5. FULL-STACK DEVELOPER (18 questions)
    # =========================================================================
    {
        "identifier": "fs-tech-react-server-components-01",
        "question_text": "Explain the architectural difference between React Server Components (RSC) and traditional Client Components in Next.js App Router. When should each be used?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["React", "Next.js", "Frontend Architecture"],
        "expected_points": [
            "Server Components render strictly on the server: zero client bundle impact, direct secure access to backend DBs/secrets, no useState/useEffect",
            "Client Components ('use client') hydrate in the browser: support browser events, state (useState/useReducer), and lifecycle hooks",
            "Mental model: Server Components by default for data fetching and heavy static layout; push Client Components to leaf nodes needing interactivity",
            "Passing data across boundaries: props must be JSON-serializable",
            "Composing Server Components as children of Client Components"
        ],
        "rubric": {
            "criteria": ["Zero-Bundle Advantage", "State Boundary Clarification", "Leaf Node Pattern"],
            "key_concepts": ["rsc", "server components", "client components", "use client", "hydration", "bundle size", "next.js"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Server components render on the server, producing zero client JavaScript and allowing direct database access. Use Client Components ('use client') only at the interactive leaf nodes (buttons, form inputs, animations).",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-cors-preflight-csrf-02",
        "question_text": "What is CORS (Cross-Origin Resource Sharing)? Explain what triggers a preflight OPTIONS request and how it differs from CSRF protection.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Web Security", "HTTP", "CORS", "CSRF"],
        "expected_points": [
            "CORS is a browser security mechanism enforcing Same-Origin Policy (SOP), relaxing it via response headers (Access-Control-Allow-Origin)",
            "Preflight OPTIONS request triggered when requests use non-simple methods (PUT, DELETE, PATCH) or custom headers (Authorization, application/json)",
            "Key distinction: CORS does not prevent requests from reaching the server; it prevents the browser frontend from reading the unauthorized response",
            "CSRF (Cross-Site Request Forgery) exploits ambient cookie credentials; defended with SameSite cookie attributes, CSRF tokens, or origin verification"
        ],
        "rubric": {
            "criteria": ["Browser Enforcement vs Server Protection", "Preflight Trigger Conditions", "CORS vs CSRF Distinction"],
            "key_concepts": ["cors", "preflight", "options", "csrf", "same-origin", "headers", "samesite"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): CORS is a browser security gate: browsers block responses from unauthorized origins. Non-simple requests (like POST with JSON or auth headers) fire an OPTIONS preflight first. CORS is not CSRF defense; CSRF requires SameSite cookies or anti-forgery tokens.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-jwt-vs-session-auth-03",
        "question_text": "Compare stateless JWT authentication with stateful server-side sessions. How do you handle token revocation and secure cookie storage?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["Authentication", "Security", "JWT", "OAuth"],
        "expected_points": [
            "Stateful sessions store session IDs in a DB/Redis; server can instantly revoke access by deleting session key, but requires DB lookup per request",
            "Stateless JWTs embed user claims cryptographically signed; eliminates DB lookup, but immediate revocation before expiration is hard without a blacklist",
            "Storage security: storing tokens in httpOnly, secure, SameSite cookies to protect against XSS token theft",
            "Modern compromise: short-lived access tokens (15 mins) paired with stateful or rotatable refresh tokens stored securely"
        ],
        "rubric": {
            "criteria": ["Stateless vs Stateful Tradeoffs", "Revocation Mechanics", "HttpOnly Cookie Storage"],
            "key_concepts": ["jwt", "session", "httponly", "refresh token", "revocation", "redis", "xss"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Sessions provide instant revocation at the cost of database lookups. JWTs scale horizontally without state lookups, but can't be immediately revoked without a blacklist. Store tokens in httpOnly, Secure cookies to defend against XSS, and use short expiration windows.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-database-indexing-b-tree-04",
        "question_text": "How do B-Tree indexes work in relational databases like PostgreSQL? What are composite indexes and the leftmost prefix rule?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["PostgreSQL", "Database Indexing", "SQL Performance"],
        "expected_points": [
            "B-Tree is a self-balancing search tree where nodes hold sorted keys and pointers, enabling O(log N) lookup, insertion, and range queries",
            "Composite index on multiple columns (A, B, C): sorted hierarchically by A, then B, then C",
            "Leftmost prefix rule: queries filtering on (A) or (A, B) or (A, B, C) utilize the index; queries filtering only on (B) or (C) cannot use it efficiently",
            "Write performance overhead: every index must be updated synchronously during INSERT, UPDATE, and DELETE operations"
        ],
        "rubric": {
            "criteria": ["B-Tree Mechanics", "Leftmost Prefix Rule", "Write vs Read Overhead"],
            "key_concepts": ["b-tree", "composite index", "leftmost prefix", "index scan", "write overhead", "postgresql"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): B-Trees maintain sorted balance, supporting fast equality and range scans. On a composite index (company_id, created_at), a query filtering by company_id works instantly; a query filtering only by created_at skips the index. Remember that each index slows down writes.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-react-rendering-re-renders-05",
        "question_text": "What causes a React component to re-render? How do you prevent unnecessary re-renders using useMemo, useCallback, and React.memo without premature optimization?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["React", "Performance Optimization", "Frontend"],
        "expected_points": [
            "Re-render triggers: state change, parent re-rendering, context change, or hook updates",
            "React.memo prevents component re-render if its props are shallowly identical",
            "useCallback memoizes function references to prevent child re-renders caused by new function references on every render",
            "useMemo memoizes expensive computation results",
            "Premature optimization risk: overusing memoization introduces memory overhead and code complexity that can be slower than lightweight virtual DOM reconciliations"
        ],
        "rubric": {
            "criteria": ["Render Trigger Clarity", "useCallback/useMemo Mechanism", "Avoidance of Premature Tuning"],
            "key_concepts": ["re-render", "react.memo", "usecallback", "usememo", "shallow comparison", "reconciliation"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): A component re-renders when state, props, or context changes, or when its parent re-renders. Use `React.memo` paired with `useCallback` when passing callbacks to heavy child lists. Don't wrap trivial functions: the comparison overhead often exceeds the cost of a basic re-render.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-rest-vs-graphql-grpc-06",
        "question_text": "Compare REST, GraphQL, and gRPC. In what architectural scenarios would you choose each for client-to-server and microservice-to-microservice communication?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["API Design", "GraphQL", "REST", "gRPC"],
        "expected_points": [
            "REST: ubiquitous HTTP standard, straightforward caching (HTTP 304/ETag), but risks over-fetching and under-fetching",
            "GraphQL: client requests exact required fields, ideal for complex frontend dashboards aggregating data across diverse entities; downside: complex caching and N+1 query risks",
            "gRPC: binary Protocol Buffers over HTTP/2, highly performant with strong typing and streaming, ideal for internal microservice-to-microservice RPCs",
            "Guideline: REST/GraphQL for public client-facing APIs, gRPC for low-latency backend microservices"
        ],
        "rubric": {
            "criteria": ["Three Protocol Characteristics", "Over/Under Fetching Problem", "Architectural Fit"],
            "key_concepts": ["rest", "graphql", "grpc", "protobuf", "over-fetching", "caching", "microservices"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): REST is simple and caches easily over HTTP. GraphQL shines for complex frontend views where clients select exact nested fields in one roundtrip. gRPC with Protobuf over HTTP/2 is ideal for high-throughput internal backend-to-backend communication.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-sql-transactions-acid-isolation-07",
        "question_text": "Explain ACID properties in database transactions. What are dirty reads, non-repeatable reads, and phantom reads, and how do isolation levels address them?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Database Architecture", "ACID", "Transactions", "PostgreSQL"],
        "expected_points": [
            "ACID definition: Atomicity (all-or-nothing), Consistency (integrity constraints), Isolation (concurrent execution independence), Durability (committed data persists)",
            "Dirty read: transaction reads uncommitted changes from another transaction",
            "Non-repeatable read: re-reading the same row returns different values because another transaction modified it",
            "Phantom read: re-running a range query returns new rows inserted by another committed transaction",
            "Isolation levels: Read Uncommitted, Read Committed (Postgres default), Repeatable Read, Serializable"
        ],
        "rubric": {
            "criteria": ["ACID Definitions", "Three Read Anomalies", "Four Isolation Levels"],
            "key_concepts": ["atomicity", "consistency", "isolation", "durability", "dirty read", "phantom read", "serializable"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): ACID ensures data integrity. Read anomalies occur during concurrency: Read Committed eliminates dirty reads. Repeatable Read locks observed rows so values cannot change. Serializable eliminates phantom rows by guaranteeing total serial execution order at higher lock contention cost.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-optimistic-vs-pessimistic-locking-08",
        "question_text": "How do you handle concurrent update conflicts (e.g. two users trying to book the same last seat)? Compare optimistic locking with pessimistic locking.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["Concurrency", "Database Locking", "System Design"],
        "expected_points": [
            "Pessimistic locking (`SELECT FOR UPDATE`): locks the database row immediately until transaction commits, blocking other readers/writers; best for high contention",
            "Optimistic locking: reads without locking, includes a `version` or `updated_at` column; on update: `WHERE id = ? AND version = ?`; fails if version changed",
            "Trade-offs: Pessimistic prevents conflicts but causes connection pool contention and deadlocks; Optimistic scales better for low-to-medium contention but requires client retry logic",
            "Application to race conditions like seat reservation or inventory balance"
        ],
        "rubric": {
            "criteria": ["Pessimistic Mechanism", "Optimistic Version Check", "Contention-Based Decision"],
            "key_concepts": ["optimistic locking", "pessimistic locking", "select for update", "version", "concurrency", "race condition"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): For low contention, use optimistic locking with a version number (`WHERE version = 1`). For high contention (booking the last seat in a stadium), use pessimistic locking (`SELECT ... FOR UPDATE`) inside a short transaction to prevent overselling.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-css-layout-flexbox-grid-09",
        "question_text": "Explain when to use CSS Flexbox versus CSS Grid. How do you design modern responsive layouts without relying on endless media queries?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["CSS", "Responsive Design", "Flexbox", "CSS Grid"],
        "expected_points": [
            "Flexbox is one-dimensional (content-driven, row OR column layout, ideal for navbars, toolbars, alignment)",
            "CSS Grid is two-dimensional (container-driven, rows AND columns simultaneously, ideal for full page layouts)",
            "Modern intrinsic responsiveness: using `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` to auto-wrap elements naturally",
            "Container queries (`@container`) enabling components to adapt based on their parent container's width rather than entire viewport"
        ],
        "rubric": {
            "criteria": ["1D vs 2D Mental Model", "Auto-fit / Minmax Pattern", "Container Queries Awareness"],
            "key_concepts": ["flexbox", "grid", "minmax", "auto-fit", "responsive", "container queries", "one-dimensional"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Flexbox is 1D (row or column alignment). Grid is 2D (rows and columns together). Create responsive card grids without media queries using `repeat(auto-fit, minmax(300px, 1fr))`, and use container queries for reusable widgets.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-caching-strategies-redis-cdn-10",
        "question_text": "What multi-layer caching strategies do you implement in a full-stack application across browser, CDN edge, Redis, and database query layers?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Caching", "Redis", "CDN", "Performance"],
        "expected_points": [
            "Browser layer: Cache-Control headers (immutable, max-age, stale-while-revalidate), ETags",
            "Edge/CDN layer: caching static assets and pre-rendered HTML close to users globally",
            "Application/Memory layer: Redis/Memcached for session stores, high-traffic database results, and API rate limiting",
            "Cache invalidation strategies: Cache-Aside (Lazy loading), Write-Through, Write-Behind",
            "Cache stampede mitigation (dog-piling): using locks or probabilistic early expiration"
        ],
        "rubric": {
            "criteria": ["Layered Cache Architecture", "Cache Invalidation Strategies", "Stampede Prevention"],
            "key_concepts": ["cache-control", "cdn", "redis", "cache-aside", "stale-while-revalidate", "invalidation", "stampede"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Layer caching: static assets at CDN with long max-age; API responses with `stale-while-revalidate`. Use Redis for expensive DB queries via Cache-Aside. Handle invalidation by key versioning or event-driven cache purging on mutations.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-websocket-vs-sse-polling-11",
        "question_text": "Compare WebSockets, Server-Sent Events (SSE), and Long Polling for real-time applications (e.g. chat, notifications, live status). How do you choose?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["WebSockets", "SSE", "Real-Time Systems", "Networking"],
        "expected_points": [
            "WebSockets: bi-directional, full-duplex TCP connection; ideal for interactive chat, gaming, collaborative editing",
            "SSE (Server-Sent Events): uni-directional (server to client), runs over standard HTTP, automatic reconnect built-in, native browser EventSource API; ideal for LLM streaming, live notifications, score feeds",
            "Long Polling: repeated client HTTP requests held open; heavy connection overhead, used only as legacy fallback",
            "Infrastructure considerations: load balancers and proxy sticky sessions or Redis Pub/Sub for horizontal scaling"
        ],
        "rubric": {
            "criteria": ["Bi-directional vs Uni-directional", "Protocol Overhead", "Appropriate Use Case Selection"],
            "key_concepts": ["websockets", "sse", "server-sent events", "long polling", "real-time", "http/2", "bidirectional"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): For uni-directional server streaming (like LLM token generation or live score feeds), SSE is simpler and runs over standard HTTP with auto-reconnect. For bi-directional two-way communication (chat, whiteboarding), use full-duplex WebSockets backed by Redis Pub/Sub.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-security-owasp-top-10-12",
        "question_text": "What are the most common web security vulnerabilities according to OWASP (e.g. SQL Injection, XSS, CSRF, IDOR)? How do you systematically prevent them?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Security", "OWASP", "XSS", "SQLi", "IDOR"],
        "expected_points": [
            "SQL Injection (SQLi): parameterized queries and ORM abstractions",
            "Cross-Site Scripting (XSS): escaping user input, React JSX automatic escaping, Content Security Policy (CSP)",
            "Cross-Site Request Forgery (CSRF): anti-CSRF tokens and SameSite cookie attributes",
            "Insecure Direct Object References (IDOR): server-side authorization checks verifying user ownership (`WHERE id = ? AND profile_id = current_user.id`)",
            "Security headers: HSTS, X-Content-Type-Options, Referrer-Policy"
        ],
        "rubric": {
            "criteria": ["Vulnerability Explanations", "Specific Preventative Code Practices", "Authorization Checks for IDOR"],
            "key_concepts": ["owasp", "sql injection", "xss", "csrf", "idor", "parameterized query", "authorization"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Prevent SQLi with parameterized queries / ORM. Prevent XSS with framework sanitization and strict CSP. Prevent IDOR by never trusting client IDs: always verify `user_id == session.user_id` on every database mutation.",
        "is_active": True,
    },
    {
        "identifier": "fs-proj-file-upload-s3-presigned-urls-13",
        "question_text": "How do you design a secure, scalable file upload system (e.g. user resumes or profile photos) without choking your backend application servers?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["File Uploads", "AWS S3", "Presigned URLs", "Cloud Architecture"],
        "expected_points": [
            "Direct-to-Cloud architecture using S3/Supabase Presigned URLs instead of buffering multi-megabyte payloads in application server memory",
            "Client requests short-lived signed upload URL from backend with content-type and size constraints",
            "Client uploads directly to cloud storage (PUT / POST)",
            "Storage webhook or backend confirmation endpoint updates database record",
            "Security checks: magic byte validation for actual MIME type, antivirus scanning, serving via CDN with random non-guessable keys"
        ],
        "rubric": {
            "criteria": ["Direct-to-Storage Architecture", "Presigned URL Workflow", "Security & Validation Safeguards"],
            "key_concepts": ["presigned url", "s3", "storage", "direct upload", "mime type", "validation", "cdn"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Never proxy file buffers through API servers. Have the client ask the backend for a presigned S3 URL with strict file size/MIME limits. The client uploads directly to S3, and an S3 event triggers virus scanning and updates the database record.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-database-migration-zero-downtime-14",
        "question_text": "How do you execute database schema migrations on high-traffic production databases without causing table locks or downtime (e.g. Expand and Contract pattern)?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Database Migrations", "Zero Downtime", "Alembic", "PostgreSQL"],
        "expected_points": [
            "Expand and Contract (Parallel Run) pattern: avoid breaking existing code during schema changes",
            "Phase 1 (Expand): add new column/table as nullable or with safe defaults; write dual-write code in application",
            "Phase 2 (Backfill): run asynchronous background jobs backfilling historical data without locking tables",
            "Phase 3 (Switch): update application readers to use new column",
            "Phase 4 (Contract): clean up old column in a final non-blocking migration",
            "Avoiding dangerous operations: `ADD COLUMN ... DEFAULT` in older DBs, creating indexes concurrently (`CREATE INDEX CONCURRENTLY`)"
        ],
        "rubric": {
            "criteria": ["Expand-Contract Phasing", "Concurrent Index Creation", "Dual-Write Strategy"],
            "key_concepts": ["zero downtime", "expand contract", "concurrently", "backfill", "dual-write", "alembic", "locks"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Use the Expand-Contract pattern: Add new column as nullable, update code to dual-write to both old and new columns, backfill historical rows in batches, switch readers to the new column, and finally drop the old column. Always create indexes with `CONCURRENTLY` in Postgres.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-state-management-server-client-15",
        "question_text": "How do you decide what state belongs in URL search params, server cache (TanStack Query/SWR), and local React state (Zustand/useState)?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["State Management", "React", "TanStack Query", "URL State"],
        "expected_points": [
            "URL search params: for shareable, bookmarkable state (filters, search queries, pagination, tab selection)",
            "Server state caching (TanStack Query/SWR): asynchronous data fetched from APIs, managing caching, deduping, background revalidation, and mutation invalidation",
            "Local UI state (useState): ephemeral component-specific UI state (dropdown open/close, hovered rows, form input drafts)",
            "Global client state (Zustand/Redux): complex cross-component client state that doesn't belong in the URL or server (audio players, multi-step wizards)"
        ],
        "rubric": {
            "criteria": ["URL Shareability", "Server Cache Separation", "Ephemeral Local State"],
            "key_concepts": ["url params", "server state", "tanstack query", "zustand", "ephemeral", "caching", "shareable"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): If a user wants to share or bookmark the view (filters, sorting, page), put it in the URL. If it's remote database data, use TanStack Query/SWR for caching and revalidation. If it's ephemeral UI toggle, keep it in local `useState`.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-rate-limiting-algorithms-16",
        "question_text": "How do you implement API rate limiting to protect services from abuse? Compare Token Bucket, Leaky Bucket, and Sliding Window algorithms.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer", "General Software Engineering"],
        "is_general": False,
        "skill_tags": ["Rate Limiting", "Redis", "API Gateway", "System Design"],
        "expected_points": [
            "Token Bucket: tokens added at a constant rate up to a capacity limit; permits bursts while maintaining average throughput",
            "Leaky Bucket: requests enter a queue and process at a smooth, constant outflow rate; eliminates bursts entirely",
            "Fixed Window: counts requests in static time windows; vulnerable to traffic spikes at window boundaries (2x limit)",
            "Sliding Window Counter: weighted combination of previous and current windows using Redis ZSET or hashes, offering high accuracy and low memory",
            "Returning standard HTTP 429 Too Many Requests with Retry-After header"
        ],
        "rubric": {
            "criteria": ["Algorithm Distinctions", "Burst Handling Comparison", "Redis Implementation"],
            "key_concepts": ["rate limiting", "token bucket", "leaky bucket", "sliding window", "redis", "429", "retry-after"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Token bucket is popular because it allows brief bursts while maintaining steady limits. For distributed backends, implement sliding window rate limiting in Redis using sorted sets (ZSET) or atomic Lua scripts, returning HTTP 429 when exhausted.",
        "is_active": True,
    },
    {
        "identifier": "fs-proj-fullstack-performance-audit-17",
        "question_text": "A student dashboard is experiencing high LCP (Largest Contentful Paint) and high API response times. How do you profile and optimize the entire stack?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["Web Performance", "Core Web Vitals", "LCP", "Profiling"],
        "expected_points": [
            "Frontend audit with Chrome DevTools Performance & Lighthouse to locate the LCP element",
            "Frontend fixes: optimizing hero image priorities (fetchpriority='high'), preconnecting fonts, removing blocking scripts",
            "Backend audit: inspecting slow query logs and API middleware latency",
            "Backend fixes: eliminating N+1 ORM queries via eager loading (`selectinload`), adding missing indexes, caching dashboard totals in Redis",
            "Measuring before and after using Real User Monitoring (RUM)"
        ],
        "rubric": {
            "criteria": ["Frontend Core Web Vitals", "Backend ORM & Query Tuning", "Systematic Profiling Approach"],
            "key_concepts": ["lcp", "core web vitals", "lighthouse", "n+1 query", "eager loading", "profiling", "caching"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Profile before changing code. For frontend LCP, preload hero assets, use Next.js `<Image>`, and eliminate render-blocking CSS. For backend, check APM traces to fix N+1 queries using `selectinload` and cache slow aggregates in Redis.",
        "is_active": True,
    },
    {
        "identifier": "fs-tech-accessibility-a11y-wcag-18",
        "question_text": "What practices ensure a web application is accessible according to WCAG 2.1 AA standards? How do you support keyboard navigation and screen readers?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["Full-Stack Developer"],
        "is_general": False,
        "skill_tags": ["Accessibility", "A11y", "WCAG", "Semantic HTML"],
        "expected_points": [
            "Use native semantic HTML elements (`<button>`, `<main>`, `<nav>`, `<dialog>`) instead of unclickable `<div>` elements",
            "Keyboard navigation: visible focus rings (:focus-visible), logical tab index order, and ESC key handling for modals",
            "Proper ARIA attributes when custom widgets are required (aria-expanded, aria-labelledby, aria-live for dynamic updates)",
            "Color contrast compliance (at least 4.5:1 for normal text, 3:1 for large text)",
            "Automated auditing with axe-core / Lighthouse and manual screen reader testing (VoiceOver/NVDA)"
        ],
        "rubric": {
            "criteria": ["Semantic HTML Primacy", "Keyboard Focus States", "Color Contrast & Screen Reader Support"],
            "key_concepts": ["accessibility", "a11y", "wcag", "semantic html", "focus-visible", "aria", "contrast"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Semantic HTML is the foundation: use `<button>` for actions and `<a>` for links. Ensure 4.5:1 color contrast, never remove `:focus-visible` rings, manage focus inside modals, and use `aria-live` for dynamic toast notifications.",
        "is_active": True,
    },

    # =========================================================================
    # 6. GENERAL SOFTWARE ENGINEERING & PROJECT DISCUSSION (18 questions)
    # =========================================================================
    {
        "identifier": "swe-proj-deep-dive-architecture-01",
        "question_text": "Walk me through the architecture of the most technically complex software project you have built. What was your role and what were the key trade-offs?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["System Architecture", "Trade-Offs", "Technical Communication"],
        "expected_points": [
            "High-level system topology: client, API layer, database, and background services",
            "Personal ownership: specific modules, algorithms, or pipelines designed and written",
            "Key trade-offs evaluated (e.g. monolithic vs microservice, SQL vs NoSQL, synchronous vs asynchronous)",
            "Technical obstacles encountered and how they were debugged and resolved",
            "Measurable metrics and outcomes of the project"
        ],
        "rubric": {
            "criteria": ["Architectural Depth", "Ownership & Contribution", "Thoughtful Trade-Offs"],
            "key_concepts": ["architecture", "tradeoff", "database", "api", "bottleneck", "ownership", "scale"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Draw a clear mental diagram: user -> frontend -> backend API -> datastore. Clearly distinguish your individual contribution from teammate work. Discuss why you chose technology X over Y and what you would do differently in version 2.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-solid-principles-02",
        "question_text": "Explain the SOLID principles of object-oriented and modular software design. Provide a concrete example of Single Responsibility or Dependency Inversion.",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["Software Design", "SOLID", "Clean Code"],
        "expected_points": [
            "Single Responsibility Principle (SRP): a class/module should have only one reason to change",
            "Open/Closed Principle (OCP): open for extension, closed for modification",
            "Liskov Substitution Principle (LSP): subtypes must be substitutable for their base types without altering program correctness",
            "Interface Segregation Principle (ISP): clients should not be forced to depend on interfaces they do not use",
            "Dependency Inversion Principle (DIP): depend upon abstractions (interfaces), not concrete implementations (enabling dependency injection and mockable tests)"
        ],
        "rubric": {
            "criteria": ["Accurate Acronym Definitions", "Concrete Code Example", "Testability Benefits"],
            "key_concepts": ["solid", "single responsibility", "dependency inversion", "open closed", "interface", "clean code"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Walk through each letter. For Dependency Inversion: instead of a service creating a hardcoded `PostgresDatabase()` instance directly, inject a `DatabaseInterface`, allowing you to swap in an in-memory test database during unit tests seamlessly.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-system-design-url-shortener-03",
        "question_text": "How would you design a scalable URL shortener service (like Bitly)? Discuss hashing/encoding, database choice, and redirect caching.",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["System Design", "Scalability", "Hashing", "Caching"],
        "expected_points": [
            "Functional and non-functional requirements: read-heavy system (100:1 read to write ratio), sub-50ms latency, high availability",
            "Short key generation: Base62 encoding ([a-zA-Z0-9]) on auto-incrementing 64-bit IDs or counter service to guarantee zero collisions",
            "Database choice: key-value store or relational DB with unique index on short_url",
            "Redirect handling: HTTP 301 (Permanent Redirect - browser caches redirect) vs HTTP 302 (Temporary Redirect - allows tracking click analytics)",
            "Caching layer: Redis caching top 20% most active URLs to handle 80%+ of redirection traffic"
        ],
        "rubric": {
            "criteria": ["Base62 Collision Handling", "301 vs 302 Redirect Tradeoff", "Read-Heavy Caching Architecture"],
            "key_concepts": ["base62", "url shortener", "redis", "301 redirect", "302 redirect", "collision", "read-heavy"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Clarify scale: 100M URLs generated per month. Use Base62 encoding of an auto-incrementing ID to prevent hash collisions. Use HTTP 302 redirects if you want analytics on every click. Cache the most active URLs in Redis to keep response times under 10ms.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-git-branching-merge-rebase-04",
        "question_text": "Compare `git merge` and `git rebase`. When would you use each, and how do you resolve a complex merge conflict safely?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Git", "Version Control", "Collaboration"],
        "expected_points": [
            "Git merge creates a dedicated merge commit preserving complete non-linear branch history",
            "Git rebase replays your commits sequentially on top of the target base branch, maintaining a clean, linear project history",
            "Golden rule of rebasing: never rebase public shared branches that others have pulled",
            "Conflict resolution process: understanding incoming vs current changes, testing code after conflict resolution, running unit tests before pushing"
        ],
        "rubric": {
            "criteria": ["Merge vs Rebase Mechanism", "Rebase Safety Rule", "Conflict Resolution Procedure"],
            "key_concepts": ["git", "merge", "rebase", "linear history", "conflict", "commit", "branch"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Use rebase on local feature branches to keep history linear and readable before creating a PR. Use merge for integrating into main branches to record true historical merges. Never rebase shared public branches.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-unit-integration-e2e-testing-05",
        "question_text": "Explain the testing pyramid (Unit, Integration, End-to-End). How do you decide what level of test to write for a new feature?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Testing", "QA", "CI/CD", "Test Automation"],
        "expected_points": [
            "Testing pyramid: broad base of fast, cheap Unit tests; middle layer of Integration tests; narrow top of comprehensive but slow E2E tests",
            "Unit tests: test individual isolated functions/classes in milliseconds using mocks for external dependencies",
            "Integration tests: verify interactions between modules (e.g. API endpoint interacting with real test database)",
            "E2E tests (Playwright/Cypress): drive real browser interactions verifying critical user journeys",
            "Balancing execution speed, cost, and debugging ease vs real-world confidence"
        ],
        "rubric": {
            "criteria": ["Pyramid Layers", "Mocking vs Real Dependencies", "Execution Speed vs Confidence Trade-off"],
            "key_concepts": ["unit test", "integration test", "e2e", "testing pyramid", "mock", "playwright", "confidence"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Unit tests verify business logic quickly in memory. Integration tests check API endpoints with real database transactions. E2E tests cover 3-5 critical revenue journeys (signup, checkout). Keep most tests at the unit/integration level to keep CI fast.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-debugging-production-memory-leak-06",
        "question_text": "How do you systematically debug a suspected memory leak or CPU spike in a running backend production application?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["General Software Engineering"],
        "is_general": True,
        "skill_tags": ["Debugging", "Profiling", "Memory Leaks", "Production Operations"],
        "expected_points": [
            "Observe metrics: inspecting memory usage slope over time in APM (Prometheus/Grafana/Datadog) to verify a steady upward trajectory",
            "Reproducing in staging or taking memory heap snapshots / CPU profiling dumps on production instances",
            "Analyzing heap profiles: comparing snapshots across time to identify object retention paths and unclosed connections/closures",
            "Common culprits: unclosed database connections, global caches growing without eviction (no TTL), event listeners not removed",
            "Mitigation: setting memory restart limits (e.g. k8s OOM limits) while deploying the targeted leak fix"
        ],
        "rubric": {
            "criteria": ["Metrics Observation First", "Heap Snapshot / Profiler Usage", "Common Leak Culprits"],
            "key_concepts": ["memory leak", "heap snapshot", "profiler", "cpu spike", "garbage collection", "apm", "unclosed connection"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Confirm the sawtooth vs monotonically increasing slope in Grafana. Capture two heap dumps 30 minutes apart and diff them in DevTools/Memory profilers. Look for retained arrays, unevicted caches, or circular references holding objects in memory.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-ci-cd-pipeline-design-07",
        "question_text": "What are the essential stages of a reliable automated CI/CD pipeline, and how do you ensure pull requests can be merged with confidence?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering"],
        "is_general": True,
        "skill_tags": ["CI/CD", "DevOps", "GitHub Actions", "Automation"],
        "expected_points": [
            "Fast feedback first: linting, static code analysis, and type checking in parallel (< 2 mins)",
            "Automated test suites: unit and integration tests running in ephemeral isolated test containers",
            "Security scanning: secret scanning, dependency vulnerability audit (Dependabot/Snyk)",
            "Build stage: compiling production artifacts, Docker container build, and asset hashing",
            "Deployment gating: automated staging deploy, smoke tests, and canary/blue-green production promotion"
        ],
        "rubric": {
            "criteria": ["Pipeline Stage Sequence", "Isolation of Test Environment", "Security & Deployment Gating"],
            "key_concepts": ["ci/cd", "github actions", "linting", "automated testing", "docker", "pipeline", "security scan"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Build a pipeline that gives feedback in under 5 minutes: static analysis & lint first, followed by unit tests, isolated integration tests with test containers, secret scanning, and automated preview deployments for PR review.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-concurrency-vs-parallelism-08",
        "question_text": "Explain the difference between concurrency and parallelism. How do async/await event loops (like in Node.js or Python asyncio) differ from multi-threading and multi-processing?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["Concurrency", "Parallelism", "Async/Await", "Operating Systems"],
        "expected_points": [
            "Concurrency is dealing with lots of things at once (structure); Parallelism is doing lots of things at once simultaneously on multiple CPU cores (execution)",
            "Async event loops: single-threaded cooperative multitasking utilizing non-blocking I/O multiplexing (epoll/kqueue); high throughput for I/O-bound tasks",
            "Multi-threading: multiple threads sharing memory inside one process; vulnerable to race conditions, deadlocks, and Python GIL limitations",
            "Multi-processing: separate processes with isolated memory spaces running on separate CPU cores; ideal for CPU-bound computations"
        ],
        "rubric": {
            "criteria": ["Concurrency vs Parallelism Definition", "Event Loop Non-Blocking I/O", "Threads vs Processes (I/O vs CPU)"],
            "key_concepts": ["concurrency", "parallelism", "event loop", "threads", "processes", "asyncio", "non-blocking"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Concurrency is about structure (handling multiple tasks interleaved); parallelism is about execution (running simultaneously on multiple physical cores). Async event loops shine for I/O-bound tasks (waiting on network/DB); use multi-processing for heavy CPU calculations.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-api-versioning-backward-compatibility-09",
        "question_text": "How do you version a public or shared API to introduce new functionality without breaking existing mobile and third-party web clients?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["API Design", "Versioning", "Backward Compatibility"],
        "expected_points": [
            "Versioning strategies: URI path versioning (/api/v1/...), header versioning (Accept: application/vnd.app.v1+json), query parameters",
            "Additive change philosophy: adding optional fields is non-breaking; renaming, removing, or changing types of existing fields is breaking",
            "Deprecation timeline: publishing clear deprecation warnings in headers (Sunset header) and documentation months ahead",
            "Tolerant reader pattern: ensuring clients parse only known fields and ignore new additions gracefully"
        ],
        "rubric": {
            "criteria": ["Versioning Approaches", "Additive Non-Breaking Rules", "Graceful Deprecation Protocol"],
            "key_concepts": ["api versioning", "backward compatibility", "breaking change", "deprecation", "sunset header", "additive"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Prefer URI versioning (/api/v1) for developer clarity. Follow additive design: always add optional fields, never remove or rename existing fields. When breaking changes are unavoidable, support both versions concurrently and emit `Sunset` headers.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-clean-code-refactoring-10",
        "question_text": "What code smells alert you that a piece of software is in dire need of refactoring? How do you refactor legacy code safely without breaking behavior?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Refactoring", "Clean Code", "Code Quality"],
        "expected_points": [
            "Common code smells: Long methods, God classes, duplicate code, deep nesting, magic numbers, boolean flags altering entire function flow",
            "Prerequisite for safe refactoring: comprehensive test harness (characterization tests) verifying existing behavior",
            "Small, incremental commits rather than sweeping massive rewrites",
            "Extracting functions, introducing parameter objects, and using descriptive variable names"
        ],
        "rubric": {
            "criteria": ["Code Smells Identification", "Test Safety Net First", "Small Incremental Steps"],
            "key_concepts": ["code smell", "refactoring", "god class", "unit tests", "clean code", "incremental", "legacy"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Spot smells like 200-line functions, deeply nested if/else blocks, and duplicate logic. Never refactor without existing tests: write characterization tests first to lock in current behavior, then take tiny refactoring steps, running tests after each edit.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-database-connection-pooling-11",
        "question_text": "What is a database connection pool, and why is creating a brand-new database connection for every incoming HTTP request an anti-pattern?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["Database Architecture", "Connection Pooling", "Performance"],
        "expected_points": [
            "Overhead of new connections: TCP 3-way handshake, TLS negotiation, authentication, and process memory allocation on the database server",
            "Connection pool: maintains a pool of pre-warmed, reusable connections shared across concurrent requests",
            "Sizing the pool: optimal pool size is limited by CPU cores and disk I/O (`pool_size = (2 * cores) + effective_spindle_count`)",
            "Connection pool starvation: requests blocking if connections are held open too long or not closed properly in `finally` blocks"
        ],
        "rubric": {
            "criteria": ["TCP/TLS Connection Overhead", "Pre-Warmed Pool Concept", "Starvation & Sizing Considerations"],
            "key_concepts": ["connection pool", "tcp handshake", "reusable", "pool size", "starvation", "database", "latency"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Establishing a database connection requires a TCP handshake, TLS exchange, and authentication, adding tens of milliseconds. A connection pool holds pre-warmed connections. Size it conservatively to avoid overwhelming DB CPU and memory, and always release connections in a `finally` block.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-cap-theorem-consistency-12",
        "question_text": "Explain the CAP theorem for distributed systems. When network partitions occur, how do CP systems differ from AP systems?",
        "category": "Technical",
        "difficulty": "Advanced",
        "role_tags": ["General Software Engineering"],
        "is_general": True,
        "skill_tags": ["Distributed Systems", "CAP Theorem", "Consensus"],
        "expected_points": [
            "CAP: Consistency (all nodes see the same data at the same time), Availability (every non-failing node returns a response), Partition Tolerance (system continues operating despite network message loss)",
            "Network partitions (P) are unavoidable in distributed physical networks",
            "CP (Consistency + Partition Tolerance): system rejects or delays writes if it cannot guarantee consistency across nodes (e.g. Raft/ZooKeeper/HBase)",
            "AP (Availability + Partition Tolerance): system accepts reads/writes on partitioned nodes, returning potentially stale data with eventual consistency (e.g. Cassandra/DynamoDB)",
            "PACELC extension: trade-offs during normal operation (Latency vs Consistency)"
        ],
        "rubric": {
            "criteria": ["CAP Components", "Unavoidability of Partitions", "CP vs AP Decision Matrix"],
            "key_concepts": ["cap theorem", "consistency", "availability", "partition tolerance", "eventual consistency", "cp", "ap"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Because networks inevitably experience partitions (P), distributed systems must choose between Consistency (CP) and Availability (AP) during partitions. A CP system returns errors to protect correctness; an AP system accepts requests and resolves eventual consistency later.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-observability-logs-metrics-traces-13",
        "question_text": "What are the three pillars of observability (Logs, Metrics, Traces)? How do distributed traces connect microservice calls?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering"],
        "is_general": True,
        "skill_tags": ["Observability", "Distributed Tracing", "OpenTelemetry", "Monitoring"],
        "expected_points": [
            "Metrics: aggregatable numerical data over time (counters, gauges, histograms) for high-level alerting and trends",
            "Logs: discrete timestamped records of specific events with rich contextual metadata",
            "Traces: end-to-end journey of a single request traversing multiple distributed services",
            "Distributed tracing mechanism: injecting and propagating trace ID and span IDs across HTTP/gRPC headers (W3C TraceContext)",
            "OpenTelemetry standard for unified vendor-neutral instrumentation"
        ],
        "rubric": {
            "criteria": ["Three Pillars Distinction", "Trace ID Header Propagation", "Root Cause Analysis Workflow"],
            "key_concepts": ["observability", "metrics", "logs", "traces", "opentelemetry", "trace id", "span"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Metrics alert you THAT something is wrong (e.g. 5xx rate spiked); Traces tell you WHERE it is wrong across services; Logs tell you WHY it happened. Distributed tracing passes a correlation `trace_id` in headers across microservices so you can visualize the call graph timeline.",
        "is_active": True,
    },
    {
        "identifier": "swe-proj-optimizing-legacy-bottleneck-14",
        "question_text": "Tell me about a specific performance bottleneck you diagnosed and resolved in code you wrote or inherited. What was the before and after metric?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Performance Optimization", "Profiling", "Problem Solving"],
        "expected_points": [
            "Context: which service or feature was slow and how users experienced the problem",
            "Instrumentation: tools used to measure the bottleneck (profilers, APM, EXPLAIN plans) before guessing",
            "Root cause: algorithmic inefficiency, unindexed query, synchronization lock, or excessive network serialization",
            "Implemented solution and verified before-and-after benchmarks"
        ],
        "rubric": {
            "criteria": ["Data-Driven Instrumentation", "Clear Root Cause", "Quantifiable Improvement"],
            "key_concepts": ["bottleneck", "profiling", "latency", "optimization", "before and after", "root cause", "metric"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Pick a concrete instance: e.g. an API endpoint taking 1.8 seconds due to an unindexed join and synchronous image processing. Mention using profiling to measure the exact hot spots, moving image processing to background workers, and bringing latency down to 120ms.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-idempotency-distributed-systems-15",
        "question_text": "What is an idempotent API operation? Why is idempotency critical for payment processing or background queue retries, and how do you implement it?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "Full-Stack Developer"],
        "is_general": True,
        "skill_tags": ["Idempotency", "API Design", "Distributed Systems", "Payments"],
        "expected_points": [
            "Definition: performing the operation multiple times produces the exact same side-effect and result as performing it once",
            "HTTP method semantics: GET, PUT, DELETE are idempotent by specification; POST is not idempotent by default",
            "Why critical: network timeouts cause clients to retry requests that may have succeeded on the server (risk of double charging)",
            "Implementation: Idempotency-Key header; storing keys in database/Redis with unique constraint; returning cached response on duplicates"
        ],
        "rubric": {
            "criteria": ["Idempotency Definition", "Retry Danger (Double Billing)", "Idempotency-Key Workflow"],
            "key_concepts": ["idempotency", "idempotency key", "retry", "network timeout", "payment", "put vs post", "deduplication"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): An idempotent operation can be executed repeatedly with the same outcome. For payments, clients generate a unique `Idempotency-Key`. The backend records this key in a database transaction: if a duplicate arrives, it returns the cached result without re-charging.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-message-queues-rabbitmq-kafka-16",
        "question_text": "Compare traditional message brokers (like RabbitMQ) with event streaming platforms (like Apache Kafka). When should you choose each?",
        "category": "Technical",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering"],
        "is_general": True,
        "skill_tags": ["Message Queues", "Kafka", "RabbitMQ", "Event-Driven Architecture"],
        "expected_points": [
            "RabbitMQ: traditional broker; messages are deleted once acknowledged by consumers; complex routing keys and exchange patterns",
            "Kafka: partitioned distributed append-only log; messages persist on disk for a retention period; consumers track their own offset",
            "Replaying messages: Kafka allows rewinding offsets to re-process historical streams; RabbitMQ cannot replay consumed messages natively",
            "Guideline: RabbitMQ for discrete task delegation and background job queues; Kafka for high-throughput streaming, real-time analytics, and event sourcing"
        ],
        "rubric": {
            "criteria": ["Message Broker vs Log", "Retention & Replayability", "Use Case Scenarios"],
            "key_concepts": ["rabbitmq", "kafka", "message queue", "event streaming", "offsets", "retention", "pub/sub"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): RabbitMQ is a smart broker/dumb consumer model: once a message is processed, it's gone. Kafka is a dumb broker/smart consumer append-only log: messages are retained for days, allowing multiple independent consumer groups to replay events at massive scale.",
        "is_active": True,
    },
    {
        "identifier": "swe-proj-technical-debt-management-17",
        "question_text": "How do you identify, prioritize, and pay down technical debt while maintaining momentum on business feature requests?",
        "category": "Project-Based",
        "difficulty": "Intermediate",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Technical Debt", "Engineering Leadership", "Sprint Planning"],
        "expected_points": [
            "Cataloging technical debt with severity based on developer velocity impact and production failure risk",
            "The Boy Scout Rule: leaving code slightly cleaner than you found it during regular feature work",
            "Allocating dedicated engineering capacity (e.g. 15-20% of every sprint) for infrastructure and debt paydown",
            "Translating tech debt into business risk: explaining to product managers how debt slows delivery velocity or causes churn",
            "Refactoring with test coverage before modifying fragile legacy paths"
        ],
        "rubric": {
            "criteria": ["Debt Classification", "Boy Scout Rule & Sprint Budget", "Business Translation"],
            "key_concepts": ["technical debt", "boy scout rule", "refactoring", "sprint budget", "velocity", "risk", "maintenance"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Don't ask for a 3-month pause to rewrite everything—it rarely works. Instead, allocate 15-20% of each sprint to high-impact debt, apply the Boy Scout rule on touched files, and tie tech debt directly to developer velocity and outage risks.",
        "is_active": True,
    },
    {
        "identifier": "swe-tech-secure-coding-secrets-management-18",
        "question_text": "What practices ensure sensitive credentials (API keys, database passwords, JWT secrets) are managed securely across development, CI/CD, and production?",
        "category": "Technical",
        "difficulty": "Beginner",
        "role_tags": ["General Software Engineering", "All Roles"],
        "is_general": True,
        "skill_tags": ["Security", "Secrets Management", "DevOps"],
        "expected_points": [
            "Never commit secrets to Git repositories; enforce with git pre-commit hooks and repo secret scanners (GitGuardian/TruffleHog)",
            "Environment variables and .env files kept out of version control via .gitignore (.env.example provided for documentation)",
            "Production secrets injected via dedicated secret managers (AWS Secrets Manager, HashiCorp Vault, Supabase Vault)",
            "Principle of least privilege for API tokens with expiration dates and immediate rotation workflows if compromised",
            "Ensuring secrets are never logged in plaintext or bundled into client-side browser builds"
        ],
        "rubric": {
            "criteria": ["Git Hygiene & Pre-Commit Checks", "Production Secret Managers", "Client Bundle & Log Protection"],
            "key_concepts": ["secrets management", "gitignore", "vault", "environment variables", "gitguardian", "least privilege", "rotation"]
        },
        "reference_answer": "Guidance Framework (For Reference Only): Never commit secrets to Git. Use pre-commit hooks and automated secret scanning. In development, use uncommitted `.env` files. In production, inject secrets at runtime from Vault or Cloud Secret Managers, and ensure server-side keys never leak into client-side JS bundles.",
        "is_active": True,
    },
]
