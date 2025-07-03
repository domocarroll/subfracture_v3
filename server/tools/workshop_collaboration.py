"""
SUBFRACTURE Workshop Collaboration Tools

Multi-user workshop session management and real-time collaboration
for brand intelligence workshops using FastMCP.
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
from models import WorkshopSession, WorkshopEvent, Brand
from database import DatabaseService
from metrics import (
    TOOL_EXECUTION_COUNTER, 
    TOOL_EXECUTION_DURATION, 
    WORKSHOP_SESSIONS_TOTAL,
    COLLABORATION_EVENTS_TOTAL,
    ACTIVE_SESSIONS
)

logger = structlog.get_logger()

class WorkshopCreationRequest(BaseModel):
    """Request model for creating a workshop session"""
    brand_id: str = Field(..., description="Brand to work on")
    name: str = Field(..., description="Workshop session name", min_length=1, max_length=255)
    facilitator_id: str = Field(..., description="Workshop facilitator ID")
    participants: List[str] = Field(default=[], description="Initial participant IDs")
    session_config: Dict[str, Any] = Field(default={}, description="Session configuration")
    description: Optional[str] = Field(None, description="Workshop description")

class ParticipantAction(BaseModel):
    """Participant action in workshop session"""
    session_id: str = Field(..., description="Workshop session ID")
    participant_id: str = Field(..., description="Participant ID")
    action_type: str = Field(..., description="Action type: signal_added, dimension_evolved, etc.")
    action_data: Dict[str, Any] = Field(..., description="Action data")
    context: Optional[str] = Field(None, description="Action context")

class SessionStateUpdate(BaseModel):
    """Update workshop session state"""
    session_id: str = Field(..., description="Workshop session ID")
    state_updates: Dict[str, Any] = Field(..., description="State updates to apply")
    updated_by: str = Field(..., description="User making the update")

# Tool implementation functions
async def create_workshop_session_tool(request: WorkshopCreationRequest, db_service: DatabaseService) -> Dict:
    """Create a new workshop collaboration session"""
    
    start_time = datetime.now()
    tool_name = "create_workshop_session"
    
    try:
        async with db_service.get_session() as session:
            # Verify brand exists
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
            
            # Create workshop session
            workshop = WorkshopSession(
                id=str(uuid.uuid4()),
                brand_id=request.brand_id,
                name=request.name,
                facilitator_id=request.facilitator_id,
                participants=request.participants,
                session_config={
                    **request.session_config,
                    "description": request.description,
                    "max_participants": request.session_config.get("max_participants", 10),
                    "allow_anonymous": request.session_config.get("allow_anonymous", False)
                },
                current_state={
                    "phase": "setup",
                    "active_participants": [],
                    "signals_collected": 0,
                    "dimensions_evolved": 0,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                },
                status="active"
            )
            
            session.add(workshop)
            await session.flush()
            
            # Create initial event
            initial_event = WorkshopEvent(
                id=str(uuid.uuid4()),
                session_id=workshop.id,
                participant_id=request.facilitator_id,
                event_type="session_created",
                event_data={
                    "brand_id": request.brand_id,
                    "brand_name": brand.name,
                    "initial_participants": request.participants,
                    "session_config": workshop.session_config
                },
                context="Workshop session initialized"
            )
            
            session.add(initial_event)
            await session.commit()
            
            # Update metrics
            WORKSHOP_SESSIONS_TOTAL.labels(session_type="collaborative").inc()
            ACTIVE_SESSIONS.inc()
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Workshop session created",
                session_id=workshop.id,
                brand_id=request.brand_id,
                facilitator=request.facilitator_id,
                participants=len(request.participants)
            )
            
            return {
                "success": True,
                "session_id": workshop.id,
                "workshop": {
                    "id": workshop.id,
                    "brand_id": workshop.brand_id,
                    "brand_name": brand.name,
                    "name": workshop.name,
                    "facilitator_id": workshop.facilitator_id,
                    "participants": workshop.participants,
                    "status": workshop.status,
                    "current_state": workshop.current_state,
                    "session_config": workshop.session_config,
                    "created_at": workshop.created_at.isoformat()
                },
                "initial_event_id": initial_event.id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to create workshop session", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to create workshop session: {str(e)}"
        }

async def add_participant_action_tool(action: ParticipantAction, db_service: DatabaseService) -> Dict:
    """Add participant action to workshop session"""
    
    start_time = datetime.now()
    tool_name = "add_participant_action"
    
    try:
        async with db_service.get_session() as session:
            # Get workshop session
            workshop_result = await session.execute(
                select(WorkshopSession).where(
                    WorkshopSession.id == action.session_id,
                    WorkshopSession.is_active == True
                )
            )
            workshop = workshop_result.scalar_one_or_none()
            
            if not workshop:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Workshop session {action.session_id} not found"
                }
            
            # Verify participant is part of session
            if action.participant_id not in workshop.participants and action.participant_id != workshop.facilitator_id:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Participant {action.participant_id} not authorized for session"
                }
            
            # Create event
            event = WorkshopEvent(
                id=str(uuid.uuid4()),
                session_id=action.session_id,
                participant_id=action.participant_id,
                event_type=action.action_type,
                event_data=action.action_data,
                context=action.context
            )
            
            session.add(event)
            
            # Update session state based on action type
            current_state = workshop.current_state.copy()
            
            if action.action_type == "signal_added":
                current_state["signals_collected"] = current_state.get("signals_collected", 0) + 1
            elif action.action_type == "dimension_evolved":
                current_state["dimensions_evolved"] = current_state.get("dimensions_evolved", 0) + 1
            elif action.action_type == "participant_joined":
                active_participants = current_state.get("active_participants", [])
                if action.participant_id not in active_participants:
                    active_participants.append(action.participant_id)
                current_state["active_participants"] = active_participants
            elif action.action_type == "participant_left":
                active_participants = current_state.get("active_participants", [])
                if action.participant_id in active_participants:
                    active_participants.remove(action.participant_id)
                current_state["active_participants"] = active_participants
            
            current_state["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            # Update workshop session
            workshop.current_state = current_state
            workshop.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            # Update metrics
            COLLABORATION_EVENTS_TOTAL.labels(
                event_type=action.action_type,
                participant_type="human"  # Default to human, could be enhanced
            ).inc()
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info(
                "Participant action added",
                session_id=action.session_id,
                participant_id=action.participant_id,
                action_type=action.action_type
            )
            
            return {
                "success": True,
                "event_id": event.id,
                "session_id": action.session_id,
                "participant_id": action.participant_id,
                "action_type": action.action_type,
                "updated_state": current_state,
                "timestamp": event.created_at.isoformat()
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to add participant action", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to add participant action: {str(e)}"
        }

async def get_workshop_session_tool(session_id: str, include_events: bool = False, db_service: DatabaseService = None) -> Dict:
    """Get workshop session details with optional event history"""
    
    start_time = datetime.now()
    tool_name = "get_workshop_session"
    
    try:
        async with db_service.get_session() as session:
            # Get workshop session
            workshop_result = await session.execute(
                select(WorkshopSession).where(WorkshopSession.id == session_id)
            )
            workshop = workshop_result.scalar_one_or_none()
            
            if not workshop:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
                return {
                    "success": False,
                    "error": f"Workshop session {session_id} not found"
                }
            
            # Get brand details
            brand_result = await session.execute(
                select(Brand).where(Brand.id == workshop.brand_id)
            )
            brand = brand_result.scalar_one_or_none()
            
            result_data = {
                "session_id": session_id,
                "workshop": {
                    "id": workshop.id,
                    "brand_id": workshop.brand_id,
                    "brand_name": brand.name if brand else "Unknown",
                    "name": workshop.name,
                    "facilitator_id": workshop.facilitator_id,
                    "participants": workshop.participants,
                    "status": workshop.status,
                    "current_state": workshop.current_state,
                    "session_config": workshop.session_config,
                    "created_at": workshop.created_at.isoformat(),
                    "updated_at": workshop.updated_at.isoformat(),
                    "ended_at": workshop.ended_at.isoformat() if workshop.ended_at else None
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Include events if requested
            if include_events:
                events_result = await session.execute(
                    select(WorkshopEvent)
                    .where(WorkshopEvent.session_id == session_id)
                    .order_by(WorkshopEvent.created_at.desc())
                    .limit(50)
                )
                events = events_result.scalars().all()
                
                result_data["events"] = [
                    {
                        "event_id": event.id,
                        "participant_id": event.participant_id,
                        "event_type": event.event_type,
                        "event_data": event.event_data,
                        "context": event.context,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in events
                ]
            
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="success").inc()
            
            duration = (datetime.now() - start_time).total_seconds()
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name).observe(duration)
            
            logger.info("Workshop session retrieved", session_id=session_id, include_events=include_events)
            
            return {
                "success": True,
                **result_data
            }
            
    except Exception as e:
        TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, status="error").inc()
        logger.error("Failed to get workshop session", session_id=session_id, error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get workshop session: {str(e)}"
        }

# Tool registration function
def register_tools(mcp: FastMCP, db_service: DatabaseService):
    """Register workshop collaboration tools with FastMCP server"""
    
    @mcp.tool
    def create_workshop_session(
        brand_id: str,
        name: str,
        facilitator_id: str,
        participants: List[str] = [],
        session_config: Dict[str, Any] = {},
        description: Optional[str] = None
    ) -> Dict:
        """
        Create a new workshop collaboration session
        
        Args:
            brand_id: Brand to work on
            name: Workshop session name
            facilitator_id: Workshop facilitator ID
            participants: Initial participant IDs
            session_config: Session configuration
            description: Workshop description
            
        Returns:
            Workshop session creation result
        """
        request = WorkshopCreationRequest(
            brand_id=brand_id,
            name=name,
            facilitator_id=facilitator_id,
            participants=participants,
            session_config=session_config,
            description=description
        )
        return asyncio.run(create_workshop_session_tool(request, db_service))
    
    @mcp.tool
    def add_participant_action(
        session_id: str,
        participant_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict:
        """
        Add participant action to workshop session
        
        Args:
            session_id: Workshop session ID
            participant_id: Participant ID
            action_type: Action type (signal_added, dimension_evolved, etc.)
            action_data: Action data
            context: Action context
            
        Returns:
            Action recording result
        """
        action = ParticipantAction(
            session_id=session_id,
            participant_id=participant_id,
            action_type=action_type,
            action_data=action_data,
            context=context
        )
        return asyncio.run(add_participant_action_tool(action, db_service))
    
    @mcp.tool
    def get_workshop_session(
        session_id: str,
        include_events: bool = False
    ) -> Dict:
        """
        Get workshop session details and state
        
        Args:
            session_id: Workshop session ID
            include_events: Include recent event history
            
        Returns:
            Workshop session details
        """
        return asyncio.run(get_workshop_session_tool(session_id, include_events, db_service))
    
    logger.info("Workshop collaboration tools registered successfully")