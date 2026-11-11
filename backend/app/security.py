import os
from fastapi import Header, HTTPException

def actor_context(authorization: str | None = Header(default=None), x_actor: str = Header(default="demo-analyst"), x_role: str = Header(default="analyst")):
    env = os.getenv("APP_ENV", "demo").lower()
    if env in {"development", "demo", "test"}:
        if x_role not in {"analyst", "investigator", "admin", "reviewer"}:
            raise HTTPException(403, "Unsupported role")
        return {"actor": x_actor[:120], "role": x_role}
    tokens = {
        os.getenv("TRACE_ANALYST_TOKEN", ""): "analyst",
        os.getenv("TRACE_INVESTIGATOR_TOKEN", ""): "investigator",
        os.getenv("TRACE_ADMIN_TOKEN", ""): "admin",
    }
    token = (authorization or "").removeprefix("Bearer ").strip()
    role = tokens.get(token)
    if not token or not role or role == "":
        raise HTTPException(401, "Valid TRACE bearer token required")
    return {"actor": x_actor[:120], "role": role}

def require_role(actor: dict, allowed: set[str]):
    if actor["role"] not in allowed:
        raise HTTPException(403, "Insufficient role for this operation")
