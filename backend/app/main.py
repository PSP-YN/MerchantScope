from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .engine import MERCHANTS, get_dashboard, get_transactions, get_relationships, score_merchant

app = FastAPI(title="MerchantScope API", version="0.1.0", description="Explainable merchant behaviour risk intelligence prototype")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["*"])
CASES = {}

class CaseUpdate(BaseModel):
    status: str = Field(pattern="^(open|investigating|resolved|false_positive)$")
    note: str = Field(default="", max_length=1000)

@app.get("/health")
def health(): return {"status": "ok", "service": "merchantscope-api", "data_mode": "synthetic"}

@app.get("/api/dashboard")
def dashboard(): return get_dashboard()

@app.get("/api/merchants")
def merchants(): return get_dashboard()["merchants"]

@app.get("/api/merchants/{merchant_id}")
def merchant_detail(merchant_id: str):
    merchant = next((m for m in MERCHANTS if m["id"] == merchant_id), None)
    if not merchant: raise HTTPException(404, "Merchant not found")
    return {**merchant, **score_merchant(merchant)}

@app.get("/api/transactions")
def transactions(merchant_id: str | None = None): return get_transactions(merchant_id)

@app.get("/api/relationships")
def relationships(): return get_relationships()

@app.get("/api/cases")
def cases():
    # Open a review case for medium/high merchants once, preserving reviewer changes.
    for m in get_dashboard()["merchants"]:
        if m["risk_level"] in ("medium", "high"):
            cid = f"case-{m['id']}"
            CASES.setdefault(cid, {"id": cid, "merchant_id": m["id"], "merchant_name": m["name"],
                "risk_score": m["risk_score"], "risk_level": m["risk_level"], "status": "open",
                "signals": m["signals"], "notes": [], "created_at": get_dashboard()["generated_at"]})
    return list(CASES.values())

@app.patch("/api/cases/{case_id}")
def update_case(case_id: str, update: CaseUpdate):
    if case_id not in CASES: cases()
    if case_id not in CASES: raise HTTPException(404, "Case not found")
    CASES[case_id]["status"] = update.status
    if update.note.strip(): CASES[case_id]["notes"].append(update.note.strip())
    return CASES[case_id]
