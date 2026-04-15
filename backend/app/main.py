from fastapi import FastAPI


app = FastAPI(title="HireHub API", version="0.1.0")


@app.get("/api/v1/health")

async def health_check() -> dict:
    
    return {
        
        "data": {
            
            "status": "ok",
            "db": "not_checked",
            "analysis_engine": "ready",
            
        },
        
        "error": None,
    }
