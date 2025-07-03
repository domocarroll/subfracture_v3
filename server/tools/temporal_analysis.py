"""
SUBFRACTURE Temporal Analysis Tools

Brand evolution tracking, pattern detection, and temporal insights
using FastMCP for longitudinal brand intelligence analysis.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid
import structlog
from sqlalchemy import select, update, delete, func
import statistics
import math

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# Import database models and services
from models import Brand, BrandSnapshot, WorkshopEvent
from database import DatabaseService
from metrics import TOOL_EXECUTION_COUNTER, TOOL_EXECUTION_DURATION

logger = structlog.get_logger()

class TemporalAnalysisRequest(BaseModel):
    """Request model for temporal analysis"""
    brand_id: str = Field(..., description="Brand identifier")
    time_window: str = Field(default="all", description="Time window: 7d, 30d, 90d, 1y, all")
    analysis_types: List[str] = Field(
        default=["evolution", "trends", "velocity", "stability"],
        description="Types of temporal analysis"
    )
    dimension_focus: Optional[List[str]] = Field(None, description="Specific dimensions to analyze")
    include_predictions: bool = Field(default=True, description="Include trend predictions")

class EvolutionPatternRequest(BaseModel):
    """Request model for evolution pattern detection"""
    brand_id: str = Field(..., description="Brand identifier")
    pattern_types: List[str] = Field(
        default=["growth", "decline", "oscillation", "plateau"],
        description="Pattern types to detect"
    )
    sensitivity: float = Field(default=0.6, ge=0, le=1, description="Pattern detection sensitivity")
    min_data_points: int = Field(default=3, description="Minimum data points for pattern detection")

class VelocityAnalysisRequest(BaseModel):
    """Request model for brand evolution velocity analysis"""
    brand_id: str = Field(..., description="Brand identifier")
    velocity_metrics: List[str] = Field(
        default=["coherence_velocity", "signal_velocity", "dimension_velocity"],
        description="Velocity metrics to calculate"
    )
    window_size: int = Field(default=7, description="Window size in days for velocity calculation")

# Analysis implementation functions
async def analyze_brand_evolution_tool(request: TemporalAnalysisRequest, db_service: DatabaseService) -> Dict:
    """Analyze brand evolution over time"""
    
    start_time = datetime.now()
    tool_name = "analyze_brand_evolution"
    
    try:
        async with db_service.get_session() as session:
            # Get brand
            brand_result = await session.execute(
                select(Brand).where(Brand.id == request.brand_id, Brand.is_active == True)
            )
            brand = brand_result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {request.brand_id} not found"
                }
            
            # Calculate time window
            end_time = datetime.now(timezone.utc)
            if request.time_window == "7d":
                start_time_filter = end_time - timedelta(days=7)
            elif request.time_window == "30d":
                start_time_filter = end_time - timedelta(days=30)
            elif request.time_window == "90d":
                start_time_filter = end_time - timedelta(days=90)
            elif request.time_window == "1y":
                start_time_filter = end_time - timedelta(days=365)
            else:  # "all"
                start_time_filter = datetime(1970, 1, 1, tzinfo=timezone.utc)
            
            # Get snapshots within time window
            snapshots_result = await session.execute(
                select(BrandSnapshot)
                .where(
                    BrandSnapshot.brand_id == request.brand_id,
                    BrandSnapshot.created_at >= start_time_filter
                )
                .order_by(BrandSnapshot.created_at.asc())
            )
            snapshots = snapshots_result.scalars().all()
            
            if len(snapshots) < 2:
                return {
                    "success": True,
                    "brand_id": request.brand_id,
                    "analysis_types": request.analysis_types,
                    "message": "Insufficient historical data for temporal analysis",
                    "snapshots_found": len(snapshots),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            analysis_results = {}
            
            # Evolution analysis
            if "evolution" in request.analysis_types:
                evolution_data = []
                for snapshot in snapshots:
                    brand_state = snapshot.brand_state
                    dimensions = brand_state.get("dimensions", [])
                    
                    # Filter dimensions if focus specified
                    if request.dimension_focus:
                        dimensions = [d for d in dimensions if d.get("name") in request.dimension_focus]
                    
                    if dimensions:
                        coherence_values = [d.get("coherence", 0) for d in dimensions]
                        signal_values = [d.get("signal_strength", 0) for d in dimensions]
                        
                        evolution_data.append({
                            "timestamp": snapshot.created_at.isoformat(),
                            "snapshot_id": snapshot.id,
                            "snapshot_name": snapshot.name,
                            "overall_coherence": statistics.mean(coherence_values),
                            "overall_signal_strength": statistics.mean(signal_values),
                            "dimension_count": len(dimensions),
                            "coherence_variance": statistics.variance(coherence_values) if len(coherence_values) > 1 else 0,
                            "signal_variance": statistics.variance(signal_values) if len(signal_values) > 1 else 0
                        })
                
                analysis_results["evolution"] = {
                    "data_points": evolution_data,
                    "total_snapshots": len(evolution_data),
                    "time_span_days": (snapshots[-1].created_at - snapshots[0].created_at).days,
                    "earliest_snapshot": snapshots[0].created_at.isoformat(),
                    "latest_snapshot": snapshots[-1].created_at.isoformat()
                }
            
            # Trend analysis
            if "trends" in request.analysis_types:
                if len(snapshots) >= 3:
                    coherence_trend = []
                    signal_trend = []
                    
                    for snapshot in snapshots:
                        dimensions = snapshot.brand_state.get("dimensions", [])
                        if request.dimension_focus:
                            dimensions = [d for d in dimensions if d.get("name") in request.dimension_focus]
                        
                        if dimensions:
                            coherence_trend.append(statistics.mean([d.get("coherence", 0) for d in dimensions]))
                            signal_trend.append(statistics.mean([d.get("signal_strength", 0) for d in dimensions]))
                    
                    # Calculate trend direction and strength
                    def calculate_trend(values):
                        if len(values) < 2:
                            return {"direction": "insufficient_data", "strength": 0, "slope": 0}
                        
                        x = list(range(len(values)))
                        n = len(values)
                        sum_x = sum(x)
                        sum_y = sum(values)
                        sum_xy = sum(x[i] * values[i] for i in range(n))
                        sum_x2 = sum(xi ** 2 for xi in x)
                        
                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
                        
                        direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
                        strength = abs(slope)
                        
                        return {"direction": direction, "strength": round(strength, 4), "slope": round(slope, 4)}
                    
                    analysis_results["trends"] = {
                        "coherence_trend": calculate_trend(coherence_trend),
                        "signal_strength_trend": calculate_trend(signal_trend),
                        "trend_period": f"{len(snapshots)} snapshots over {(snapshots[-1].created_at - snapshots[0].created_at).days} days"
                    }
            
            # Velocity analysis
            if "velocity" in request.analysis_types:
                velocity_data = []
                
                for i in range(1, len(snapshots)):
                    prev_snapshot = snapshots[i-1]
                    curr_snapshot = snapshots[i]
                    
                    time_diff = (curr_snapshot.created_at - prev_snapshot.created_at).total_seconds() / 86400  # days
                    
                    prev_dims = prev_snapshot.brand_state.get("dimensions", [])
                    curr_dims = curr_snapshot.brand_state.get("dimensions", [])
                    
                    if request.dimension_focus:
                        prev_dims = [d for d in prev_dims if d.get("name") in request.dimension_focus]
                        curr_dims = [d for d in curr_dims if d.get("name") in request.dimension_focus]
                    
                    if prev_dims and curr_dims and time_diff > 0:
                        prev_coherence = statistics.mean([d.get("coherence", 0) for d in prev_dims])
                        curr_coherence = statistics.mean([d.get("coherence", 0) for d in curr_dims])
                        coherence_velocity = (curr_coherence - prev_coherence) / time_diff
                        
                        prev_signal = statistics.mean([d.get("signal_strength", 0) for d in prev_dims])
                        curr_signal = statistics.mean([d.get("signal_strength", 0) for d in curr_dims])
                        signal_velocity = (curr_signal - prev_signal) / time_diff
                        
                        velocity_data.append({
                            "period_start": prev_snapshot.created_at.isoformat(),
                            "period_end": curr_snapshot.created_at.isoformat(),
                            "time_diff_days": round(time_diff, 2),
                            "coherence_velocity": round(coherence_velocity, 4),
                            "signal_velocity": round(signal_velocity, 4),
                            "magnitude": round(math.sqrt(coherence_velocity**2 + signal_velocity**2), 4)
                        })
                
                avg_velocity = {
                    "coherence": statistics.mean([v["coherence_velocity"] for v in velocity_data]) if velocity_data else 0,
                    "signal": statistics.mean([v["signal_velocity"] for v in velocity_data]) if velocity_data else 0
                }
                
                analysis_results["velocity"] = {
                    "period_velocities": velocity_data,
                    "average_velocity": avg_velocity,
                    "total_periods": len(velocity_data)
                }
            
            # Stability analysis
            if "stability" in request.analysis_types:
                if len(snapshots) >= 3:
                    coherence_values = []
                    signal_values = []
                    
                    for snapshot in snapshots:
                        dimensions = snapshot.brand_state.get("dimensions", [])
                        if request.dimension_focus:
                            dimensions = [d for d in dimensions if d.get("name") in request.dimension_focus]
                        
                        if dimensions:
                            coherence_values.append(statistics.mean([d.get("coherence", 0) for d in dimensions]))
                            signal_values.append(statistics.mean([d.get("signal_strength", 0) for d in dimensions]))
                    
                    stability_metrics = {}
                    if coherence_values:
                        coherence_variance = statistics.variance(coherence_values)
                        coherence_stability = max(0, 1 - coherence_variance)
                        stability_metrics["coherence_stability"] = round(coherence_stability, 3)
                        stability_metrics["coherence_variance"] = round(coherence_variance, 3)
                    
                    if signal_values:
                        signal_variance = statistics.variance(signal_values)
                        signal_stability = max(0, 1 - signal_variance)
                        stability_metrics["signal_stability"] = round(signal_stability, 3)
                        stability_metrics["signal_variance"] = round(signal_variance, 3)
                    
                    # Overall stability score
                    if "coherence_stability" in stability_metrics and "signal_stability" in stability_metrics:
                        overall_stability = (stability_metrics["coherence_stability"] + stability_metrics["signal_stability"]) / 2
                        stability_metrics["overall_stability"] = round(overall_stability, 3)
                    
                    analysis_results["stability"] = stability_metrics
            
            # Predictions (simple trend extrapolation)
            predictions = {}
            if request.include_predictions and "trends" in analysis_results:
                trend_data = analysis_results["trends"]
                
                # 30-day predictions based on current trends
                if trend_data["coherence_trend"]["direction"] != "insufficient_data":
                    coherence_slope = trend_data["coherence_trend"]["slope"]
                    current_coherence = evolution_data[-1]["overall_coherence"] if evolution_data else 0.5
                    predicted_coherence = current_coherence + (coherence_slope * 30)  # 30 days ahead
                    predictions["coherence_30d"] = round(max(0, min(1, predicted_coherence)), 3)
                
                if trend_data["signal_strength_trend"]["direction"] != "insufficient_data":
                    signal_slope = trend_data["signal_strength_trend"]["slope"]
                    current_signal = evolution_data[-1]["overall_signal_strength"] if evolution_data else 0.5
                    predicted_signal = current_signal + (signal_slope * 30)
                    predictions["signal_strength_30d"] = round(max(0, min(1, predicted_signal)), 3)
                
                analysis_results["predictions"] = predictions
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Brand evolution analysis completed",
                brand_id=request.brand_id,
                time_window=request.time_window,
                snapshots_analyzed=len(snapshots),
                analysis_types=request.analysis_types
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "time_window": request.time_window,
                "analysis_types": request.analysis_types,
                "dimension_focus": request.dimension_focus,
                "analysis_results": analysis_results,
                "snapshots_analyzed": len(snapshots),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to analyze brand evolution", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to analyze brand evolution: {str(e)}"
        }

async def detect_evolution_patterns_tool(request: EvolutionPatternRequest, db_service: DatabaseService) -> Dict:
    """Detect patterns in brand evolution"""
    
    start_time = datetime.now()
    tool_name = "detect_evolution_patterns"
    
    try:
        async with db_service.get_session() as session:
            # Get brand snapshots
            snapshots_result = await session.execute(
                select(BrandSnapshot)
                .where(BrandSnapshot.brand_id == request.brand_id)
                .order_by(BrandSnapshot.created_at.asc())
            )
            snapshots = snapshots_result.scalars().all()
            
            if len(snapshots) < request.min_data_points:
                return {
                    "success": True,
                    "brand_id": request.brand_id,
                    "patterns": [],
                    "message": f"Insufficient data points for pattern detection (need {request.min_data_points}, found {len(snapshots)})",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Extract time series data
            time_series = []
            for snapshot in snapshots:
                dimensions = snapshot.brand_state.get("dimensions", [])
                if dimensions:
                    coherence = statistics.mean([d.get("coherence", 0) for d in dimensions])
                    signal_strength = statistics.mean([d.get("signal_strength", 0) for d in dimensions])
                    
                    time_series.append({
                        "timestamp": snapshot.created_at,
                        "coherence": coherence,
                        "signal_strength": signal_strength,
                        "snapshot_id": snapshot.id
                    })
            
            patterns = []
            
            def detect_pattern_in_series(values, pattern_type, threshold=0.1):
                """Detect specific pattern in time series"""
                if len(values) < 3:
                    return None
                
                # Calculate first and second derivatives (simplified)
                first_diff = [values[i+1] - values[i] for i in range(len(values)-1)]
                second_diff = [first_diff[i+1] - first_diff[i] for i in range(len(first_diff)-1)]
                
                if pattern_type == "growth":
                    # Sustained positive trend
                    positive_changes = sum(1 for x in first_diff if x > threshold)
                    if positive_changes >= len(first_diff) * 0.7:
                        strength = positive_changes / len(first_diff)
                        return {
                            "type": "growth",
                            "strength": round(strength, 3),
                            "confidence": round(strength * request.sensitivity, 3),
                            "total_change": round(values[-1] - values[0], 3)
                        }
                
                elif pattern_type == "decline":
                    # Sustained negative trend
                    negative_changes = sum(1 for x in first_diff if x < -threshold)
                    if negative_changes >= len(first_diff) * 0.7:
                        strength = negative_changes / len(first_diff)
                        return {
                            "type": "decline",
                            "strength": round(strength, 3),
                            "confidence": round(strength * request.sensitivity, 3),
                            "total_change": round(values[-1] - values[0], 3)
                        }
                
                elif pattern_type == "oscillation":
                    # Regular ups and downs
                    sign_changes = sum(1 for i in range(len(first_diff)-1) if first_diff[i] * first_diff[i+1] < 0)
                    if sign_changes >= len(first_diff) * 0.5:
                        strength = sign_changes / max(len(first_diff) - 1, 1)
                        amplitude = statistics.stdev(values) if len(values) > 1 else 0
                        return {
                            "type": "oscillation",
                            "strength": round(strength, 3),
                            "confidence": round(strength * request.sensitivity, 3),
                            "amplitude": round(amplitude, 3),
                            "frequency": round(sign_changes / len(values), 3)
                        }
                
                elif pattern_type == "plateau":
                    # Stable values with minimal change
                    variance = statistics.variance(values) if len(values) > 1 else 0
                    if variance < threshold:
                        stability = 1 - variance
                        return {
                            "type": "plateau",
                            "strength": round(stability, 3),
                            "confidence": round(stability * request.sensitivity, 3),
                            "variance": round(variance, 3),
                            "duration_snapshots": len(values)
                        }
                
                return None
            
            # Detect patterns in coherence
            coherence_values = [ts["coherence"] for ts in time_series]
            for pattern_type in request.pattern_types:
                pattern = detect_pattern_in_series(coherence_values, pattern_type)
                if pattern and pattern["confidence"] >= request.sensitivity:
                    patterns.append({
                        **pattern,
                        "metric": "coherence",
                        "time_period": {
                            "start": time_series[0]["timestamp"].isoformat(),
                            "end": time_series[-1]["timestamp"].isoformat(),
                            "duration_days": (time_series[-1]["timestamp"] - time_series[0]["timestamp"]).days
                        }
                    })
            
            # Detect patterns in signal strength
            signal_values = [ts["signal_strength"] for ts in time_series]
            for pattern_type in request.pattern_types:
                pattern = detect_pattern_in_series(signal_values, pattern_type)
                if pattern and pattern["confidence"] >= request.sensitivity:
                    patterns.append({
                        **pattern,
                        "metric": "signal_strength",
                        "time_period": {
                            "start": time_series[0]["timestamp"].isoformat(),
                            "end": time_series[-1]["timestamp"].isoformat(),
                            "duration_days": (time_series[-1]["timestamp"] - time_series[0]["timestamp"]).days
                        }
                    })
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Evolution patterns detected",
                brand_id=request.brand_id,
                patterns_found=len(patterns),
                data_points=len(time_series)
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "patterns": patterns,
                "detection_settings": {
                    "pattern_types": request.pattern_types,
                    "sensitivity": request.sensitivity,
                    "min_data_points": request.min_data_points
                },
                "data_points_analyzed": len(time_series),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to detect evolution patterns", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to detect evolution patterns: {str(e)}"
        }

# Tool registration function
def register_tools(mcp: FastMCP, db_service: DatabaseService):
    """Register temporal analysis tools with FastMCP server"""
    
    @mcp.tool
    def analyze_brand_evolution(
        brand_id: str,
        time_window: str = "all",
        analysis_types: List[str] = ["evolution", "trends", "velocity", "stability"],
        dimension_focus: Optional[List[str]] = None,
        include_predictions: bool = True
    ) -> Dict:
        """
        Analyze brand evolution over time
        
        Args:
            brand_id: Brand identifier
            time_window: Time window (7d, 30d, 90d, 1y, all)
            analysis_types: Types of analysis to perform
            dimension_focus: Specific dimensions to analyze
            include_predictions: Include trend predictions
            
        Returns:
            Comprehensive temporal analysis results
        """
        request = TemporalAnalysisRequest(
            brand_id=brand_id,
            time_window=time_window,
            analysis_types=analysis_types,
            dimension_focus=dimension_focus,
            include_predictions=include_predictions
        )
        return asyncio.run(analyze_brand_evolution_tool(request, db_service))
    
    @mcp.tool
    def detect_evolution_patterns(
        brand_id: str,
        pattern_types: List[str] = ["growth", "decline", "oscillation", "plateau"],
        sensitivity: float = 0.6,
        min_data_points: int = 3
    ) -> Dict:
        """
        Detect patterns in brand evolution
        
        Args:
            brand_id: Brand identifier
            pattern_types: Pattern types to detect
            sensitivity: Detection sensitivity (0-1)
            min_data_points: Minimum data points required
            
        Returns:
            Detected evolution patterns
        """
        request = EvolutionPatternRequest(
            brand_id=brand_id,
            pattern_types=pattern_types,
            sensitivity=sensitivity,
            min_data_points=min_data_points
        )
        return asyncio.run(detect_evolution_patterns_tool(request, db_service))
    
    logger.info("Temporal analysis tools registered successfully")