#!/usr/bin/env python3
"""Reproducible TRACE synthetic benchmark runner."""
from __future__ import annotations
import json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
from dotenv import load_dotenv
load_dotenv(ROOT/"backend"/".env")
from app.db import Base,engine,SessionLocal
from app.generator import seed_demo
from app.evaluation import evaluate_models

def main():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        seed_demo(db)
        report=evaluate_models(db)
        output=ROOT/"evaluation"/"reports"
        output.mkdir(parents=True,exist_ok=True)
        target=output/"latest-benchmark.json"
        target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(report,indent=2))
        print(f"\nSaved report: {target.relative_to(ROOT)}")
    finally:
        db.close()

if __name__=="__main__":
    main()
