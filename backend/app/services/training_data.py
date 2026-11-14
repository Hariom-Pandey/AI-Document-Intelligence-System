"""
Comprehensive multi-class dataset for training and fine-tuning the
Document Classification model across 7 industry standard categories.
"""

DOCUMENT_DATASET = [
    # ==========================================
    # 1. LEGAL / CONTRACT
    # ==========================================
    (
        "This Mutual Non-Disclosure Agreement ('Agreement') is entered into by and between the parties hereto. "
        "Each party agrees to maintain in confidence all Confidential Information disclosed by the Disclosing Party. "
        "The Receiving Party shall exercise reasonable care, not less than the degree of care it uses for its own sensitive trade secrets, "
        "to prevent unauthorized disclosure, copying, or dissemination. This obligation shall survive termination for a period of three years.",
        "Legal / Contract"
    ),
    (
        "Commercial Lease Agreement: Landlord hereby leases to Tenant, and Tenant hereby leases from Landlord, "
        "the real property premises described herein. Tenant agrees to pay base monthly rent on or before the first day of each calendar month. "
        "Tenant shall deposit a security deposit to guarantee faithful performance of covenants, repairs, utilities, and surrender of premises.",
        "Legal / Contract"
    ),
    (
        "Master Services Agreement (MSA): Provider shall perform deliverables and professional consulting services specified in each Statement of Work (SOW). "
        "Customer shall pay invoices within thirty (30) calendar days of receipt. All intellectual property developed specifically under an SOW shall vest in Customer "
        "upon payment in full. Neither party shall be liable for consequential, incidental, or indirect damages.",
        "Legal / Contract"
    ),
    (
        "Employment and Non-Compete Agreement: Employee agrees that during employment and for twelve months thereafter, "
        "Employee shall not directly or indirectly engage in, perform services for, or invest in any competing business entity within the restricted territory. "
        "All inventions, patents, copyrights, and works made for hire created during employment belong exclusively to Employer.",
        "Legal / Contract"
    ),
    (
        "Settlement and Mutual Release Agreement: In consideration of the mutual covenants, payment sum, and releases contained herein, "
        "Plaintiff and Defendant fully release, acquit, and forever discharge each other from any and all claims, demands, liabilities, and causes of action, "
        "whether known or unknown, arising out of the civil litigation action in district court.",
        "Legal / Contract"
    ),
    (
        "Software License and Terms of Service (EULA): Licensor grants Licensee a non-exclusive, non-transferable, revocable license to install "
        "and execute the object code of the software program. Licensee shall not decompile, reverse engineer, disassemble, or sub-license the software. "
        "Warranty disclaimer: The software is provided 'AS IS' without warranty of merchantability or fitness for a particular purpose.",
        "Legal / Contract"
    ),
    (
        "Arbitration Clause and Dispute Resolution: Any controversy, claim, or breach arising out of or relating to this contract shall be determined by "
        "binding arbitration administered by the American Arbitration Association (AAA) under its Commercial Arbitration Rules. "
        "Judgment on the award rendered by the arbitrator(s) may be entered in any court having jurisdiction thereof.",
        "Legal / Contract"
    ),
    (
        "Indemnification and Limitation of Liability: Contractor shall indemnify, defend, and hold harmless Client, its directors, officers, and agents "
        "from and against any third-party claims, losses, costs, liabilities, and reasonable attorney fees arising out of Contractor's gross negligence, "
        "willful misconduct, or breach of statutory compliance obligations.",
        "Legal / Contract"
    ),
    (
        "Power of Attorney: Principal hereby appoints Attorney-in-Fact with full power and authority to act on Principal's behalf in executing contracts, "
        "managing bank accounts, real estate conveyances, tax filings, and legal affairs. This durable power of attorney shall not be affected by subsequent disability or incapacity.",
        "Legal / Contract"
    ),
    (
        "Partnership Dissolution Deed: The partners of the joint venture hereby agree to dissolve the partnership, wind up operations, liquidate remaining assets, "
        "discharge all partnership liabilities and creditor debts, and distribute residual capital accounts in accordance with the original partnership deed ratios.",
        "Legal / Contract"
    ),
    (
        "Non-Disclosure Agreement: Recipient shall keep confidential all technical designs, customer lists, and financial information received from Discloser. "
        "Injunctive relief and remedies available in the event of unauthorized disclosure or breach.",
        "Legal / Contract"
    ),
    (
        "Commercial Contract: The terms and conditions herein govern the sale and delivery of goods between buyer and seller. "
        "Governing law is Delaware, and all disputes will be resolved through arbitration.",
        "Legal / Contract"
    ),
    (
        "Residential Lease Agreement: Tenant agrees to pay landlord monthly rent of $2,400 on the first of each month. Security deposit is refundable upon termination.",
        "Legal / Contract"
    ),
    (
        "Independent Contractor Agreement: Contractor will provide consulting services to client as an independent contractor, with no employee benefits, withholding, or joint liability.",
        "Legal / Contract"
    ),
    (
        "Intellectual Property Assignment Agreement: Assignor irrevocably sells and assigns all right, title, and interest in patents, inventions, trademarks, and copyrights to assignee.",
        "Legal / Contract"
    ),

    # ==========================================
    # 2. FINANCIAL / INVOICE
    # ==========================================
    (
        "COMMERCIAL INVOICE #INV-2026-889. Bill To: Global Enterprises Corp. Due Date: Net 30 days. "
        "Item 1: Enterprise Cloud Hosting (12 Months) - Unit Price: $1,200.00 - Total: $14,400.00. "
        "Item 2: Implementation Consulting (40 Hours) - Unit Price: $150.00 - Total: $6,000.00. "
        "Subtotal: $20,400.00. Sales Tax (8.25%): $1,683.00. Total Balance Due: $22,083.00. Please remit wire payment to account.",
        "Financial / Invoice"
    ),
    (
        "Consolidated Balance Sheet: Total Current Assets: Cash and cash equivalents $45,200,000; Accounts receivable less allowance for doubtful accounts $12,800,000; "
        "Inventories $8,400,000. Total Liabilities: Accounts payable $9,500,000; Short-term debt $3,200,000; Long-term debt obligations $25,000,000. "
        "Stockholders' Equity: Common stock and retained earnings $28,700,000.",
        "Financial / Invoice"
    ),
    (
        "Quarterly Income Statement and Earnings Report: Total Net Revenue increased by 18% year-over-year to $182.4 million. "
        "Gross margin reached 68.5%. Operating expenses included Research & Development $34.2M, Sales & Marketing $42.1M, and General Administrative $18.6M. "
        "Operating Income (EBITDA) was $45.8 million, yielding diluted earnings per share (EPS) of $0.84.",
        "Financial / Invoice"
    ),
    (
        "Statement of Cash Flows: Cash flows from operating activities generated $52.3M. Capital expenditures (CapEx) for property, plant, and equipment were $14.1M. "
        "Financing activities included repayment of credit facilities of $10.0M and dividend payments to shareholders totaling $8.5M. "
        "Ending cash and restricted cash balance stood at $84.2 million.",
        "Financial / Invoice"
    ),
    (
        "Purchase Order (PO #84729): Vendor ID: V-99321. Shipping Address: Distribution Hub 4. Payment terms: 2/10 Net 60. "
        "Quantity: 500 units Precision Bearings SKU #BRG-400. Unit cost: $48.50. Extended price: $24,250.00. "
        "FOB Destination freight prepaid. Authorized procurement officer signature required upon receipt.",
        "Financial / Invoice"
    ),
    (
        "Corporate Tax Return Form 1120 Schedule K: Gross receipts or sales $9,450,200; Cost of goods sold $4,210,000; "
        "Gross profit $5,240,200. Allowable tax deductions: Officer compensation $820,000; Salaries and wages $1,450,000; Depreciation deduction $310,000. "
        "Taxable income before net operating loss deduction $1,210,000. Total income tax liability due: $254,100.",
        "Financial / Invoice"
    ),
    (
        "Bank Account Statement of Account: Monthly transaction summary. Opening Ledger Balance: $112,430.22. "
        "Total Electronic Deposits & ACH Credits: $84,320.00. Total Withdrawals, Checks & Debit Sweeps: $62,110.15. "
        "Service charges and wire transfer fees: $125.00. Closing Available Balance as of October 31: $134,515.07.",
        "Financial / Invoice"
    ),
    (
        "Audit Opinion Report by Independent Certified Public Accountants: In our opinion, the accompanying consolidated financial statements "
        "present fairly, in all material respects, the financial position of the Company as of December 31, and the results of its operations and its cash flows "
        "for the year then ended in conformity with U.S. Generally Accepted Accounting Principles (US GAAP).",
        "Financial / Invoice"
    ),
    (
        "Credit Facility and Term Loan Agreement: Borrower agrees to borrow principal sum of $15,000,000 bearing interest at SOFR plus 2.75% per annum. "
        "Borrower shall maintain a Debt Service Coverage Ratio (DSCR) of not less than 1.25x and a Maximum Leverage Ratio not exceeding 3.50x. "
        "Quarterly amortization schedule and covenant compliance certificates required.",
        "Financial / Invoice"
    ),
    (
        "Tax Invoice #9982: Billed to Acme Corp. Total taxable amount $5,400.00. Tax rate 10%, total tax $540.00. Total invoice amount payable $5,940.00. Please remit to our bank account.",
        "Financial / Invoice"
    ),
    (
        "Financial Statement for Year Ended Dec 31: Net revenues grew to $48.2 million, operating profit margin was 24%, EBITDA totaled $11.5M, and net cash flow remained positive.",
        "Financial / Invoice"
    ),
    (
        "Billing Statement & Remittance Advice: Account balance $14,920.50. Payment due upon receipt. Late payment fee of 1.5% applied monthly on outstanding balances.",
        "Financial / Invoice"
    ),
    (
        "Receipt of Payment: Paid in full by Mastercard credit card ending in 4092. Total charged: $1,250.00. Thank you for your payment.",
        "Financial / Invoice"
    ),
    (
        "Quarterly Profit and Loss Statement: Gross profit $3,210,000, selling and administrative expenses $1,800,000, operating income $1,410,000, income taxes $296,000, net profit $1,114,000.",
        "Financial / Invoice"
    ),

    # ==========================================
    # 3. TECHNICAL / ENGINEERING
    # ==========================================
    (
        "Microservices Architecture Specification: The backend service is decomposed into autonomous containerized microservices communicating via gRPC "
        "and RESTful JSON APIs. Service discovery is managed by Kubernetes CoreDNS. Ingress controllers route traffic with TLS termination, "
        "JWT token authentication, and distributed rate limiting implemented via Redis token bucket algorithm.",
        "Technical / Engineering"
    ),
    (
        "REST API Documentation and Schema: Endpoint: POST /api/v2/embeddings. Request Headers: Authorization: Bearer <JWT>, Content-Type: application/json. "
        "Request Body: { 'texts': ['string'], 'model': 'all-MiniLM-L6-v2', 'normalize': true }. "
        "Response: 200 OK, JSON array of 384-dimensional floating point vectors. Error handling: 400 Bad Request, 401 Unauthorized, 429 Rate Limit Exceeded.",
        "Technical / Engineering"
    ),
    (
        "Database Schema and Query Optimization: Table definition: CREATE TABLE document_chunks (id UUID PRIMARY KEY, doc_id UUID REFERENCES documents(id) ON DELETE CASCADE, "
        "chunk_index INT, page_number INT, text TEXT, embedding VECTOR(384)). "
        "Create index using HNSW or IVFFlat for fast approximate nearest neighbor vector search with cosine distance metric.",
        "Technical / Engineering"
    ),
    (
        "DevOps CI/CD Deployment Pipeline: Automated build workflow using Docker containers and GitHub Actions. "
        "Pipeline steps: 1. Code checkout and linting with flake8/black; 2. Unit and integration test execution with pytest; "
        "3. Multi-stage Docker build producing lightweight Alpine container; 4. Security scan with Trivy; 5. Push image to Container Registry; 6. Helm chart deploy to AWS EKS cluster.",
        "Technical / Engineering"
    ),
    (
        "Hardware Embedded Firmware Specification: The firmware executes on an ARM Cortex-M4 microcontroller operating at 168 MHz with 1MB Flash memory. "
        "Communication with digital accelerometer and temperature sensors occurs over SPI and I2C buses at 400 kHz. "
        "DMA channels handle ADC data acquisition without interrupting RTOS task scheduling loops.",
        "Technical / Engineering"
    ),
    (
        "Deep Learning Neural Network Model Card: Architecture: RoBERTa-based bidirectional encoder transformer with 12 layers, 12 attention heads, "
        "and 125M parameters. Trained using masked language modeling (MLM) and fine-tuned on SQuAD 2.0 question answering spans with cross-entropy loss, "
        "AdamW optimizer, learning rate 3e-5, warmup ratio 0.1, and linear decay schedule on Nvidia A100 GPUs.",
        "Technical / Engineering"
    ),
    (
        "Network Security and Firewall Configuration: All ingress TCP traffic on port 22 is blocked from public internet. "
        "Application tier communicates with database tier over private VPC subnets with Network Security Groups (NSGs). "
        "mTLS (Mutual TLS 1.3) encryption enforced for inter-service RPC communication. Intrusion detection system monitors anomalous outbound UDP traffic.",
        "Technical / Engineering"
    ),
    (
        "Distributed System High Availability & Failover: Apache Kafka cluster deployed across three availability zones with replication factor of 3 "
        "and min.insync.replicas=2 to guarantee zero data loss. Zookeeper ensemble handles leader election and consumer group offset management. "
        "P99 latency monitored under 100,000 messages per second workload.",
        "Technical / Engineering"
    ),
    (
        "Software Engineering Guide: The backend is built using FastAPI and Python 3.12 with asynchronous endpoints, SQLAlchemy ORM, and SQLite database storage.",
        "Technical / Engineering"
    ),
    (
        "API Reference: GET /api/v1/users returns JSON list of user objects with id, username, email, and created_at timestamps. Status code 200 on success.",
        "Technical / Engineering"
    ),
    (
        "Database Architecture: The relational schema consists of tables with foreign key constraints, indexes on document_id, and transaction rollback support.",
        "Technical / Engineering"
    ),
    (
        "Docker Container Deployment: The multi-stage Dockerfile uses python:3.12-slim base image, installs wheels, exposes port 8000, and executes uvicorn runner.",
        "Technical / Engineering"
    ),
    (
        "Front-End Web Development: The React application is bundled with Vite, using React hooks, CSS variables, Lucide icons, and component-based routing.",
        "Technical / Engineering"
    ),

    # ==========================================
    # 4. ACADEMIC / RESEARCH
    # ==========================================
    (
        "Abstract: In this paper, we propose a novel self-supervised contrastive learning framework for multimodal representation learning. "
        "Extensive empirical evaluations across five benchmark datasets demonstrate that our approach outperforms existing baselines by 4.2% in Top-1 accuracy. "
        "We conduct ablation studies verifying the contribution of each architectural module, followed by statistical significance tests (p < 0.01).",
        "Academic / Research"
    ),
    (
        "Methodology and Experimental Design: We conducted a randomized controlled trial evaluating algorithm efficiency. "
        "Participants were divided into control (n=120) and experimental (n=120) cohorts. Data was analyzed using two-way Analysis of Variance (ANOVA) "
        "and multivariate linear regression. Confidence intervals (95% CI) and effect sizes (Cohen's d) were calculated to confirm hypothesis validity.",
        "Academic / Research"
    ),
    (
        "Literature Review: Early foundational research in natural language processing relied heavily on symbolic grammar systems and rule-based parsers (Chomsky, 1957). "
        "The advent of statistical machine translation (Brown et al., 1993) and distributed representations (Mikolov et al., 2013) shifted the paradigm toward neural embeddings, "
        "culminating in the Transformer self-attention mechanism (Vaswani et al., 2017).",
        "Academic / Research"
    ),
    (
        "Doctoral Dissertation Proposal: A Qualitative and Quantitative Analysis of Cognitive Load in Human-AI Interaction. "
        "Theoretical framework: Cognitive Load Theory and Distributed Cognition. Research questions examine task completion latency and subjective mental workload "
        "using NASA-TLX indices. Ethical approval obtained from the Institutional Review Board (IRB #2026-081).",
        "Academic / Research"
    ),
    (
        "Results and Discussion: Table 3 presents the ablation performance across epochs. The baseline model achieved an F1-score of 0.78, "
        "whereas incorporating adversarial regularization increased the score to 0.86 (t = 4.82, p < 0.001). "
        "These findings support our hypothesis that feature orthogonalization prevents representation collapse in latent space.",
        "Academic / Research"
    ),
    (
        "Peer-Reviewed Journal Submission: Quantum Entanglement and Coherence Times in Superconducting Qubits. "
        "We report experimental measurements of T1 relaxation and T2 dephasing times in a transmon qubit architecture at 15 mK dilution refrigerator temperatures. "
        "Decoherence mechanisms due to quasiparticle tunneling and dielectric loss tangents are modeled mathematically.",
        "Academic / Research"
    ),
    (
        "Bibliography and Citation References: [1] Devlin, J. et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers. NAACL. "
        "[2] Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese Networks. EMNLP. "
        "[3] Lewis, M. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.",
        "Academic / Research"
    ),
    (
        "Abstract: This research paper analyzes the empirical findings of our experimental study on deep learning optimization. Results demonstrate statistical significance (p < 0.05).",
        "Academic / Research"
    ),
    (
        "Academic Thesis: Chapter 4 presents quantitative data collected from 500 respondents. Descriptive statistics, correlation matrices, and linear regression models were calculated.",
        "Academic / Research"
    ),
    (
        "Scientific Journal Article: We formulate a novel theoretical hypothesis regarding quantum coherence. Mathematical proofs, derivation equations, and bibliography are provided.",
        "Academic / Research"
    ),
    (
        "Research Methodology: The experiment utilized a double-blind protocol with an active control group. Data was evaluated using ANOVA and peer-reviewed benchmark datasets.",
        "Academic / Research"
    ),

    # ==========================================
    # 5. MEDICAL / HEALTHCARE
    # ==========================================
    (
        "Clinical Patient Summary & Medical History: Patient is a 58-year-old male presenting with acute dyspnea, non-productive cough, and chest tightness. "
        "Past medical history significant for essential hypertension and Type 2 diabetes mellitus managed on Metformin 1000mg BID. "
        "Vital signs: Blood pressure 142/88 mmHg, heart rate 86 bpm regular, respiratory rate 20/min, SpO2 96% on ambient air.",
        "Medical / Healthcare"
    ),
    (
        "Radiology & Diagnostic Imaging Report: Examination: Contrast-enhanced Computed Tomography (CT) scan of chest, abdomen, and pelvis. "
        "Findings: Lungs demonstrate clear parenchymal expansion without focal consolidation, pleural effusion, or pneumothorax. "
        "No evidence of acute pulmonary embolism in central pulmonary arterial tree. Mediastinal and hilar lymph nodes within normal limits.",
        "Medical / Healthcare"
    ),
    (
        "Pathology Laboratory Report: Specimen: Core needle biopsy of right breast nodule. Histopathology reveals infiltrating ductal carcinoma, "
        "Nottingham Grade II. Immunohistochemical staining profile: Estrogen Receptor (ER) positive (95%), Progesterone Receptor (PR) positive (80%), "
        "HER2/neu negative by IHC (score 1+), Ki-67 proliferative index 18%. Surgical margins clear.",
        "Medical / Healthcare"
    ),
    (
        "Physician Prescription and Treatment Plan: Rx: 1. Amoxicillin-Clavulanate 875/125 mg PO twice daily with meals for 10 days; "
        "2. Albuterol Sulfate HFA Inhaler 90 mcg, 2 puffs inhaled every 4 to 6 hours as needed for bronchospasm; "
        "3. Acetaminophen 500 mg PO every 6 hours PRN mild-to-moderate pain or fever. Patient advised on medication adherence and hydration.",
        "Medical / Healthcare"
    ),
    (
        "Hospital Inpatient Discharge Summary: Admission Diagnosis: Acute bacterial pneumonia. Hospital Course: Patient was admitted to medical ward "
        "and initiated on IV Ceftriaxone and Azithromycin. Demonstrated prompt clinical improvement with defervescence by hospital day 3. "
        "Discharged in stable condition. Follow-up clinic appointment scheduled with primary care physician in 2 weeks.",
        "Medical / Healthcare"
    ),
    (
        "Cardiology Consultation & Echocardiogram: Transthoracic echocardiography reveals normal left ventricular size and systolic function "
        "with an estimated left ventricular ejection fraction (LVEF) of 60-65%. No regional wall motion abnormalities. "
        "Mild aortic valve sclerosis without significant stenosis. Trace mitral regurgitation. Normal right ventricular systolic pressure.",
        "Medical / Healthcare"
    ),
    (
        "Clinical Progress Note: Patient examined in outpatient clinic. Blood pressure 128/82 mmHg. Lungs clear to auscultation bilaterally. Heart rate and rhythm normal. Refilled prescription for Atorvastatin 20mg.",
        "Medical / Healthcare"
    ),
    (
        "Medical Examination Report: Patient presented with symptoms of acute viral pharyngitis, mild fever, and sore throat. Recommended hydration, rest, and ibuprofen for pain management.",
        "Medical / Healthcare"
    ),
    (
        "Laboratory Test Results: Comprehensive metabolic panel (CMP). Fasting glucose 94 mg/dL (normal), Creatinine 0.9 mg/dL (normal), Liver enzymes AST 22 U/L, ALT 24 U/L within reference limits.",
        "Medical / Healthcare"
    ),
    (
        "Doctor Prescription Order: Take Metformin 500mg by mouth once daily with evening meal. Dispense #30 tablets. Zero refills authorized without follow-up HbA1c test.",
        "Medical / Healthcare"
    ),

    # ==========================================
    # 6. HUMAN RESOURCES / RESUME
    # ==========================================
    (
        "Curriculum Vitae (CV) - Jane Doe, Senior Software Engineer. Contact: jane.doe@email.com, (555) 234-5678, San Francisco, CA. "
        "Professional Summary: 8+ years experience designing scalable distributed cloud backends, Python microservices, and machine learning pipelines. "
        "Education: Bachelor of Science in Computer Science, University of California, Berkeley. "
        "Technical Skills: Python, FastAPI, Docker, Kubernetes, PyTorch, SQL, AWS, Git, CI/CD.",
        "Human Resources / Resume"
    ),
    (
        "Professional Work Experience: Staff DevOps Engineer, Apex Cloud Solutions (2021 - Present). "
        "Spearheaded Kubernetes migration reducing cloud infrastructure hosting expenses by 34%. "
        "Implemented automated zero-downtime blue/green deployment pipelines servicing 10 million daily active users. "
        "Mentored team of 6 junior and mid-level engineers in reliability best practices.",
        "Human Resources / Resume"
    ),
    (
        "Job Description & Requisition: Title: Lead Data Scientist - Natural Language Processing. Department: AI Research. "
        "Requirements: Master's or Ph.D. in Computer Science or computational linguistics with 5+ years experience deploying NLP models. "
        "Responsibilities: Architect Retrieval-Augmented Generation (RAG) search systems, optimize vector embeddings, and lead model evaluation. "
        "Compensation: Competitive salary $160,000 - $195,000 plus equity options, 401(k) matching, and comprehensive healthcare benefits.",
        "Human Resources / Resume"
    ),
    (
        "Annual Employee Performance Review: Employee: Alex Morgan. Manager: Sarah Jenkins. Period: Fiscal Year 2026. "
        "Evaluation of Core Competencies: Technical Execution: Exceeds Expectations. Collaboration & Leadership: Exceeds Expectations. "
        "Key Accomplishments: Successfully delivered the Enterprise Search v2 milestone on schedule. Promoted to Senior Engineering Manager.",
        "Human Resources / Resume"
    ),
    (
        "Employee Onboarding and Benefits Enrollment Guide: Welcome to the company. Please complete Form W-4 and Form I-9 verification within 3 business days. "
        "Health insurance coverage (Medical, Dental, Vision) begins on the first of the month following hire date. "
        "Flexible Paid Time Off (PTO), 11 paid company holidays, parental leave policy, and 401(k) retirement savings plan details outlined herein.",
        "Human Resources / Resume"
    ),
    (
        "Resume - David Kim, Product Marketing Manager. Experience: Led go-to-market strategy for B2B SaaS software launch resulting in $4.2M ARR in Year 1. "
        "Conducted customer persona interviews, pricing sensitivity analysis, and competitive product positioning. "
        "Education: MBA, Northwestern University, Kellogg School of Management; B.A. Economics.",
        "Human Resources / Resume"
    ),
    (
        "Candidate Resume: Professional software engineer with 5 years experience in React, JavaScript, Node.js, and CSS. Bachelor of Technology in Information Technology. Strong communication skills.",
        "Human Resources / Resume"
    ),
    (
        "Job Posting: Senior Cloud Architect. Responsibilities include designing scalable AWS infrastructure, leading migration projects, and mentoring junior engineers. Competitive salary and benefits package.",
        "Human Resources / Resume"
    ),
    (
        "Employee Handbook: Company code of conduct, equal opportunity employment statement, remote work policy, grievance procedures, and annual performance appraisal guidelines.",
        "Human Resources / Resume"
    ),
    (
        "Offer Letter of Employment: We are pleased to offer you the full-time position of Software Developer with an annual starting salary of $115,000, healthcare insurance, and stock options.",
        "Human Resources / Resume"
    ),

    # ==========================================
    # 7. GENERAL BUSINESS / REPORT
    # ==========================================
    (
        "Executive Summary and Business Proposal: Strategic Expansion into Emerging Markets. This business proposal outlines our market entry strategy, "
        "capital expenditure requirements, revenue projections, and risk mitigation frameworks. By establishing regional distribution centers, "
        "the company expects to capture an estimated 14% market share over the next 36 months, delivering positive net ROI within year two.",
        "General Business / Report"
    ),
    (
        "Market Research and Competitive Industry Analysis: The global document intelligence software market size was valued at $4.8 billion in 2025 "
        "and is projected to expand at a compound annual growth rate (CAGR) of 22.4% through 2032. Key market drivers include the enterprise adoption "
        "of generative AI, automated OCR data extraction, and workflow efficiency mandates across legal and financial sectors.",
        "General Business / Report"
    ),
    (
        "Board of Directors Meeting Minutes: Date: October 18, 2026. Chair: Jonathan Bradley. Present: Full Board of Directors. "
        "Agenda Items: Review of Q3 operational performance, approval of Series B financing term sheet, and appointment of Chief Operating Officer. "
        "Resolutions: Motion to approve the $25 million equity financing unanimously carried by all voting members.",
        "General Business / Report"
    ),
    (
        "Company Standard Operating Procedure (SOP #OPS-204): Vendor Selection and Procurement Workflow. "
        "Purpose: Establish transparent guidelines for vendor evaluation, price quotation bidding, contract negotiation, and security compliance review. "
        "All purchases exceeding $10,000 require competitive bids from at least three qualified vendors and approval from Department Vice President.",
        "General Business / Report"
    ),
    (
        "Annual Corporate Sustainability and ESG Report: Environmental, Social, and Governance performance overview. "
        "Our organization reduced greenhouse gas emissions by 28% across operations, transitioned two primary data centers to 100% renewable solar power, "
        "and increased supplier diversity expenditures. Governance policies updated to enforce ethical AI deployment standards.",
        "General Business / Report"
    ),
    (
        "Project Charter and Roadmap: Project Odyssey - Next Generation Customer Portal. Project Sponsors: VP Customer Success and Chief Information Officer. "
        "Objectives: Modernize customer self-service workflows, reduce support ticket resolution turnaround by 40%, and achieve 99.95% system uptime. "
        "Key Deliverables and Milestones: Sprint 1 Requirements, Sprint 4 Prototype, Sprint 8 Production Release.",
        "General Business / Report"
    ),
    (
        "Quarterly Business Review (QBR): Presentation summarizing strategic business initiatives, sales pipeline expansion, customer retention rates, and marketing campaign performance.",
        "General Business / Report"
    ),
    (
        "Company Strategic Plan 2027: Five-year corporate roadmap focusing on digital transformation, customer acquisition, operational efficiency, and sustainable revenue growth.",
        "General Business / Report"
    ),
    (
        "Project Status Update: Executive summary of project milestones, budget tracking, resource allocation, and key risks for management stakeholder review.",
        "General Business / Report"
    ),
    (
        "Market Research Whitepaper: Global trends in enterprise cloud computing, consumer adoption patterns, competitive landscape analysis, and projected market share growth.",
        "General Business / Report"
    )
]
