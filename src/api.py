"""
FastAPI web interface for A/B Testing Platform
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import json
import uuid
from datetime import datetime, timedelta
import asyncio
import logging
from pathlib import Path

# Import our modules
from data_simulation import ABTestDataGenerator
from data_cleaning import ABTestCleaner
from statistical_testing import ABTestStatisticalAnalyzer
from decision_engine import ABTestDecisionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="A/B Testing Platform API",
    description="Advanced A/B Testing Experimentation Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for experiment storage
experiments_db = {}
results_cache = {}

# Pydantic models
class ExperimentConfig(BaseModel):
    name: str = Field(..., description="Experiment name")
    hypothesis: str = Field(..., description="Experiment hypothesis")
    primary_metric: str = Field(..., description="Primary metric to track")
    secondary_metrics: List[str] = Field(default=[], description="Secondary metrics")
    traffic_allocation: Dict[str, float] = Field(default={"control": 0.5, "treatment": 0.5})
    significance_level: float = Field(default=0.05, description="Statistical significance level")
    power: float = Field(default=0.80, description="Statistical power")
    min_effect_size: float = Field(default=0.05, description="Minimum detectable effect")
    sample_size: int = Field(default=1000, description="Target sample size")

class ExperimentRequest(BaseModel):
    config: ExperimentConfig
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")

class AnalysisRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    analysis_type: str = Field(default="full", description="Type of analysis to run")

class DecisionRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    guardrail_metrics: List[str] = Field(default=[], description="Guardrail metrics to check")

# Helper functions
def generate_experiment_id() -> str:
    """Generate unique experiment ID"""
    return str(uuid.uuid4())[:8]

def get_experiment_path(experiment_id: str) -> Path:
    """Get file path for experiment data"""
    return Path(f"data/experiment_{experiment_id}.csv")

def get_results_path(experiment_id: str) -> Path:
    """Get file path for experiment results"""
    return Path(f"results/experiment_{experiment_id}.json")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "A/B Testing Platform API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.post("/api/v1/experiments", response_model=Dict[str, Any])
async def create_experiment(request: ExperimentRequest):
    """Create new experiment"""
    try:
        experiment_id = generate_experiment_id()
        
        # Store experiment configuration
        experiments_db[experiment_id] = {
            "id": experiment_id,
            "config": request.config.dict(),
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created experiment {experiment_id}")
        
        return {
            "experiment_id": experiment_id,
            "status": "created",
            "config": request.config.dict(),
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/experiments", response_model=List[Dict[str, Any]])
async def list_experiments():
    """List all experiments"""
    return list(experiments_db.values())

@app.get("/api/v1/experiments/{experiment_id}", response_model=Dict[str, Any])
async def get_experiment(experiment_id: str):
    """Get experiment details"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return experiments_db[experiment_id]

@app.post("/api/v1/experiments/{experiment_id}/generate-data")
async def generate_experiment_data(
    experiment_id: str, 
    background_tasks: BackgroundTasks,
    n_users: int = 10000
):
    """Generate synthetic data for experiment"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    try:
        # Update experiment status
        experiments_db[experiment_id]["status"] = "generating_data"
        experiments_db[experiment_id]["updated_at"] = datetime.now().isoformat()
        
        # Generate data in background
        background_tasks.add_task(
            generate_data_task, 
            experiment_id, 
            n_users
        )
        
        return {
            "experiment_id": experiment_id,
            "status": "data_generation_started",
            "n_users": n_users,
            "message": "Data generation started in background"
        }
        
    except Exception as e:
        logger.error(f"Error starting data generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_data_task(experiment_id: str, n_users: int):
    """Background task for data generation"""
    try:
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        
        # Generate data
        config = experiments_db[experiment_id]["config"]
        seed = config.get("seed", 42)
        
        generator = ABTestDataGenerator(seed=seed)
        df = generator.generate_dataset(n_users)
        
        # Save data
        data_path = get_experiment_path(experiment_id)
        df.to_csv(data_path, index=False)
        
        # Update experiment status
        experiments_db[experiment_id]["status"] = "data_ready"
        experiments_db[experiment_id]["data_generated_at"] = datetime.now().isoformat()
        experiments_db[experiment_id]["data_path"] = str(data_path)
        experiments_db[experiment_id]["n_records"] = len(df)
        experiments_db[experiment_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Generated {len(df)} records for experiment {experiment_id}")
        
    except Exception as e:
        logger.error(f"Error generating data for experiment {experiment_id}: {str(e)}")
        experiments_db[experiment_id]["status"] = "data_generation_failed"
        experiments_db[experiment_id]["error"] = str(e)

@app.post("/api/v1/experiments/{experiment_id}/analyze")
async def analyze_experiment(request: AnalysisRequest):
    """Run statistical analysis on experiment data"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    try:
        # Check if data exists
        data_path = get_experiment_path(experiment_id)
        if not data_path.exists():
            raise HTTPException(status_code=400, detail="No data available for analysis")
        
        # Load data
        df = pd.read_csv(data_path)
        
        # Clean data
        cleaner = ABTestCleaner()
        cleaned_df, quality_report = cleaner.clean_data(data_path)
        
        # Run analysis
        analyzer = ABTestStatisticalAnalyzer()
        results = analyzer.run_full_analysis(cleaned_df)
        
        # Store results
        results_cache[experiment_id] = {
            "experiment_id": experiment_id,
            "analysis_type": request.analysis_type,
            "results": results,
            "quality_report": quality_report,
            "analyzed_at": datetime.now().isoformat(),
            "n_records_analyzed": len(cleaned_df)
        }
        
        # Update experiment status
        experiments_db[experiment_id]["status"] = "analyzed"
        experiments_db[experiment_id]["analyzed_at"] = datetime.now().isoformat()
        experiments_db[experiment_id]["updated_at"] = datetime.now().isoformat()
        
        return {
            "experiment_id": experiment_id,
            "analysis_type": request.analysis_type,
            "status": "completed",
            "n_records_analyzed": len(cleaned_df),
            "key_metrics": {
                "conversion_rate_lift": results["conversion"].relative_difference,
                "ctr_lift": results["ctr"].relative_difference,
                "conversion_significance": results["conversion"].is_significant,
                "ctr_significance": results["ctr"].is_significant
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing experiment {experiment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get experiment analysis results"""
    if experiment_id not in results_cache:
        raise HTTPException(status_code=404, detail="No results available for this experiment")
    
    return results_cache[experiment_id]

@app.post("/api/v1/experiments/{experiment_id}/decide")
async def make_decision(request: DecisionRequest):
    """Make automated decision based on experiment results"""
    if experiment_id not in results_cache:
        raise HTTPException(status_code=404, detail="No results available for decision making")
    
    try:
        results = results_cache[experiment_id]["results"]
        
        # Prepare guardrail results
        guardrail_results = []
        for metric in request.guardrail_metrics:
            if metric in results:
                guardrail_results.append(results[metric])
        
        # Make decision
        engine = ABTestDecisionEngine()
        recommendation = engine.make_decision(
            primary_result=results["conversion"],
            guardrail_results=guardrail_results,
            segment_results=results.get("device_segments", {})
        )
        
        # Update experiment status
        experiments_db[experiment_id]["status"] = "decision_made"
        experiments_db[experiment_id]["decision"] = recommendation
        experiments_db[experiment_id]["decided_at"] = datetime.now().isoformat()
        experiments_db[experiment_id]["updated_at"] = datetime.now().isoformat()
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error making decision for experiment {experiment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/experiments/{experiment_id}/report")
async def get_experiment_report(experiment_id: str):
    """Generate comprehensive experiment report"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if experiment_id not in results_cache:
        raise HTTPException(status_code=404, detail="No results available for report generation")
    
    try:
        experiment = experiments_db[experiment_id]
        results = results_cache[experiment_id]
        
        # Generate report
        analyzer = ABTestStatisticalAnalyzer()
        statistical_report = analyzer.generate_report(results["results"])
        
        # Generate decision report if available
        decision_report = ""
        if "decision" in experiment:
            engine = ABTestDecisionEngine()
            decision_report = engine.generate_decision_report(experiment["decision"])
        
        return {
            "experiment_id": experiment_id,
            "experiment_config": experiment["config"],
            "experiment_status": experiment["status"],
            "statistical_report": statistical_report,
            "decision_report": decision_report,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating report for experiment {experiment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/experiments/{experiment_id}/upload-data")
async def upload_experiment_data(
    experiment_id: str, 
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks
):
    """Upload experiment data from CSV file"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        
        # Save uploaded file
        data_path = get_experiment_path(experiment_id)
        
        # Process file in background
        background_tasks.add_task(
            process_uploaded_file,
            experiment_id,
            file,
            data_path
        )
        
        return {
            "experiment_id": experiment_id,
            "status": "upload_started",
            "filename": file.filename,
            "message": "File upload started in background"
        }
        
    except Exception as e:
        logger.error(f"Error uploading data for experiment {experiment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_uploaded_file(experiment_id: str, file: UploadFile, data_path: Path):
    """Background task for processing uploaded file"""
    try:
        # Read and validate file
        contents = await file.read()
        
        # Save file
        with open(data_path, 'wb') as f:
            f.write(contents)
        
        # Validate CSV structure
        df = pd.read_csv(data_path)
        
        required_columns = ['user_id', 'group', 'viewed', 'clicked', 'purchased']
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Update experiment status
        experiments_db[experiment_id]["status"] = "data_ready"
        experiments_db[experiment_id]["data_uploaded_at"] = datetime.now().isoformat()
        experiments_db[experiment_id]["data_path"] = str(data_path)
        experiments_db[experiment_id]["n_records"] = len(df)
        experiments_db[experiment_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Processed uploaded file for experiment {experiment_id}: {len(df)} records")
        
    except Exception as e:
        logger.error(f"Error processing uploaded file for experiment {experiment_id}: {str(e)}")
        experiments_db[experiment_id]["status"] = "upload_failed"
        experiments_db[experiment_id]["error"] = str(e)

@app.get("/api/v1/metrics/summary")
async def get_metrics_summary():
    """Get summary of all experiments metrics"""
    if not results_cache:
        return {"message": "No experiment results available"}
    
    summary = {
        "total_experiments": len(results_cache),
        "experiments": []
    }
    
    for exp_id, results in results_cache.items():
        exp_summary = {
            "experiment_id": exp_id,
            "analyzed_at": results["analyzed_at"],
            "n_records": results["n_records_analyzed"],
            "conversion_lift": results["results"]["conversion"].relative_difference,
            "ctr_lift": results["results"]["ctr"].relative_difference,
            "conversion_significant": results["results"]["conversion"].is_significant,
            "ctr_significant": results["results"]["ctr"].is_significant
        }
        summary["experiments"].append(exp_summary)
    
    return summary

@app.delete("/api/v1/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str):
    """Delete experiment and all associated data"""
    if experiment_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    try:
        # Delete data files
        data_path = get_experiment_path(experiment_id)
        if data_path.exists():
            data_path.unlink()
        
        # Remove from databases
        experiments_db.pop(experiment_id, None)
        results_cache.pop(experiment_id, None)
        
        return {"message": f"Experiment {experiment_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting experiment {experiment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
