AI-Based Tender Evaluation and Eligibility Analysis for Government Procurement by CRPF

Context

Government organisations such as the Central Reserve Police Force (CRPF) issue tenders to procure goods and services. Each tender specifies detailed requirements: technical specifications, financial thresholds, compliance rules, eligibility conditions, document checklists and mandatory certifications. These requirements are typically written in formal, legally careful language and are spread across many pages of the tender document.

Private companies respond with bids, each submitting their own set of supporting documents — company profiles, financial statements, experience letters, tax registrations, certifications and more. The documents arrive in many formats: structured text PDFs, scanned copies, Word files, tables and even photographs of physical certificates. The same kind of information is presented in many different ways across bidders.

Evaluating whether each bidder meets the stated eligibility criteria is currently a manual process. It is slow, inconsistent across evaluators, prone to oversight, and hard to audit. For a single tender, a committee may spend days cross-checking hundreds of pages against a list of criteria, and two evaluators may reach different conclusions from the same set of documents. There is a clear opportunity to bring modern AI techniques to this problem — to extract structured information from unstructured tender and bid documents, apply the eligibility rules consistently, and produce explainable evaluation reports that a human officer can trust and sign off on.

 

The Problem

Design a technical platform that, given a tender document and a set of bidder submissions, can do the following:Understand the tender

Extract the eligibility criteria from the tender document — technical specifications, financial thresholds, compliance conditions, and document and certification requirements.
Distinguish between mandatory and optional criteria.
Capture each criterion in a form that can be matched against a bidder's submission.
 

Understand each bidder

Parse every bidder submission, regardless of whether the documents are typed PDFs, scanned copies, Word files or photographs.
Extract the values and evidence relevant to each criterion from those documents.
Handle variation in how bidders present the same information.
 

Evaluate and explain

For each bidder, decide whether they are Eligible, Not Eligible, or Need Manual Review against each criterion and overall.
Produce an explanation for every verdict that references the specific criterion, the specific document and the specific value that drove the decision.
Surface ambiguous or uncertain cases for human review rather than silently disqualifying them.
Produce a consolidated evaluation report that a procurement officer can use as the basis for a decision.
 

Non-Negotiables

Every verdict must be explainable at the criterion level — which criterion was being checked, which document was used, what value was found, and why the bidder passed, failed or needs review.
The system must never silently disqualify a bidder. Ambiguous or uncertain cases must be surfaced for human review with the reason.
The system must handle scanned documents and photographs, not only digital text.
The system must be auditable end-to-end and suitable for use in a formal government procurement decision.
Real tender and bid data will not be released for Round 1. Any Round 2 implementation will run on representative mock or redacted documents inside a sandbox.
 

What Success Looks Like

A working solution should eventually make the following behaviours possible:

A procurement officer uploads a tender document and a set of bidder submissions. The system extracts the eligibility criteria automatically and lists them for review.
For each bidder, the system produces a criterion-by-criterion evaluation with references back to the source documents.
Clearly eligible and clearly ineligible bidders are marked as such; genuinely ambiguous cases are flagged for manual review with the reason for the ambiguity.
A consolidated report can be exported and signed off, with a complete audit trail of every automated decision.
 

Sample Scenario

To help you visualise the problem, consider a representative scenario:

A government department issues a tender for construction services with the following eligibility criteria: a minimum annual turnover of ₹5 crore, at least 3 similar projects completed in the last 5 years, a valid GST registration, and an ISO 9001 certification. Ten bidders submit responses, each with their own combination of typed and scanned supporting documents.

A good solution would extract these four criteria from the tender, parse each bidder's submission, and produce a report. For example: 6 bidders clearly eligible with evidence for each criterion, 3 clearly ineligible with the specific criterion they failed and the document that showed it, and 1 flagged for manual review because the turnover document is a scanned certificate with figures that could not be read with confidence.

 

What Your Solution Should Cover

Round 1 of this hackathon is a written solution submission. Your solution document should make clear how you would build this platform. At minimum, it should cover:

Your understanding of the problem and the realities of government procurement, in your own words.
Your approach to extracting eligibility criteria from a tender document, including how you separate technical, financial and compliance conditions, and how you distinguish mandatory from optional criteria.
Your approach to parsing bidder submissions with heterogeneous document types — typed PDFs, scanned documents, tables, photographs — and extracting the values that map to each criterion.
How you match extracted bidder information against the criteria, and how you handle ambiguity, partial information and variation in legal and technical language.
How the system produces explainable, criterion-level verdicts, and how ambiguous cases are surfaced for human review instead of being silently rejected.
How you would guarantee the auditability of every decision, suitable for a formal government procurement context.
A clear architecture overview, the key technology and model choices you would make, and the reasons behind them.
The main risks and trade-offs you see, and how you would handle them.
A rough implementation plan for Round 2, assuming a sandbox with sample tender and bidder documents is provided.
 

How We Will Evaluate Proposals

Clarity of problem understanding — does the team show they have grasped the realities of government procurement, not just the surface problem?
Technical soundness of the proposed approach, including document understanding, criterion matching and explainability.
Depth of thinking on edge cases: scanned documents, photographs, ambiguous language, partial information and format inconsistency.
Design of the human-in-the-loop path for ambiguous cases, and of the audit trail.
Quality of the architecture, the justification of technology and model choices, and the identified risks and trade-offs.

solution : 
Title
*
CriteriaGuard - Explainable AI Platform for Government Tender Eligibility Evaluation
Description
*
Every year, procurement committees across Indian government bodies spend days manually cross-checking bidder submissions against tender eligibility criteria. A single missed condition leads to a wrongful award. A single untraceable decision invites a court challenge or RTI inquiry. When two evaluators reading the same document reach different conclusions, the entire process loses its legitimacy. This is not merely a technology gap, it is a governance gap, and it deserves a governance-grade solution.
CriteriaGuard is that solution. It is an end-to-end, explainable AI platform that takes a tender document and any number of bidder submissions and produces a fully auditable, criterion-level eligibility report in under 30 minutes ,regardless of whether documents arrive as typed PDFs, scanned certificates, Word files, or photographs of physical documents. It does not replace the procurement officer. It gives them something they have never had before: a consistent, evidence-backed, fully traceable first-pass evaluation they can actually trust and sign off on.
Why This Problem Is Harder Than It Looks
Tender documents are written in dense, legally cautious language spread across 50 to 150 pages. Eligibility criteria are rarely presented as a clean list , they are embedded in clauses, sub-clauses, and annexures, often using language like "works of similar nature and magnitude" without numerical definition. Mandatory and optional conditions are sometimes distinguished by a single word "shall" versus "should" and sometimes not distinguished at all. Bidder submissions are equally variable: one company presents turnover in an audited balance sheet, another in a CA certificate, a third in a scanned photograph with handwritten figures. A serious evaluation system must understand all three equally well, and must be honest when it cannot.


CriteriaGuard is designed around these realities, not an idealised version of the problem.

How CriteriaGuard Works
The platform operates through three tightly integrated processing stages.
Stage 1 — Tender Intelligence (CriteriaLens). CriteriaGuard reads the tender document through an LLM pipeline tuned for legal and procurement language. It extracts every eligibility criterion and structures it into a formal schema: criterion text, category (technical, financial, or compliance), mandatory or optional status, numeric threshold and reference period, and expected evidence document types. Mandatory classification is driven by linguistic markers "shall," "must," and "essential" signal mandatory requirements; "should" and "preferred" signal optional ones. Where language is genuinely ambiguous, the criterion is flagged for officer confirmation before evaluation begins. The system never assumes. The structured schema is presented to the procurement officer for approval, creating a clean checkpoint before any bidder is evaluated.

Stage 2 — Bidder Document Understanding (DocProbe). Every submission passes through a multi-format document pipeline. Typed PDFs are processed via direct text extraction with layout preservation. Scanned documents and photographs are routed through image preprocessing deskewing, contrast enhancement, noise removal before OCR using a Tesseract and cloud vision ensemble, with the higher-confidence output selected. Tables and financial data are parsed using LayoutLMv3, a model purpose-built for mixed text-and-visual document understanding. For each criterion, DocProbe locates the exact page, paragraph, and value and records the source reference. If a value cannot be found or read confidently, the system returns an explicit signal. It never invents evidence this is a hard architectural constraint, not a policy aspiration.


Stage 3 — Verdict Engine (VerdictCore). Each criterion-bidder pair is scored on four confidence factors: extraction quality, alignment between the extracted value and the criterion requirement, document authenticity signals, and numeric parseability. Where the criterion is clearly met, the bidder receives an Eligible verdict with full citation. Where it is clearly unmet, the bidder receives a Not Eligible verdict with the specific document, page, and value cited. Any case involving low confidence, a borderline numeric value, conflicting evidence, or a missing document is routed to a human review queue as Needs Officer Review, with the reason stated in plain English. Nothing is ever silently disqualified a bidder is never quietly removed from contention because a scanned certificate was partially illegible.


Explainability and the Audit Trail
Every verdict contains the criterion ID, source document name, page number, extracted value, confidence score, and a plain-English explanation of the outcome. The audit log is append-only and SHA-256 chained, making it tamper-evident and suitable for formal government record-keeping and legal scrutiny. The consolidated report exports as a signed PDF ready for officer endorsement and archival. Officer review decisions are logged with identifier and timestamp, and feed back as labelled training examples to improve future accuracy. This is not just compliance infrastructure it is the institutional memory of every procurement decision the organisation makes.


Technology Stack and Deployability
CriteriaGuard is built on a modular, cloud-native architecture deployable on NIC Cloud and MeitY-approved infrastructure. The document understanding layer uses fine-tuned open-weight LLMs (Llama 3 / Mistral) for criterion extraction and matching, with a GPT-4-class fallback for high-ambiguity cases. The backend runs on Python with FastAPI and PostgreSQL; the officer interface is built in React, optimised for document-heavy review workflows. The full stack is containerised and Kubernetes-orchestrated for horizontal scaling. All processing occurs within the organisation's infrastructure boundary data never leaves the deployment environment, which is a non-negotiable requirement for government procurement data.
The platform integrates with the GeM portal structure and requires no changes to how bidders submit documents or how officers conduct their review. It sits behind the existing process and makes it faster, more consistent, and fully traceable.


Risks and How They Are Managed
OCR failure on poor-quality scans is managed through confidence scoring uncertain extractions are routed to the review queue, never auto-decided. LLM hallucination is mitigated architecturally: every extracted value must carry a traceable source citation; if the evidence is not in the document, the system says so. Document fraud is acknowledged honestly CriteriaGuard flags internal inconsistencies and missing authenticity markers, but final verification remains a human responsibility, as it must in a formal government context.


Scalability and Long-Term Impact
The platform is domain-agnostic. Any government body issuing tenders defence, infrastructure, health, education runs the same fundamental process, and CriteriaGuard can be configured for any new domain by updating criterion extraction parameters without rebuilding the platform. As officer review decisions accumulate, accuracy improves continuously. At scale, the audit trail becomes a dataset that gives procurement policy teams visibility into how criteria are written, where ambiguity most commonly arises, and how evaluation quality varies across departments insights that have never previously been accessible.
The longer-term vision is a national procurement intelligence layer: a system that not only evaluates individual tenders but helps policy teams write clearer, fairer, and more auditable tenders in the first place.


Round 2 Implementation Plan
Week 1 delivers the tender parser, criterion schema generator, and full multi-format OCR pipeline, tested against ten synthetic tender documents across three procurement domains. Week 2 delivers the verdict engine, confidence scoring logic, and officer review queue interface. Week 3 completes the report generator, tamper-evident audit log, and an end-to-end test across ten synthetic bidder submissions including deliberately degraded scans and partial submissions. The Round 2 deliverable will be a working web prototype, a documented GitHub repository, a signed sample evaluation report, and a five-minute demonstration video covering the complete workflow from tender upload to officer-endorsed report export.




CriteriaGuard is built for the realities of Indian government procurement the document variety, the legal stakes, and the human accountability that must sit at the centre of every decision. The goal is not to automate procurement. It is to make procurement officers more consistent, more defensible, and more effective in the decisions they have always been responsible for making.