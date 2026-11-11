from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
from app.db import SessionLocal
from app.evaluation import evaluate_models

db=SessionLocal()
try:
    result=evaluate_models(db)
    print(json.dumps(result,indent=2))
    Path(__file__).with_name("latest-results.json").write_text(json.dumps(result,indent=2))
finally:
    db.close()
