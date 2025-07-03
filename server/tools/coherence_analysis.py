"""
SUBFRACTURE Coherence Analysis Tools

Advanced brand coherence analysis, contradiction detection,
and gap identification using FastMCP.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import uuid
import structlog
from sqlalchemy import select, update, delete
import statistics
import math

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# Import database models and services
from models import Brand, BrandSnapshot
from database import DatabaseService
from metrics import TOOL_EXECUTION_COUNTER, TOOL_EXECUTION_DURATION

logger = structlog.get_logger()

class CoherenceAnalysisRequest(BaseModel):
    """Request model for coherence analysis"""
    brand_id: str = Field(..., description="Brand identifier")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth: basic, detailed, comprehensive")
    focus_areas: List[str] = Field(default=[], description="Specific dimensions to analyze")
    include_recommendations: bool = Field(default=True, description="Include improvement recommendations")
    threshold_settings: Dict[str, float] = Field(
        default={
            "coherence_threshold": 0.7,
            "signal_variance_threshold": 0.3,
            "contradiction_sensitivity": 0.8
        },
        description="Analysis threshold settings"
    )

class ContradictionDetectionRequest(BaseModel):
    """Request model for contradiction detection"""
    brand_id: str = Field(..., description="Brand identifier")
    dimension_pairs: Optional[List[Tuple[str, str]]] = Field(None, description="Specific dimension pairs to analyze")
    sensitivity: float = Field(default=0.8, ge=0, le=1, description="Detection sensitivity")

class GapAnalysisRequest(BaseModel):
    """Request model for gap analysis"""
    brand_id: str = Field(..., description="Brand identifier")
    target_profile: Optional[Dict[str, float]] = Field(None, description="Target brand profile for comparison")
    gap_types: List[str] = Field(default=["strength", "coherence", "coverage"], description="Types of gaps to analyze")

# Analysis implementation functions
async def analyze_brand_coherence_tool(request: CoherenceAnalysisRequest, db_service: DatabaseService) -> Dict:
    """Comprehensive brand coherence analysis"""
    
    start_time = datetime.now()
    tool_name = "analyze_brand_coherence"
    
    try:
        async with db_service.get_session() as session:
            # Get brand
            result = await session.execute(
                select(Brand).where(Brand.id == request.brand_id, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {request.brand_id} not found"
                }
            
            dimensions = brand.dimensions
            if not dimensions:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": "Brand has no dimensions to analyze"
                }
            
            # Filter dimensions if focus areas specified
            if request.focus_areas:
                dimensions = [d for d in dimensions if d.get("name") in request.focus_areas]
            
            # Basic coherence metrics
            coherence_values = [d.get("coherence", 0) for d in dimensions]
            signal_strengths = [d.get("signal_strength", 0) for d in dimensions]
            
            overall_coherence = statistics.mean(coherence_values) if coherence_values else 0
            coherence_variance = statistics.variance(coherence_values) if len(coherence_values) > 1 else 0
            signal_variance = statistics.variance(signal_strengths) if len(signal_strengths) > 1 else 0
            
            # Advanced analysis based on depth
            analysis_results = {
                "overall_coherence": round(overall_coherence, 3),
                "coherence_variance": round(coherence_variance, 3),
                "signal_variance": round(signal_variance, 3),
                "dimension_count": len(dimensions),
                "strong_dimensions": len([d for d in dimensions if d.get("coherence", 0) >= request.threshold_settings["coherence_threshold"]]),
                "weak_dimensions": len([d for d in dimensions if d.get("coherence", 0) < request.threshold_settings["coherence_threshold"]])
            }
            
            if request.analysis_depth in ["detailed", "comprehensive"]:
                # Dimension-level analysis
                dimension_analysis = []
                for dim in dimensions:
                    dim_coherence = dim.get("coherence", 0)
                    dim_strength = dim.get("signal_strength", 0)
                    
                    # Coherence-strength balance
                    balance_score = 1 - abs(dim_coherence - dim_strength)
                    
                    # Connection strength (if connections exist)
                    connections = dim.get("connections", [])
                    connection_strength = len(connections) / max(len(dimensions) - 1, 1) if len(dimensions) > 1 else 0
                    
                    dimension_analysis.append({
                        "name": dim.get("name"),
                        "coherence": dim_coherence,
                        "signal_strength": dim_strength,
                        "balance_score": round(balance_score, 3),
                        "connection_strength": round(connection_strength, 3),
                        "status": "strong" if dim_coherence >= request.threshold_settings["coherence_threshold"] else "weak",
                        "connections": connections
                    })
                
                analysis_results["dimension_analysis"] = dimension_analysis
            
            if request.analysis_depth == "comprehensive":
                # Network analysis
                total_connections = sum(len(d.get("connections", [])) for d in dimensions)
                max_possible_connections = len(dimensions) * (len(dimensions) - 1)
                network_density = total_connections / max_possible_connections if max_possible_connections > 0 else 0
                
                # Coherence distribution analysis
                coherence_distribution = {
                    "high": len([d for d in dimensions if d.get("coherence", 0) >= 0.8]),
                    "medium": len([d for d in dimensions if 0.5 <= d.get("coherence", 0) < 0.8]),
                    "low": len([d for d in dimensions if d.get("coherence", 0) < 0.5])
                }
                
                # Stability metrics (requires historical data)
                snapshots_result = await session.execute(
                    select(BrandSnapshot)
                    .where(BrandSnapshot.brand_id == request.brand_id)
                    .order_by(BrandSnapshot.created_at.desc())
                    .limit(5)
                )
                snapshots = snapshots_result.scalars().all()
                
                stability_metrics = {}
                if len(snapshots) >= 2:
                    # Calculate coherence stability over time
                    historical_coherences = []
                    for snapshot in snapshots:
                        dims = snapshot.brand_state.get("dimensions", [])
                        if dims:
                            hist_coherence = statistics.mean([d.get("coherence", 0) for d in dims])
                            historical_coherences.append(hist_coherence)
                    
                    if len(historical_coherences) >= 2:
                        coherence_trend = historical_coherences[0] - historical_coherences[-1]
                        coherence_stability = 1 - statistics.variance(historical_coherences)
                        stability_metrics = {
                            "coherence_trend": round(coherence_trend, 3),
                            "coherence_stability": round(max(coherence_stability, 0), 3),
                            "historical_snapshots": len(historical_coherences)
                        }
                
                analysis_results.update({
                    "network_density": round(network_density, 3),
                    "coherence_distribution": coherence_distribution,
                    "stability_metrics": stability_metrics
                })
            
            # Generate recommendations if requested
            recommendations = []
            if request.include_recommendations:
                if overall_coherence < request.threshold_settings["coherence_threshold"]:
                    recommendations.append({
                        "type": "coherence_improvement",
                        "priority": "high",
                        "description": "Overall brand coherence is below threshold. Focus on strengthening weak dimensions.",
                        "suggested_actions": [
                            "Review and clarify brand narrative",
                            "Strengthen value proposition articulation",
                            "Align emotional landscape with market position"
                        ]
                    })
                
                if signal_variance > request.threshold_settings["signal_variance_threshold"]:
                    recommendations.append({
                        "type": "signal_balance",
                        "priority": "medium",
                        "description": "Signal strength variance is high. Some dimensions may be over/under-emphasized.",
                        "suggested_actions": [
                            "Balance attention across all dimensions",
                            "Strengthen weak signal dimensions",
                            "Validate strong signals for sustainability"
                        ]
                    })
                
                # Dimension-specific recommendations
                if request.analysis_depth in ["detailed", "comprehensive"]:
                    weak_dims = [d for d in dimension_analysis if d["status"] == "weak"]
                    if weak_dims:
                        recommendations.append({
                            "type": "dimension_strengthening",
                            "priority": "high",
                            "description": f"Strengthen weak dimensions: {', '.join([d['name'] for d in weak_dims])}",
                            "suggested_actions": [
                                f"Develop clearer definition for {dim['name']}" for dim in weak_dims[:3]
                            ]
                        })
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Brand coherence analysis completed",
                brand_id=request.brand_id,
                overall_coherence=overall_coherence,
                analysis_depth=request.analysis_depth,
                recommendations_count=len(recommendations)
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "analysis_depth": request.analysis_depth,
                "analysis_results": analysis_results,
                "recommendations": recommendations,
                "threshold_settings": request.threshold_settings,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to analyze brand coherence", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to analyze brand coherence: {str(e)}"
        }

async def detect_contradictions_tool(request: ContradictionDetectionRequest, db_service: DatabaseService) -> Dict:
    """Detect contradictions between brand dimensions"""
    
    start_time = datetime.now()
    tool_name = "detect_contradictions"
    
    try:
        async with db_service.get_session() as session:
            # Get brand
            result = await session.execute(
                select(Brand).where(Brand.id == request.brand_id, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {request.brand_id} not found"
                }
            
            dimensions = brand.dimensions
            if len(dimensions) < 2:
                return {
                    "success": True,
                    "brand_id": request.brand_id,
                    "contradictions": [],
                    "summary": "Insufficient dimensions for contradiction analysis",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            contradictions = []
            
            # Analyze dimension pairs
            for i, dim1 in enumerate(dimensions):
                for j, dim2 in enumerate(dimensions[i+1:], i+1):
                    # Skip if specific pairs requested and this pair not included
                    if request.dimension_pairs:
                        pair_names = (dim1.get("name"), dim2.get("name"))
                        reverse_pair = (dim2.get("name"), dim1.get("name"))
                        if pair_names not in request.dimension_pairs and reverse_pair not in request.dimension_pairs:
                            continue
                    
                    # Signal strength contradiction
                    strength1 = dim1.get("signal_strength", 0)
                    strength2 = dim2.get("signal_strength", 0)
                    strength_diff = abs(strength1 - strength2)
                    
                    # Coherence contradiction
                    coherence1 = dim1.get("coherence", 0)
                    coherence2 = dim2.get("coherence", 0)
                    coherence_diff = abs(coherence1 - coherence2)
                    
                    # Check for conceptual contradictions (simplified heuristic)
                    conceptual_contradiction = False
                    contradiction_score = 0
                    
                    # High signal strength difference might indicate contradiction
                    if strength_diff > 0.5:
                        contradiction_score += 0.3
                    
                    # Large coherence difference might indicate contradiction
                    if coherence_diff > 0.4:
                        contradiction_score += 0.3
                    
                    # Check for opposite connections (if one connects to the other but not vice versa)
                    connections1 = set(dim1.get("connections", []))
                    connections2 = set(dim2.get("connections", []))
                    
                    if dim1.get("name") in connections2 and dim2.get("name") not in connections1:
                        contradiction_score += 0.2
                    elif dim2.get("name") in connections1 and dim1.get("name") not in connections2:
                        contradiction_score += 0.2
                    
                    # Conceptual contradiction heuristics (could be enhanced with AI/LLM analysis)
                    dim1_name = dim1.get("name", "").lower()
                    dim2_name = dim2.get("name", "").lower()
                    
                    # Simple keyword-based contradiction detection
                    opposing_pairs = [
                        ("traditional", "innovative"),
                        ("premium", "affordable"),
                        ("corporate", "personal"),
                        ("global", "local"),
                        ("analytical", "emotional")
                    ]
                    
                    for pair in opposing_pairs:
                        if (pair[0] in dim1_name and pair[1] in dim2_name) or (pair[1] in dim1_name and pair[0] in dim2_name):
                            contradiction_score += 0.4
                            conceptual_contradiction = True
                            break
                    
                    # Report contradiction if above sensitivity threshold
                    if contradiction_score >= request.sensitivity:
                        contradictions.append({
                            "dimension_1": {
                                "name": dim1.get("name"),
                                "signal_strength": strength1,
                                "coherence": coherence1,
                                "connections": dim1.get("connections", [])
                            },
                            "dimension_2": {
                                "name": dim2.get("name"),
                                "signal_strength": strength2,
                                "coherence": coherence2,
                                "connections": dim2.get("connections", [])
                            },
                            "contradiction_score": round(contradiction_score, 3),
                            "contradiction_type": "conceptual" if conceptual_contradiction else "metric",
                            "details": {
                                "strength_difference": round(strength_diff, 3),
                                "coherence_difference": round(coherence_diff, 3),
                                "conceptual_opposition": conceptual_contradiction
                            },
                            "severity": "high" if contradiction_score >= 0.8 else "medium" if contradiction_score >= 0.6 else "low"
                        })
            
            # Update brand contradictions if any found
            if contradictions:
                brand.contradictions = contradictions
                brand.updated_at = datetime.now(timezone.utc)
                await session.commit()
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Contradiction detection completed",
                brand_id=request.brand_id,
                contradictions_found=len(contradictions),
                sensitivity=request.sensitivity
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "contradictions": contradictions,
                "summary": {
                    "total_contradictions": len(contradictions),
                    "high_severity": len([c for c in contradictions if c["severity"] == "high"]),
                    "medium_severity": len([c for c in contradictions if c["severity"] == "medium"]),
                    "low_severity": len([c for c in contradictions if c["severity"] == "low"]),
                    "sensitivity_used": request.sensitivity
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to detect contradictions", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to detect contradictions: {str(e)}"
        }

async def identify_gaps_tool(request: GapAnalysisRequest, db_service: DatabaseService) -> Dict:
    """Identify gaps in brand development"""
    
    start_time = datetime.now()
    tool_name = "identify_gaps"
    
    try:
        async with db_service.get_session() as session:
            # Get brand
            result = await session.execute(
                select(Brand).where(Brand.id == request.brand_id, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {request.brand_id} not found"
                }
            
            dimensions = brand.dimensions
            gaps = []
            
            # Standard brand dimensions for comparison
            standard_dimensions = [
                "market_position", "value_proposition", "emotional_landscape",
                "brand_narrative", "target_audience", "competitive_differentiation",
                "visual_identity", "brand_voice", "customer_experience",
                "innovation_approach", "sustainability_position"
            ]
            
            current_dim_names = [d.get("name") for d in dimensions]
            
            # Coverage gaps
            if "coverage" in request.gap_types:
                missing_dimensions = [dim for dim in standard_dimensions if dim not in current_dim_names]
                if missing_dimensions:
                    gaps.append({
                        "gap_type": "coverage",
                        "description": "Missing standard brand dimensions",
                        "missing_elements": missing_dimensions,
                        "impact": "medium",
                        "recommendation": "Consider adding these dimensions for comprehensive brand definition"
                    })
            
            # Strength gaps
            if "strength" in request.gap_types:
                weak_dimensions = []
                for dim in dimensions:
                    strength = dim.get("signal_strength", 0)
                    if strength < 0.4:
                        weak_dimensions.append({
                            "name": dim.get("name"),
                            "current_strength": strength,
                            "target_strength": 0.7,
                            "gap_size": round(0.7 - strength, 3)
                        })
                
                if weak_dimensions:
                    gaps.append({
                        "gap_type": "strength",
                        "description": "Dimensions with low signal strength",
                        "weak_dimensions": weak_dimensions,
                        "impact": "high",
                        "recommendation": "Strengthen these dimensions through focused development efforts"
                    })
            
            # Coherence gaps
            if "coherence" in request.gap_types:
                incoherent_dimensions = []
                for dim in dimensions:
                    coherence = dim.get("coherence", 0)
                    if coherence < 0.6:
                        incoherent_dimensions.append({
                            "name": dim.get("name"),
                            "current_coherence": coherence,
                            "target_coherence": 0.8,
                            "gap_size": round(0.8 - coherence, 3)
                        })
                
                if incoherent_dimensions:
                    gaps.append({
                        "gap_type": "coherence",
                        "description": "Dimensions with low coherence",
                        "incoherent_dimensions": incoherent_dimensions,
                        "impact": "high",
                        "recommendation": "Clarify and align these dimensions for better brand coherence"
                    })
            
            # Target profile gaps (if target provided)
            if request.target_profile:
                profile_gaps = []
                for target_dim, target_value in request.target_profile.items():
                    current_dim = next((d for d in dimensions if d.get("name") == target_dim), None)
                    if current_dim:
                        current_value = current_dim.get("signal_strength", 0)
                        gap_size = target_value - current_value
                        if abs(gap_size) > 0.2:  # Significant gap
                            profile_gaps.append({
                                "dimension": target_dim,
                                "current_value": current_value,
                                "target_value": target_value,
                                "gap_size": round(gap_size, 3),
                                "direction": "strengthen" if gap_size > 0 else "reduce"
                            })
                    else:
                        profile_gaps.append({
                            "dimension": target_dim,
                            "current_value": 0,
                            "target_value": target_value,
                            "gap_size": target_value,
                            "direction": "create"
                        })
                
                if profile_gaps:
                    gaps.append({
                        "gap_type": "target_profile",
                        "description": "Gaps compared to target brand profile",
                        "profile_gaps": profile_gaps,
                        "impact": "high",
                        "recommendation": "Adjust dimensions to align with target brand profile"
                    })
            
            # Update brand gaps
            if gaps:
                brand.gaps = gaps
                brand.updated_at = datetime.now(timezone.utc)
                await session.commit()
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Gap analysis completed",
                brand_id=request.brand_id,
                gaps_found=len(gaps),
                gap_types=request.gap_types
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "gaps": gaps,
                "summary": {
                    "total_gaps": len(gaps),
                    "gap_types_analyzed": request.gap_types,
                    "high_impact_gaps": len([g for g in gaps if g.get("impact") == "high"]),
                    "medium_impact_gaps": len([g for g in gaps if g.get("impact") == "medium"])
                },
                "target_profile_used": request.target_profile is not None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to identify gaps", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to identify gaps: {str(e)}"
        }

# Tool registration function
def register_tools(mcp: FastMCP, db_service: DatabaseService):
    """Register coherence analysis tools with FastMCP server"""
    
    @mcp.tool
    def analyze_brand_coherence(
        brand_id: str,
        analysis_depth: str = "comprehensive",
        focus_areas: List[str] = [],
        include_recommendations: bool = True,
        threshold_settings: Dict[str, float] = {
            "coherence_threshold": 0.7,
            "signal_variance_threshold": 0.3,
            "contradiction_sensitivity": 0.8
        }
    ) -> Dict:
        """
        Analyze brand coherence across dimensions
        
        Args:
            brand_id: Brand identifier
            analysis_depth: Analysis depth (basic, detailed, comprehensive)
            focus_areas: Specific dimensions to analyze
            include_recommendations: Include improvement recommendations
            threshold_settings: Analysis threshold settings
            
        Returns:
            Comprehensive coherence analysis results
        """
        request = CoherenceAnalysisRequest(
            brand_id=brand_id,
            analysis_depth=analysis_depth,
            focus_areas=focus_areas,
            include_recommendations=include_recommendations,
            threshold_settings=threshold_settings
        )
        return asyncio.run(analyze_brand_coherence_tool(request, db_service))
    
    @mcp.tool
    def detect_contradictions(
        brand_id: str,
        dimension_pairs: Optional[List[Tuple[str, str]]] = None,
        sensitivity: float = 0.8
    ) -> Dict:
        """
        Detect contradictions between brand dimensions
        
        Args:
            brand_id: Brand identifier
            dimension_pairs: Specific dimension pairs to analyze
            sensitivity: Detection sensitivity (0-1)
            
        Returns:
            Contradiction detection results
        """
        request = ContradictionDetectionRequest(
            brand_id=brand_id,
            dimension_pairs=dimension_pairs,
            sensitivity=sensitivity
        )
        return asyncio.run(detect_contradictions_tool(request, db_service))
    
    @mcp.tool
    def identify_gaps(
        brand_id: str,
        target_profile: Optional[Dict[str, float]] = None,
        gap_types: List[str] = ["strength", "coherence", "coverage"]
    ) -> Dict:
        """
        Identify gaps in brand development
        
        Args:
            brand_id: Brand identifier
            target_profile: Target brand profile for comparison
            gap_types: Types of gaps to analyze
            
        Returns:
            Gap analysis results with recommendations
        """
        request = GapAnalysisRequest(
            brand_id=brand_id,
            target_profile=target_profile,
            gap_types=gap_types
        )
        return asyncio.run(identify_gaps_tool(request, db_service))
    
    logger.info("Coherence analysis tools registered successfully")