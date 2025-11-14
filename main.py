import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from database import create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ------------------- paired signup logic -------------------
IVY_LEAGUE_DOMAINS = {
    "harvard.edu",
    "college.harvard.edu",
    "mit.edu",  # not ivy but often requested; remove if strict
    "yale.edu",
    "princeton.edu",
    "columbia.edu",
    "brown.edu",
    "dartmouth.edu",
    "upenn.edu",
    "wharton.upenn.edu",
    "cornell.edu",
}

ivy_pattern = re.compile(r"^[^@]+@([^@]+)$")

class SignupPayload(BaseModel):
    email: EmailStr
    source: str | None = None

@app.post("/api/signup")
def signup(payload: SignupPayload):
    match = ivy_pattern.match(payload.email)
    domain = match.group(1).lower() if match else ""

    # allow subdomains of ivy league domains as well
    def is_ivy(domain: str) -> bool:
        return any(domain == d or domain.endswith("." + d) for d in IVY_LEAGUE_DOMAINS)

    if not is_ivy(domain):
        raise HTTPException(status_code=400, detail="email domain not eligible")

    try:
        doc_id = create_document("signup", payload.model_dump())
        return {"ok": True, "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
