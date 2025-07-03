"""
SUBFRACTURE Brand Management Tools

Core brand intelligence operations using FastMCP
Provides comprehensive brand dimension management, evolution tracking,
and coherence analysis for collaborative brand development.

Future Enhancement: These tools will be invoked by AG UI Protocol agents
for AI-native brand intelligence collaboration.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import uuid
import structlog
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# Import database models and services
from models import Brand, BrandSnapshot
from database import DatabaseService
from metrics import TOOL_EXECUTION_COUNTER, TOOL_EXECUTION_DURATION, BRANDS_TOTAL

logger = structlog.get_logger()

class BrandCreationRequest(BaseModel):
    """Request model for creating a new brand"""
    name: str = Field(..., description="Brand name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Brand description")
    owner_id: Optional[str] = Field(None, description="Brand owner identifier")
    initial_dimensions: Optional[List[Dict]] = Field(None, description="Initial brand dimensions")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class DimensionEvolutionRequest(BaseModel):
    """Request model for evolving brand dimensions"""
    brand_id: str = Field(..., description="Brand identifier")
    dimension_name: str = Field(..., description="Dimension to evolve")
    signal_strength: Optional[float] = Field(None, ge=0, le=1, description="New signal strength")
    coherence: Optional[float] = Field(None, ge=0, le=1, description="New coherence level")
    evolution_reason: str = Field(..., description="Reason for evolution")
    signals: List[Dict] = Field(default=[], description="Contributing signals")
    participant_id: Optional[str] = Field(None, description="Participant making change")

class CoherenceAnalysisRequest(BaseModel):
    """Request model for brand coherence analysis"""
    brand_id: str = Field(..., description="Brand identifier")
    analysis_depth: str = Field(default="basic", description="Analysis depth: basic, detailed, comprehensive")
    focus_areas: List[str] = Field(default=[], description="Specific areas to analyze")
    include_recommendations: bool = Field(default=True, description="Include recommendations")

# Tool implementation functions
async def create_brand_tool(request: BrandCreationRequest, db_service: DatabaseService) -> Dict:
    """Create a new brand with default or specified dimensions"""
    
    start_time = datetime.now()
    tool_name = "create_brand"
    
    try:
        async with db_service.get_session() as session:
            # Check if brand with same name exists
            existing = await session.execute(
                select(Brand).where(Brand.name == request.name, Brand.is_active == True)
            )
            if existing.scalar_one_or_none():
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand with name '{request.name}' already exists"
                }
            
            # Create default dimensions if none provided
            if not request.initial_dimensions:
                default_dimensions = [
                    {"name": "market_position", "signal_strength": 0.5, "coherence": 0.7, "connections": []},
                    {"name": "value_proposition", "signal_strength": 0.6, "coherence": 0.8, "connections": []},
                    {"name": "emotional_landscape", "signal_strength": 0.4, "coherence": 0.6, "connections": []},
                    {"name": "brand_narrative", "signal_strength": 0.7, "coherence": 0.9, "connections": []},
                    {"name": "target_audience", "signal_strength": 0.3, "coherence": 0.5, "connections": []},
                    {"name": "competitive_differentiation", "signal_strength": 0.5, "coherence": 0.6, "connections": []}
                ]
            else:
                default_dimensions = request.initial_dimensions
            
            # Create brand entity
            brand = Brand(
                id=str(uuid.uuid4()),
                name=request.name,
                description=request.description,
                dimensions=default_dimensions,
                cognitive_state={"analytical": 0.5, "intuitive": 0.5, "efficiency": 0.7},
                contradictions=[],
                gaps=[],
                brand_metadata=request.metadata,
                owner_id=request.owner_id
            )
            
            session.add(brand)
            await session.flush()  # Get the ID
            
            # Create initial snapshot
            snapshot = BrandSnapshot(
                id=str(uuid.uuid4()),
                brand_id=brand.id,
                name="Initial State",
                context="Brand creation snapshot",
                brand_state={
                    "id": brand.id,
                    "name": brand.name,
                    "description": brand.description,
                    "dimensions": brand.dimensions,
                    "cognitive_state": brand.cognitive_state,
                    "contradictions": brand.contradictions,
                    "gaps": brand.gaps,
                    "metadata": brand.brand_metadata
                },
                created_by=request.owner_id
            )
            
            session.add(snapshot)
            await session.commit()
            
            # Update metrics
            BRANDS_TOTAL.inc()
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info("Brand created", brand_id=brand.id, brand_name=brand.name)
            
            return {
                "success": True,
                "brand_id": brand.id,
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "description": brand.description,
                    "dimensions": brand.dimensions,
                    "cognitive_state": brand.cognitive_state,
                    "created_at": brand.created_at.isoformat(),
                    "metadata": brand.brand_metadata
                },
                "snapshot_id": snapshot.id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to create brand", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to create brand: {str(e)}"
        }

async def get_brand_dimensions_tool(brand_id: str, include_history: bool = False, db_service: DatabaseService = None) -> Dict:
    """Get brand dimensions with current state and optional history"""
    
    start_time = datetime.now()
    tool_name = "get_brand_dimensions"
    
    try:
        async with db_service.get_session() as session:
            # Get brand with current state
            result = await session.execute(
                select(Brand).where(Brand.id == brand_id, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {brand_id} not found"
                }
            
            # Calculate coherence metrics
            dimensions = brand.dimensions
            if dimensions:
                coherence_values = [d.get("coherence", 0) for d in dimensions]
                signal_strengths = [d.get("signal_strength", 0) for d in dimensions]
                
                overall_coherence = sum(coherence_values) / len(coherence_values) if coherence_values else 0
                signal_variance = sum((x - sum(signal_strengths)/len(signal_strengths))**2 for x in signal_strengths) / len(signal_strengths) if signal_strengths else 0
            else:
                overall_coherence = 0
                signal_variance = 0
            
            result_data = {
                "brand_id": brand_id,
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "description": brand.description,
                    "dimensions": brand.dimensions,
                    "cognitive_state": brand.cognitive_state,
                    "contradictions": brand.contradictions,
                    "gaps": brand.gaps,
                    "metadata": brand.brand_metadata,
                    "created_at": brand.created_at.isoformat(),
                    "updated_at": brand.updated_at.isoformat()
                },
                "metrics": {
                    "overall_coherence": round(overall_coherence, 3),
                    "signal_strength_variance": round(signal_variance, 3),
                    "dimension_count": len(dimensions),
                    "last_update": brand.updated_at.isoformat()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Include history if requested
            if include_history:
                snapshots_result = await session.execute(
                    select(BrandSnapshot)
                    .where(BrandSnapshot.brand_id == brand_id)
                    .order_by(BrandSnapshot.created_at.desc())
                    .limit(10)
                )
                snapshots = snapshots_result.scalars().all()
                
                result_data["history"] = [
                    {
                        "snapshot_id": snapshot.id,
                        "name": snapshot.name,
                        "context": snapshot.context,
                        "created_at": snapshot.created_at.isoformat(),
                        "created_by": snapshot.created_by
                    }
                    for snapshot in snapshots
                ]
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info("Brand dimensions retrieved", brand_id=brand_id, dimension_count=len(dimensions))
            
            return {
                "success": True,
                **result_data
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to get brand dimensions", brand_id=brand_id, error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get brand dimensions: {str(e)}"
        }

async def evolve_brand_dimension_tool(request: DimensionEvolutionRequest, db_service: DatabaseService) -> Dict:
    """Evolve a specific brand dimension based on signals and insights"""
    
    start_time = datetime.now()
    tool_name = "evolve_brand_dimension"
    
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
            
            # Find dimension to evolve
            dimensions = brand.dimensions.copy()
            dimension_index = None
            original_dimension = None
            
            for i, dim in enumerate(dimensions):
                if dim.get("name") == request.dimension_name:
                    dimension_index = i
                    original_dimension = dim.copy()
                    break
            
            if dimension_index is None:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Dimension '{request.dimension_name}' not found in brand"
                }
            
            # Apply evolution
            evolved_dimension = dimensions[dimension_index].copy()
            
            if request.signal_strength is not None:
                evolved_dimension["signal_strength"] = request.signal_strength
            
            if request.coherence is not None:
                evolved_dimension["coherence"] = request.coherence
            
            # Process contributing signals
            if request.signals:
                signal_strengths = [s.get("confidence", 0.5) for s in request.signals if s.get("confidence")]
                if signal_strengths:
                    avg_signal_strength = sum(signal_strengths) / len(signal_strengths)
                    # Blend with existing strength (70% existing, 30% new signals)
                    current_strength = evolved_dimension.get("signal_strength", 0.5)
                    evolved_dimension["signal_strength"] = (current_strength * 0.7) + (avg_signal_strength * 0.3)
                    
                    # Slightly increase coherence when signals are added
                    current_coherence = evolved_dimension.get("coherence", 0.5)
                    evolved_dimension["coherence"] = min(current_coherence + 0.05, 1.0)
            
            evolved_dimension["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Update dimensions array
            dimensions[dimension_index] = evolved_dimension
            
            # Update brand
            brand.dimensions = dimensions
            brand.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            # Calculate evolution metrics
            evolution_metrics = {
                "signal_strength_change": evolved_dimension.get("signal_strength", 0) - original_dimension.get("signal_strength", 0),
                "coherence_change": evolved_dimension.get("coherence", 0) - original_dimension.get("coherence", 0),
                "signals_processed": len(request.signals),
                "evolution_reason": request.evolution_reason
            }
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Brand dimension evolved",
                brand_id=request.brand_id,
                dimension=request.dimension_name,
                signal_change=evolution_metrics["signal_strength_change"],
                coherence_change=evolution_metrics["coherence_change"]
            )
            
            return {
                "success": True,
                "brand_id": request.brand_id,
                "dimension_name": request.dimension_name,
                "evolution": {
                    "original": original_dimension,
                    "evolved": evolved_dimension,
                    "metrics": evolution_metrics
                },
                "participant_id": request.participant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to evolve brand dimension", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to evolve brand dimension: {str(e)}"
        }

async def create_brand_snapshot_tool(brand_id: str, snapshot_name: str, context: Optional[str] = None, created_by: Optional[str] = None, db_service: DatabaseService = None) -> Dict:
    """Create a timestamped snapshot of brand state"""
    
    start_time = datetime.now()
    tool_name = "create_brand_snapshot"
    
    try:
        async with db_service.get_session() as session:
            # Get brand
            result = await session.execute(
                select(Brand).where(Brand.id == brand_id, Brand.is_active == True)
            )
            brand = result.scalar_one_or_none()
            
            if not brand:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Brand {brand_id} not found"
                }
            
            # Create snapshot
            snapshot = BrandSnapshot(
                id=str(uuid.uuid4()),
                brand_id=brand_id,
                name=snapshot_name or f"Snapshot {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                context=context,
                brand_state={
                    "id": brand.id,
                    "name": brand.name,
                    "description": brand.description,
                    "dimensions": brand.dimensions,
                    "cognitive_state": brand.cognitive_state,
                    "contradictions": brand.contradictions,
                    "gaps": brand.gaps,
                    "metadata": brand.brand_metadata,
                    "created_at": brand.created_at.isoformat(),
                    "updated_at": brand.updated_at.isoformat()
                },
                created_by=created_by
            )
            
            session.add(snapshot)
            await session.commit()
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info("Brand snapshot created", brand_id=brand_id, snapshot_id=snapshot.id)
            
            return {
                "success": True,
                "snapshot_id": snapshot.id,
                "brand_id": brand_id,
                "name": snapshot.name,
                "context": context,
                "created_at": snapshot.created_at.isoformat(),
                "created_by": created_by
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to create brand snapshot", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to create brand snapshot: {str(e)}"
        }

# Tool registration function
def register_tools(mcp: FastMCP, db_service: DatabaseService):
    """Register brand management tools with FastMCP server"""
    
    @mcp.tool
    def create_brand(
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        initial_dimensions: Optional[List[Dict]] = None,
        metadata: Dict[str, Any] = {}
    ) -> Dict:
        """
        Create a new brand with default or custom dimensions
        
        Args:
            name: Brand name (required)
            description: Brand description
            owner_id: Brand owner identifier  
            initial_dimensions: Custom initial dimensions (optional)
            metadata: Additional metadata
            
        Returns:
            Brand creation result with brand ID and initial state
        """
        request = BrandCreationRequest(
            name=name,
            description=description,
            owner_id=owner_id,
            initial_dimensions=initial_dimensions,
            metadata=metadata
        )
        return asyncio.run(create_brand_tool(request, db_service))
    
    @mcp.tool
    def get_brand_dimensions(
        brand_id: str,
        include_history: bool = False
    ) -> Dict:
        """
        Get brand dimensions with current state and metrics
        
        Args:
            brand_id: Brand identifier
            include_history: Include recent snapshots
            
        Returns:
            Complete brand state with dimensions and metrics
        """
        return asyncio.run(get_brand_dimensions_tool(brand_id, include_history, db_service))
    
    @mcp.tool
    def evolve_brand_dimension(
        brand_id: str,
        dimension_name: str,
        signal_strength: Optional[float] = None,
        coherence: Optional[float] = None,
        evolution_reason: str = "Manual evolution",
        signals: List[Dict] = [],
        participant_id: Optional[str] = None
    ) -> Dict:
        """
        Evolve a brand dimension based on signals and insights
        
        Args:
            brand_id: Brand identifier
            dimension_name: Dimension to evolve
            signal_strength: New signal strength (0-1)
            coherence: New coherence level (0-1)
            evolution_reason: Reason for evolution
            signals: Contributing signals data
            participant_id: Participant making the change
            
        Returns:
            Evolution result with before/after states
        """
        request = DimensionEvolutionRequest(
            brand_id=brand_id,
            dimension_name=dimension_name,
            signal_strength=signal_strength,
            coherence=coherence,
            evolution_reason=evolution_reason,
            signals=signals,
            participant_id=participant_id
        )
        return asyncio.run(evolve_brand_dimension_tool(request, db_service))
    
    @mcp.tool
    def create_brand_snapshot(
        brand_id: str,
        snapshot_name: str,
        context: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict:
        """
        Create a timestamped snapshot of brand state
        
        Args:
            brand_id: Brand identifier
            snapshot_name: Name for the snapshot
            context: Context or reason for snapshot
            created_by: User creating the snapshot
            
        Returns:
            Snapshot creation result
        """
        return asyncio.run(create_brand_snapshot_tool(brand_id, snapshot_name, context, created_by, db_service))
    
    logger.info("Brand management tools registered successfully")