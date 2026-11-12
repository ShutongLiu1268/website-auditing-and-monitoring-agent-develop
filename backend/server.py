"""FastAPI server for Dell PDP Audit & Comparison Tool"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Dell PDP Audit & Comparison API")

# Enable CORS for the web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRIPT_DIR = Path(__file__).parent


class AuditRequest(BaseModel):
    url: str
    audit_type: str = "R2"
    region: str = "US"


class ComparisonRequest(BaseModel):
    url1: str
    url2: str


@app.get("/")
async def root():
    """Serve the web interface"""
    return FileResponse(SCRIPT_DIR / "pdp-tool.html")


@app.post("/api/audit")
async def run_audit(request: AuditRequest):
    """Run audit on a single PDP URL"""
    try:
        # Run the unified tool in audit mode
        cmd = [
            "python",
            str(SCRIPT_DIR / "unified_tool.py"),
            "audit",
            request.url,
            request.audit_type,
            request.region,
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(SCRIPT_DIR),
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Audit failed: {stderr.decode()}"
            )
        
        # Read the generated report
        report_file = SCRIPT_DIR / "audit_report.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            return report
        else:
            raise HTTPException(
                status_code=500,
                detail="Audit report not generated"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
async def run_comparison(request: ComparisonRequest):
    """Run comparison between two PDP URLs"""
    try:
        # Run the unified tool in comparison mode
        cmd = [
            "python",
            str(SCRIPT_DIR / "unified_tool.py"),
            "compare",
            request.url1,
            request.url2,
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(SCRIPT_DIR),
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Comparison failed: {stderr.decode()}"
            )
        
        # Read the generated report
        report_file = SCRIPT_DIR / "comparison_report.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            return report
        else:
            raise HTTPException(
                status_code=500,
                detail="Comparison report not generated"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{filename}")
async def get_file(filename: str):
    """Download generated files"""
    file_path = SCRIPT_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
