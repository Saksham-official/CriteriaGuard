from fastapi import APIRouter, HTTPException
import hashlib
import json
from typing import Any
from db.database import supabase

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/")
async def get_audit_trail():
    try:
        # Fetch audit log in chronological order
        log_res = supabase.table("audit_log").select("*").order("sequence", desc=False).execute()
        logs = log_res.data

        # Verify the chain integrity dynamically
        valid = True
        verification_results = []
        for raw_log in logs:
            log: dict[str, Any] = raw_log  # type: ignore[assignment]

            # Normalize timestamp for stable verification (YYYY-MM-DDTHH:MM:SS)
            raw_ts = str(log['timestamp'])
            stable_ts = raw_ts.replace(' ', 'T').split('.')[0].split('+')[0]
            if stable_ts.endswith('Z'):
                stable_ts = stable_ts[:-1]

            payload_stripped = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts
            }
            content_to_hash_stripped = json.dumps(payload_stripped, sort_keys=True)
            computed_hash_stripped = hashlib.sha256(content_to_hash_stripped.encode()).hexdigest()

            payload_tz = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts + "+00:00"
            }
            content_to_hash_tz = json.dumps(payload_tz, sort_keys=True)
            computed_hash_tz = hashlib.sha256(content_to_hash_tz.encode()).hexdigest()

            is_intact = (computed_hash_stripped == log['entry_hash']) or (computed_hash_tz == log['entry_hash'])
            if not is_intact:
                valid = False

            verification_results.append({
                "id": log["id"],
                "is_intact": is_intact
            })

        return {
            "is_chain_valid": valid,
            "logs": logs,
            "verification": verification_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-pdf")
async def export_audit_pdf(officer_id: str = "SYSTEM_OR_OFFICER"):
    try:
        from fastapi.responses import Response
        from jinja2 import Template
        from xhtml2pdf import pisa
        import io
        from datetime import datetime
        from services.audit import log_audit_action

        # Fetch audit log in chronological order
        log_res = supabase.table("audit_log").select("*").order("sequence", desc=False).execute()
        logs = log_res.data

        # Verify the chain integrity dynamically
        valid = True
        for raw_log in logs:
            log: dict[str, Any] = raw_log  # type: ignore[assignment]
            raw_ts = str(log['timestamp'])
            stable_ts = raw_ts.replace(' ', 'T').split('.')[0].split('+')[0]
            if stable_ts.endswith('Z'):
                stable_ts = stable_ts[:-1]

            payload_stripped = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts
            }
            content_to_hash_stripped = json.dumps(payload_stripped, sort_keys=True)
            computed_hash_stripped = hashlib.sha256(content_to_hash_stripped.encode()).hexdigest()

            payload_tz = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts + "+00:00"
            }
            content_to_hash_tz = json.dumps(payload_tz, sort_keys=True)
            computed_hash_tz = hashlib.sha256(content_to_hash_tz.encode()).hexdigest()

            is_intact = (computed_hash_stripped == log['entry_hash']) or (computed_hash_tz == log['entry_hash'])
            if not is_intact:
                valid = False
                break

        # Define Audit Log HTML Template
        audit_html_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            @page {
                size: A4;
                margin: 1.5cm;
                @frame footer {
                    -pdf-frame-content: footerContent;
                    bottom: 1cm;
                    margin-left: 1.5cm;
                    margin-right: 1.5cm;
                    height: 1cm;
                }
            }
            body { font-family: Helvetica, sans-serif; font-size: 8pt; color: #2d3748; }
            h1 { color: #1a365d; text-align: center; border-bottom: 2px solid #1a365d; padding-bottom: 8px; font-size: 16pt; margin-bottom: 20px; }
            .header { text-align: center; margin-bottom: 20px; }
            .org-name { font-size: 13pt; font-weight: bold; color: #1a365d; text-transform: uppercase; }
            .sub-org { font-size: 9pt; color: #4a5568; }
            .meta-box { background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
            .meta-grid { width: 100%; }
            .meta-grid td { border: none; padding: 3px 0; }
            table.log-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            table.log-table th, table.log-table td { border: 1px solid #cbd5e0; padding: 6px; text-align: left; }
            table.log-table th { background-color: #f7fafc; font-weight: bold; color: #1a365d; }
            .badge-valid { color: green; font-weight: bold; }
            .badge-invalid { color: red; font-weight: bold; }
            .mono { font-family: Courier, monospace; font-size: 7.5pt; color: #4a5568; }
        </style>
        </head>
        <body>

        <div class="header">
            <div class="org-name">CriteriaGuard Governance Platform</div>
            <div class="sub-org">Immutable Cryptographic Audit Ledger</div>
        </div>

        <div class="meta-box">
            <table class="meta-grid">
                <tr>
                    <td><strong>Ledger Integrity Status:</strong> <span class="{% if is_chain_valid %}badge-valid{% else %}badge-invalid{% endif %}">{% if is_chain_valid %}VERIFIED INTACT{% else %}COMPROMISED{% endif %}</span></td>
                    <td style="text-align: right;"><strong>Algorithm:</strong> SHA-256 Chained</td>
                </tr>
                <tr>
                    <td><strong>Total Blocks:</strong> {{ logs | length }}</td>
                    <td style="text-align: right;"><strong>Export Date:</strong> {{ date }}</td>
                </tr>
                <tr>
                    <td colspan="2"><strong>Generated By:</strong> CriteriaGuard Verification Engine</td>
                </tr>
            </table>
        </div>

        <h1>Audit Trail Ledger</h1>
        <p>This document presents the full chronological audit ledger of all decisions, bidder assessments, and report generation actions recorded in CriteriaGuard. Each block contains the cryptographic signature of the preceding block, ensuring perfect data immutability.</p>

        <table class="log-table">
            <thead>
                <tr>
                    <th style="width: 5%;">Seq</th>
                    <th style="width: 15%;">Timestamp</th>
                    <th style="width: 20%;">Action Type</th>
                    <th style="width: 15%;">Actor</th>
                    <th style="width: 10%;">Result</th>
                    <th style="width: 35%;">Chained Hashes</th>
                </tr>
            </thead>
            <tbody>
                {% for log in logs %}
                <tr>
                    <td>{{ log.sequence }}</td>
                    <td>{{ log.timestamp }}</td>
                    <td>{{ log.action_type }}</td>
                    <td>{{ log.actor }}</td>
                    <td>{{ log.result }}</td>
                    <td>
                        <strong>Prev Hash:</strong><br/>
                        <span class="mono">{{ log.previous_hash[:32] }}...</span><br/>
                        <strong>Entry Hash:</strong><br/>
                        <span class="mono">{{ log.entry_hash[:32] }}...</span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div id="footerContent" style="text-align:center; font-size: 8pt; color: #718096;">
            CriteriaGuard Cryptographic Audit Ledger | Page <pdf:pagenumber> of <pdf:pagecount>
        </div>

        </body>
        </html>
        """

        template = Template(audit_html_template)
        html_content = template.render(
            is_chain_valid=valid,
            logs=logs,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
        if pisa_status.err:
            raise Exception("Failed to generate PDF report")

        pdf_bytes = pdf_buffer.getvalue()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Log PDF Export into the ledger itself as a REPORT_EXPORT
        log_audit_action(
            action_type="REPORT_EXPORT",
            actor=officer_id,
            target_type="audit",
            target_id="system_ledger",
            result="success",
            metadata={"logs_count": len(logs), "pdf_hash": pdf_hash}
        )

        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="criteriaguard_audit_ledger_{datetime.now().strftime("%Y-%m-%d")}.pdf"'
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class VerifyPDFRequest(BaseModel):
    pdf_hash: str

@router.post("/verify-pdf")
async def verify_pdf_report(req: VerifyPDFRequest):
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured.")

        # 1. Fetch REPORT_EXPORT logs
        log_res = supabase.table("audit_log").select("*").eq("action_type", "REPORT_EXPORT").execute()
        logs = log_res.data
        
        match_log = None
        for log in logs:
            meta = log.get("metadata") or {}
            if meta.get("pdf_hash") == req.pdf_hash:
                match_log = log
                break
                
        if not match_log:
            return {
                "is_valid": False,
                "message": "No matching cryptographically sealed report found in the ledger. This document may have been altered, or was not generated by CriteriaGuard."
            }
            
        # 2. Re-verify the entire hash chain integrity
        all_logs_res = supabase.table("audit_log").select("*").order("sequence", desc=False).execute()
        all_logs = all_logs_res.data
        
        valid = True
        for log in all_logs:
            raw_ts = str(log['timestamp'])
            stable_ts = raw_ts.replace(' ', 'T').split('.')[0].split('+')[0]
            if stable_ts.endswith('Z'):
                stable_ts = stable_ts[:-1]

            payload_stripped = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts
            }
            content_to_hash_stripped = json.dumps(payload_stripped, sort_keys=True)
            computed_hash_stripped = hashlib.sha256(content_to_hash_stripped.encode()).hexdigest()

            payload_tz = {
                "previous_hash": str(log['previous_hash']),
                "action_type": str(log['action_type']),
                "actor": str(log['actor']),
                "target_id": str(log['target_id']),
                "result": str(log['result']),
                "timestamp": stable_ts + "+00:00"
            }
            content_to_hash_tz = json.dumps(payload_tz, sort_keys=True)
            computed_hash_tz = hashlib.sha256(content_to_hash_tz.encode()).hexdigest()

            is_intact = (computed_hash_stripped == log['entry_hash']) or (computed_hash_tz == log['entry_hash'])
            if not is_intact:
                valid = False
                break
                
        return {
            "is_valid": True,
            "is_chain_valid": valid,
            "audit_log": match_log,
            "message": "Cryptographic signature verified! The document is genuine and the ledger is secure."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
