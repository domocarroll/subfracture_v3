#!/usr/bin/env python3
"""
SUBFRACTURE Production FastMCP Server

Enterprise-grade brand intelligence platform powered by FastMCP
Designed for scalability, reliability, and future AG UI Protocol integration

Architecture:
- FastMCP tools for brand intelligence operations
- SQLAlchemy for robust database persistence  
- Structured logging and monitoring
- Comprehensive error handling and recovery
- Multi-user workshop session management
- Real-time collaboration support
- Security and performance optimization

Future Enhancement: AG UI Protocol layer for AI agent collaboration
"""

import asyncio
import logging
import sys
import signal
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import uuid

# FastMCP framework
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, ConfigDict
import structlog

# Database and persistence
from database import DatabaseService
from models import Base, Brand, BrandSnapshot, WorkshopSession, WorkshopEvent, BrandDimension, BrandState, WorkshopSignal

# AG UI Protocol integration
from ag_ui_protocol import (
    FastMCPToAGUIBridge, 
    DanniAIFacilitator, 
    AGUIProtocolServer,
    BrandIntelligenceEventType
)

# Configuration and environment
from dynaconf import Dynaconf
import os
from pathlib import Path

# Monitoring and observability  
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

# Load configuration
config = Dynaconf(
    envvar_prefix="SUBFRACTURE",
    settings_files=["config/settings.toml", "config/.secrets.toml"],
    environments=True,
    load_dotenv=True,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize monitoring
if config.get("sentry_dsn"):
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        integrations=[SqlalchemyIntegration(), AsyncioIntegration()],
        traces_sample_rate=config.get("sentry_traces_sample_rate", 0.1),
        environment=config.get("environment", "development")
    )

# Import metrics from metrics module
from metrics import TOOL_EXECUTION_COUNTER, TOOL_EXECUTION_DURATION, ACTIVE_SESSIONS, BRANDS_TOTAL

# Models are imported from separate modules

# Main FastMCP Server Class
class SubfractureServer:
    """Production SUBFRACTURE FastMCP Server"""
    
    def __init__(self):
        self.mcp = FastMCP("SUBFRACTURE-Brand-Intelligence-v2")
        self.db_service = DatabaseService(
            config.get("database_url", "sqlite+aiosqlite:///subfracture.db")
        )
        self.active_sessions: Dict[str, Dict] = {}
        self.logger = structlog.get_logger()
        
        # AG UI Protocol components
        self.ag_ui_bridge = FastMCPToAGUIBridge(self.db_service)
        self.danni_facilitator = None  # Initialize after tools are registered
        self.ag_ui_server = None  # Initialize after facilitator is ready
        
    async def startup(self):
        """Server startup tasks"""
        self.logger.info("Starting SUBFRACTURE FastMCP Server")
        
        # Initialize database
        await self.db_service.init_db()
        
        # Start monitoring if enabled
        if config.get("metrics_enabled", True):
            start_http_server(config.get("metrics_port", 8000))
            self.logger.info("Metrics server started", port=config.get("metrics_port", 8000))
        
        # Register all tools
        mcp_tools = await self.register_tools()
        
        # Initialize AG UI Protocol components
        await self.setup_ag_ui_protocol(mcp_tools)
        
        self.logger.info("SUBFRACTURE FastMCP Server ready with AG UI Protocol integration")
    
    async def shutdown(self):
        """Server shutdown tasks"""
        self.logger.info("Shutting down SUBFRACTURE FastMCP Server")
        await self.db_service.close()
        self.logger.info("Database connections closed")
    
    async def register_tools(self):
        """Register all brand intelligence tools and return tool registry"""
        self.logger.info("Registering brand intelligence tools")
        
        # Import and register tool modules
        from tools import (
            brand_management,
            workshop_collaboration, 
            coherence_analysis,
            temporal_analysis,
            ai_integration
        )
        
        # Each module registers its tools with self.mcp
        brand_management.register_tools(self.mcp, self.db_service)
        workshop_collaboration.register_tools(self.mcp, self.db_service) 
        coherence_analysis.register_tools(self.mcp, self.db_service)
        temporal_analysis.register_tools(self.mcp, self.db_service)
        ai_integration.register_tools(self.mcp, self.db_service)
        
        # Build tool registry for AG UI Protocol integration
        tool_registry = await self.mcp.get_tools()
            
        self.logger.info("All tools registered successfully", tool_count=len(tool_registry))
        return tool_registry
        
    async def setup_ag_ui_protocol(self, mcp_tools: Dict):
        """Initialize AG UI Protocol components"""
        self.logger.info("Setting up AG UI Protocol integration")
        
        # Initialize Danni AI facilitator with MCP tools
        self.danni_facilitator = DanniAIFacilitator(self.ag_ui_bridge, mcp_tools)
        
        # Initialize AG UI Protocol HTTP server
        self.ag_ui_server = AGUIProtocolServer(self.ag_ui_bridge, self.danni_facilitator)
        
        self.logger.info("AG UI Protocol integration ready")

# Global server instance
server = SubfractureServer()

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal", signal=signum)
    asyncio.create_task(server.shutdown())

# Main entry point  
async def main():
    """Main server entry point"""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start server
        await server.startup()
        
        # Run FastMCP server
        await server.mcp.run_async()
        
    except Exception as e:
        logger.error("Server startup failed", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        await server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())