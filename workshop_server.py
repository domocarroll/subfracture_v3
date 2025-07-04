#!/usr/bin/env python3
"""
Minimal FastMCP 2.0 Workshop Facilitator Server
Focus: Workshop collaboration tools only
"""

from fastmcp import FastMCP
from typing import Dict, List, Optional
import sqlite3
import json
import time
import uuid
from datetime import datetime

# Initialize FastMCP 2.0 server
mcp = FastMCP("Workshop-Facilitator")

# Simple in-memory session storage (will upgrade to SQLite later)
workshop_sessions: Dict[str, Dict] = {}
session_events: Dict[str, List[Dict]] = {}

@mcp.tool
def create_workshop_session(
    brand: str,
    facilitator: str,
    workshop_type: str = "brand_strategy",
    max_participants: int = 10
) -> Dict:
    """
    Create a new workshop session for brand collaboration.
    
    Args:
        brand: The brand name for this workshop
        facilitator: Name of the workshop facilitator
        workshop_type: Type of workshop (brand_strategy, coherence_analysis, etc.)
        max_participants: Maximum number of participants allowed
    
    Returns:
        Dictionary with session details including session_id
    """
    session_id = str(uuid.uuid4())[:8]  # Short UUID for easy reference
    
    session_data = {
        "session_id": session_id,
        "brand": brand,
        "facilitator": facilitator,
        "workshop_type": workshop_type,
        "max_participants": max_participants,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "participants": [],
        "participant_count": 0
    }
    
    # Store session
    workshop_sessions[session_id] = session_data
    session_events[session_id] = []
    
    # Log creation event
    session_events[session_id].append({
        "event_type": "session_created",
        "timestamp": datetime.now().isoformat(),
        "actor": facilitator,
        "details": {"brand": brand, "workshop_type": workshop_type}
    })
    
    return {
        "success": True,
        "session_id": session_id,
        "session_data": session_data,
        "message": f"Workshop session '{session_id}' created for brand '{brand}'"
    }

@mcp.tool
def add_participant_action(
    session_id: str,
    participant_name: str,
    action_type: str,
    action_data: Optional[Dict] = None
) -> Dict:
    """
    Add a participant action to a workshop session.
    
    Args:
        session_id: The workshop session ID
        participant_name: Name of the participant
        action_type: Type of action (join, signal_added, dimension_evolved, etc.)
        action_data: Optional additional data for the action
    
    Returns:
        Dictionary with action result and updated session state
    """
    if session_id not in workshop_sessions:
        return {
            "success": False,
            "error": f"Session '{session_id}' not found"
        }
    
    session = workshop_sessions[session_id]
    
    # Handle participant joining
    if action_type == "join" and participant_name not in session["participants"]:
        if len(session["participants"]) >= session["max_participants"]:
            return {
                "success": False,
                "error": "Workshop session is at maximum capacity"
            }
        
        session["participants"].append(participant_name)
        session["participant_count"] = len(session["participants"])
    
    # Log the action
    event = {
        "event_type": action_type,
        "timestamp": datetime.now().isoformat(),
        "actor": participant_name,
        "details": action_data or {}
    }
    
    session_events[session_id].append(event)
    
    return {
        "success": True,
        "session_id": session_id,
        "action_logged": True,
        "current_participants": session["participants"],
        "participant_count": session["participant_count"],
        "message": f"Action '{action_type}' by '{participant_name}' logged successfully"
    }

@mcp.tool
def get_workshop_session(
    session_id: str,
    include_events: bool = False
) -> Dict:
    """
    Retrieve workshop session information.
    
    Args:
        session_id: The workshop session ID
        include_events: Whether to include event history
    
    Returns:
        Dictionary with session data and optionally event history
    """
    if session_id not in workshop_sessions:
        return {
            "success": False,
            "error": f"Session '{session_id}' not found"
        }
    
    session_data = workshop_sessions[session_id].copy()
    
    result = {
        "success": True,
        "session_data": session_data
    }
    
    if include_events:
        result["events"] = session_events.get(session_id, [])
        result["event_count"] = len(session_events.get(session_id, []))
    
    return result

@mcp.tool
def list_active_workshops() -> Dict:
    """
    List all active workshop sessions.
    
    Returns:
        Dictionary with list of active sessions
    """
    active_sessions = []
    
    for session_id, session_data in workshop_sessions.items():
        if session_data["status"] == "active":
            active_sessions.append({
                "session_id": session_id,
                "brand": session_data["brand"],
                "facilitator": session_data["facilitator"],
                "workshop_type": session_data["workshop_type"],
                "participant_count": session_data["participant_count"],
                "created_at": session_data["created_at"]
            })
    
    return {
        "success": True,
        "active_sessions": active_sessions,
        "total_count": len(active_sessions)
    }

# Health check endpoint for DigitalOcean
@mcp.custom_route("/health")
def health_check():
    """Health check endpoint for load balancer"""
    return {
        "status": "ok",
        "service": "workshop-facilitator",
        "version": "1.0.0",
        "active_sessions": len(workshop_sessions),
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint with service info
@mcp.custom_route("/")
def service_info():
    """Service information endpoint"""
    return {
        "service": "SUBFRACTURE Workshop Facilitator",
        "framework": "FastMCP 2.0",
        "mcp_endpoint": "/mcp",
        "health_check": "/health",
        "tools": [
            "create_workshop_session",
            "add_participant_action", 
            "get_workshop_session",
            "list_active_workshops"
        ],
        "active_sessions": len(workshop_sessions)
    }

if __name__ == "__main__":
    print("🎯 Starting SUBFRACTURE Workshop Facilitator...")
    print("📡 FastMCP 2.0 Server with HTTP Transport")
    print("🔗 MCP Endpoint: /mcp")
    print("💚 Health Check: /health")
    
    # Run with HTTP transport for DigitalOcean deployment
    mcp.run(
        transport="http",
        host="0.0.0.0",  # Accept external connections
        port=8080,       # DigitalOcean expected port
        path="/mcp"      # MCP protocol endpoint
    )