"""Task 3 Meeting-to-Scope Agent Team FastAPI Application."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.analyst import AnalystAgent
from agents.feasibility import FeasibilityAgent
from agents.estimation import EstimationAgent
from agents.proposal import ProposalAgent
from agents.comparison import ScopeComparisonModule

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("task3_agents")

app = FastAPI(
    title="AI Tech Consultant - Meeting-to-Scope Agent Team",
    description="Multi-agent team converting consultation transcripts into feasible estimates and proposals.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cached_proposal: dict[str, Any] = {}


class PipelineRunRequest(BaseModel):
    transcript_text: str | None = None
    transcript_path: str | None = None
    baseline_path: str | None = None


@app.post("/pipeline/run")
async def run_meeting_pipeline(request: PipelineRunRequest | None = None):
    """Execute the 4-agent consultation pipeline + comparison module."""
    base_dir = Path(__file__).resolve().parent.parent.parent

    # Load transcript text
    transcript = ""
    if request and request.transcript_text:
        transcript = request.transcript_text
    else:
        sample_path = (
            Path(request.transcript_path)
            if request and request.transcript_path
            else base_dir / "sample-data" / "sample_transcripts" / "consultation_transcript.txt"
        )
        if sample_path.exists():
            transcript = sample_path.read_text(encoding="utf-8")
        else:
            raise HTTPException(status_code=404, detail="Consultation transcript not found")

    # 1. Analyst Agent
    analyst = AnalystAgent()
    analysis = analyst.analyze_transcript(transcript)

    # 2. Feasibility Agent
    feasibility = FeasibilityAgent()
    feat_eval = feasibility.evaluate_requirements(analysis["requirements"])

    # 3. Estimation Agent
    estimation = EstimationAgent()
    timeline = analysis["constraints"].get("timeline_weeks", 6)
    est_output = estimation.generate_estimate(feat_eval, timeline_weeks=timeline)

    # 4. Proposal Agent
    proposal_agent = ProposalAgent()
    proposal_md = proposal_agent.generate_proposal(analysis, feat_eval, est_output)

    # 5. Comparison Module against Human Baseline
    baseline_data = {}
    baseline_file = (
        Path(request.baseline_path)
        if request and request.baseline_path
        else base_dir / "sample-data" / "sample_transcripts" / "human_baseline_scope.json"
    )
    if baseline_file.exists():
        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

    comparison_module = ScopeComparisonModule()
    comparison_results = comparison_module.compare_scopes(est_output, baseline_data)
    comparison_md = comparison_module.generate_markdown_report(comparison_results)

    # Cache results
    global _cached_proposal
    _cached_proposal = {
        "client_name": analysis["client_name"],
        "analysis": analysis,
        "feasibility": feat_eval,
        "estimation": est_output,
        "proposal_markdown": proposal_md,
        "comparison_results": comparison_results,
        "comparison_markdown": comparison_md,
    }

    # Save to disk as artifacts / reports
    output_dir = Path(__file__).resolve().parent.parent / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "generated_proposal.md").write_text(proposal_md, encoding="utf-8")
    (output_dir / "comparison_report.md").write_text(comparison_md, encoding="utf-8")

    return _cached_proposal


@app.get("/proposal")
async def get_latest_proposal():
    """Retrieve the latest generated proposal."""
    if not _cached_proposal:
        return await run_meeting_pipeline(None)
    return _cached_proposal


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
