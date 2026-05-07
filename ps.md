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