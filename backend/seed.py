from app.db import Base, engine, SessionLocal
from app.generator import seed_demo
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try: print(seed_demo(db,force=True))
finally: db.close()
