"""
SUBFRACTURE AG UI Protocol Integration

Bridge between FastMCP brand intelligence tools and AG UI Protocol
for AI-native collaborative brand intelligence platform.

This module implements:
- AG UI event types specific to brand intelligence
- FastMCP to AG UI Protocol bridge
- Event streaming for real-time UI updates
- AI agent framework for workshop facilitation
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, AsyncIterator, Callable, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
import structlog

from database import DatabaseService
from models import Brand, WorkshopSession, WorkshopEvent

logger = structlog.get_logger()

# AG UI Protocol Event Types for Brand Intelligence
class BrandIntelligenceEventType(str, Enum):
    # Core AG UI events
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS" 
    TOOL_CALL_END = "TOOL_CALL_END"
    STATE_DELTA = "STATE_DELTA"
    
    # Brand Intelligence specific events
    BRAND_DIMENSION_UPDATE = "BRAND_DIMENSION_UPDATE"
    WORKSHOP_SESSION_START = "WORKSHOP_SESSION_START"
    WORKSHOP_PARTICIPANT_JOIN = "WORKSHOP_PARTICIPANT_JOIN"
    BRAND_INSIGHT_GENERATED = "BRAND_INSIGHT_GENERATED"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    COHERENCE_ANALYSIS_COMPLETE = "COHERENCE_ANALYSIS_COMPLETE"
    VISUALIZATION_UPDATE = "VISUALIZATION_UPDATE"
    AI_FACILITATOR_MESSAGE = "AI_FACILITATOR_MESSAGE"
    DYNAMIC_UI_COMPONENT = "DYNAMIC_UI_COMPONENT"

@dataclass
class AGUIEvent:
    """Base AG UI Protocol event structure"""
    type: BrandIntelligenceEventType
    timestamp: str = None
    event_id: str = None
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

@dataclass
class BrandDimensionUpdateEvent(AGUIEvent):
    """Brand dimension evolution event"""
    type: BrandIntelligenceEventType = BrandIntelligenceEventType.BRAND_DIMENSION_UPDATE
    brand_id: str = ""
    dimension_name: str = ""
    old_value: Dict = None
    new_value: Dict = None
    evolution_reason: str = ""
    participant_id: Optional[str] = None

@dataclass
class WorkshopSessionStartEvent(AGUIEvent):
    """Workshop session initialization event"""
    type: BrandIntelligenceEventType = BrandIntelligenceEventType.WORKSHOP_SESSION_START
    session_id: str = ""
    brand_id: str = ""
    facilitator_type: str = "ai"  # ai, human, hybrid
    participants: List[str] = None
    session_config: Dict = None

@dataclass
class BrandInsightGeneratedEvent(AGUIEvent):
    """AI-generated brand insight event"""
    type: BrandIntelligenceEventType = BrandIntelligenceEventType.BRAND_INSIGHT_GENERATED
    brand_id: str = ""
    insight_type: str = ""
    insight_data: Dict = None
    confidence_score: float = 0.0
    source_tools: List[str] = None

@dataclass
class DynamicUIComponentEvent(AGUIEvent):
    """Dynamic UI component generation event"""
    type: BrandIntelligenceEventType = BrandIntelligenceEventType.DYNAMIC_UI_COMPONENT
    component_type: str = ""
    component_config: Dict = None
    target_container: str = ""
    lifecycle: str = "create"  # create, update, destroy

@dataclass
class AIFacilitatorMessageEvent(AGUIEvent):
    """AI facilitator natural language message"""
    type: BrandIntelligenceEventType = BrandIntelligenceEventType.AI_FACILITATOR_MESSAGE
    message: str = ""
    message_type: str = "guidance"  # guidance, question, insight, instruction
    context: Dict = None
    requires_response: bool = False

class AGUIEventEncoder:
    """Encode AG UI events for SSE streaming"""
    
    @staticmethod
    def encode(event: AGUIEvent) -> str:
        """Encode event as SSE format"""
        event_dict = asdict(event)
        return f"data: {json.dumps(event_dict)}\n\n"

class FastMCPToAGUIBridge:
    """Bridge FastMCP tool execution to AG UI Protocol events"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.event_subscribers: Dict[str, List[Callable]] = {}
        self.encoder = AGUIEventEncoder()
        self.logger = structlog.get_logger()
        
    async def subscribe_to_events(self, thread_id: str, callback: Callable):
        """Subscribe to AG UI events for a specific thread"""
        if thread_id not in self.event_subscribers:
            self.event_subscribers[thread_id] = []
        self.event_subscribers[thread_id].append(callback)
        
    async def unsubscribe_from_events(self, thread_id: str, callback: Callable):
        """Unsubscribe from AG UI events"""
        if thread_id in self.event_subscribers:
            self.event_subscribers[thread_id].remove(callback)
            
    async def emit_event(self, event: AGUIEvent):
        """Emit AG UI event to all subscribers"""
        thread_id = event.thread_id
        if thread_id and thread_id in self.event_subscribers:
            for callback in self.event_subscribers[thread_id]:
                try:
                    await callback(event)
                except Exception as e:
                    self.logger.error("Event callback failed", error=str(e), thread_id=thread_id)
    
    async def on_fastmcp_tool_start(self, tool_name: str, args: Dict, context: Dict):
        """Handle FastMCP tool execution start"""
        event = AGUIEvent(
            type=BrandIntelligenceEventType.TOOL_CALL_START,
            thread_id=context.get("thread_id"),
            run_id=context.get("run_id")
        )
        # Add tool-specific data
        event.tool_name = tool_name
        event.args = args
        
        await self.emit_event(event)
        
    async def on_fastmcp_tool_end(self, tool_name: str, result: Dict, context: Dict):
        """Handle FastMCP tool execution completion"""
        event = AGUIEvent(
            type=BrandIntelligenceEventType.TOOL_CALL_END,
            thread_id=context.get("thread_id"),
            run_id=context.get("run_id")
        )
        # Add tool result data
        event.tool_name = tool_name
        event.result = result
        
        await self.emit_event(event)
        
        # Generate specific brand intelligence events based on tool type
        await self._handle_tool_specific_events(tool_name, result, context)
        
    async def _handle_tool_specific_events(self, tool_name: str, result: Dict, context: Dict):
        """Generate brand intelligence specific events based on tool results"""
        thread_id = context.get("thread_id")
        
        if tool_name == "evolve_brand_dimension" and result.get("success"):
            # Brand dimension evolution
            event = BrandDimensionUpdateEvent(
                thread_id=thread_id,
                brand_id=result.get("brand_id"),
                dimension_name=result.get("dimension_name"),
                old_value=result.get("evolution", {}).get("original"),
                new_value=result.get("evolution", {}).get("evolved"),
                evolution_reason=result.get("evolution", {}).get("metrics", {}).get("evolution_reason"),
                participant_id=result.get("participant_id")
            )
            await self.emit_event(event)
            
        elif tool_name == "analyze_brand_coherence" and result.get("success"):
            # Coherence analysis completion
            event = AGUIEvent(
                type=BrandIntelligenceEventType.COHERENCE_ANALYSIS_COMPLETE,
                thread_id=thread_id
            )
            event.brand_id = result.get("brand_id")
            event.coherence_score = result.get("analysis", {}).get("overall_coherence", 0)
            event.contradictions = result.get("analysis", {}).get("contradictions", [])
            event.recommendations = result.get("analysis", {}).get("recommendations", [])
            
            await self.emit_event(event)
            
        elif tool_name == "start_workshop_session" and result.get("success"):
            # Workshop session start
            event = WorkshopSessionStartEvent(
                thread_id=thread_id,
                session_id=result.get("session_id"),
                brand_id=result.get("brand_id"),
                facilitator_type=result.get("facilitator_type", "ai"),
                participants=result.get("participants", []),
                session_config=result.get("session_config", {})
            )
            await self.emit_event(event)

class DanniAIFacilitator:
    """Danni AI Workshop Facilitator Agent
    
    An AI agent that uses FastMCP brand intelligence tools to facilitate
    collaborative brand development workshops via AG UI Protocol.
    """
    
    def __init__(self, bridge: FastMCPToAGUIBridge, mcp_tools: Dict):
        self.bridge = bridge
        self.mcp_tools = mcp_tools
        self.logger = structlog.get_logger()
        self.personality = {
            "name": "Danni",
            "role": "Brand Intelligence Facilitator",
            "style": "collaborative, insightful, encouraging",
            "expertise": ["brand strategy", "market positioning", "team facilitation"]
        }
        
    async def start_workshop_session(self, brand_id: str, participants: List[str], thread_id: str) -> str:
        """Start a new AI-facilitated workshop session"""
        
        # Create workshop session via FastMCP tools
        session_result = await self._call_mcp_tool("start_workshop_session", {
            "brand_id": brand_id,
            "facilitator_id": "danni-ai",
            "participants": participants,
            "session_config": {
                "facilitator_type": "ai",
                "ai_personality": self.personality,
                "workshop_type": "collaborative_exploration"
            }
        }, {"thread_id": thread_id})
        
        if not session_result.get("success"):
            raise Exception(f"Failed to start workshop: {session_result.get('error')}")
            
        session_id = session_result["session_id"]
        
        # Send welcome message
        welcome_event = AIFacilitatorMessageEvent(
            thread_id=thread_id,
            message=f"Hello everyone! I'm Danni, your AI brand intelligence facilitator. I'm excited to explore the '{session_result.get('brand_name', 'brand')}' with you today. Let's discover some amazing insights together!",
            message_type="guidance",
            context={"session_id": session_id, "phase": "introduction"}
        )
        await self.bridge.emit_event(welcome_event)
        
        # Analyze current brand state
        await self._analyze_brand_foundation(brand_id, thread_id, session_id)
        
        return session_id
        
    async def _analyze_brand_foundation(self, brand_id: str, thread_id: str, session_id: str):
        """Analyze brand foundation and provide initial insights"""
        
        # Get brand dimensions
        brand_result = await self._call_mcp_tool("get_brand_dimensions", {
            "brand_id": brand_id,
            "include_history": True
        }, {"thread_id": thread_id})
        
        if brand_result.get("success"):
            brand = brand_result["brand"]
            dimensions = brand.get("dimensions", [])
            
            # Analyze coherence
            coherence_result = await self._call_mcp_tool("analyze_brand_coherence", {
                "brand_id": brand_id,
                "analysis_depth": "comprehensive"
            }, {"thread_id": thread_id})
            
            # Generate initial insights
            insights_message = self._generate_foundation_insights(brand, coherence_result)
            
            insights_event = AIFacilitatorMessageEvent(
                thread_id=thread_id,
                message=insights_message,
                message_type="insight",
                context={
                    "session_id": session_id,
                    "phase": "foundation_analysis",
                    "brand_dimensions": len(dimensions),
                    "coherence_score": coherence_result.get("analysis", {}).get("overall_coherence", 0)
                }
            )
            await self.bridge.emit_event(insights_event)
            
            # Suggest dynamic UI components for exploration
            await self._suggest_exploration_ui(brand, thread_id, session_id)
    
    def _generate_foundation_insights(self, brand: Dict, coherence_result: Dict) -> str:
        """Generate natural language insights about brand foundation"""
        name = brand.get("name", "this brand")
        dimensions = brand.get("dimensions", [])
        coherence = coherence_result.get("analysis", {}).get("overall_coherence", 0)
        
        if coherence > 0.8:
            coherence_desc = "excellent coherence"
        elif coherence > 0.6:
            coherence_desc = "good coherence with room for refinement"
        else:
            coherence_desc = "opportunities for stronger alignment"
            
        strongest_dim = max(dimensions, key=lambda d: d.get("signal_strength", 0), default={})
        
        return f"""I've analyzed {name} and found some interesting insights:

🎯 **Brand Foundation**: You have {len(dimensions)} core dimensions with {coherence_desc} (coherence score: {coherence:.2f})

💪 **Strongest Signal**: '{strongest_dim.get('name', 'N/A')}' is showing the strongest signal strength at {strongest_dim.get('signal_strength', 0):.2f}

Let's explore how we can strengthen the connections between your brand dimensions. I'll guide us through some collaborative exercises to unlock new insights!"""

    async def _suggest_exploration_ui(self, brand: Dict, thread_id: str, session_id: str):
        """Suggest dynamic UI components for brand exploration"""
        
        # Suggest dimension exploration in Three.js scene
        threejs_ui_event = DynamicUIComponentEvent(
            thread_id=thread_id,
            component_type="brand_dimension_explorer",
            component_config={
                "type": "sphere",
                "position": [0, 2, 0],
                "scale": [1, 1, 1],
                "rotation": [0, 0, 0],
                "material": {
                    "color": "#8B5CF6",
                    "opacity": 0.7,
                    "metalness": 0.3,
                    "roughness": 0.2
                },
                "animation": {
                    "type": "rotate",
                    "speed": 0.5
                },
                "text": {
                    "content": "Brand Explorer",
                    "fontSize": 0.15,
                    "color": "#FFFFFF"
                }
            },
            target_container="three-scene",
            lifecycle="create"
        )
        await self.bridge.emit_event(threejs_ui_event)
        
        # Send brand dimensions to Three.js for dynamic visualization
        dimensions_event = BrandDimensionUpdateEvent(
            thread_id=thread_id,
            brand_id=brand["id"],
            dimension_name="all_dimensions",
            old_value={},
            new_value=brand.get("dimensions", []),
            evolution_reason="Initial brand analysis by Danni AI"
        )
        await self.bridge.emit_event(dimensions_event)
        
        # Create floating insight sphere
        insight_sphere_event = DynamicUIComponentEvent(
            thread_id=thread_id,
            component_type="insight_indicator",
            component_config={
                "type": "torus",
                "position": [3, 1, 0],
                "scale": [0.8, 0.8, 0.8],
                "rotation": [0, 0, 0],
                "material": {
                    "color": "#10B981",
                    "opacity": 0.6,
                    "metalness": 0.5,
                    "roughness": 0.1
                },
                "animation": {
                    "type": "float",
                    "speed": 2,
                    "amplitude": 0.5
                },
                "text": {
                    "content": "AI Insights",
                    "fontSize": 0.12,
                    "color": "#10B981"
                },
                "duration": 8000
            },
            target_container="three-scene",
            lifecycle="create"
        )
        await self.bridge.emit_event(insight_sphere_event)
        
    async def _call_mcp_tool(self, tool_name: str, args: Dict, context: Dict) -> Dict:
        """Call FastMCP tool and return result"""
        try:
            if tool_name in self.mcp_tools:
                tool_func = self.mcp_tools[tool_name]
                return tool_func(**args)
            else:
                self.logger.error("Tool not found", tool_name=tool_name)
                return {"success": False, "error": f"Tool {tool_name} not found"}
        except Exception as e:
            self.logger.error("Tool execution failed", tool_name=tool_name, error=str(e))
            return {"success": False, "error": str(e)}

class AGUIProtocolServer:
    """AG UI Protocol HTTP server for SUBFRACTURE brand intelligence"""
    
    def __init__(self, bridge: FastMCPToAGUIBridge, facilitator: DanniAIFacilitator):
        self.bridge = bridge
        self.facilitator = facilitator
        self.app = FastAPI(title="SUBFRACTURE AG UI Protocol Server")
        self.setup_routes()
        
    def setup_routes(self):
        """Setup AG UI Protocol HTTP routes"""
        
        @self.app.post("/ag-ui/run")
        async def run_agent(request: Request):
            """AG UI Protocol agent run endpoint"""
            body = await request.json()
            
            thread_id = body.get("threadId") or str(uuid.uuid4())
            run_id = body.get("runId") or str(uuid.uuid4())
            messages = body.get("messages", [])
            state = body.get("state", {})
            
            async def event_generator():
                # Start run
                start_event = AGUIEvent(
                    type=BrandIntelligenceEventType.RUN_STARTED,
                    thread_id=thread_id,
                    run_id=run_id
                )
                yield self.bridge.encoder.encode(start_event)
                
                # Process messages and execute brand intelligence workflow
                try:
                    async for event in self._process_brand_intelligence_workflow(
                        messages, state, thread_id, run_id
                    ):
                        yield event
                except Exception as e:
                    error_event = AGUIEvent(
                        type=BrandIntelligenceEventType.TEXT_MESSAGE_CONTENT,
                        thread_id=thread_id,
                        run_id=run_id
                    )
                    error_event.content = f"Error: {str(e)}"
                    yield self.bridge.encoder.encode(error_event)
                
                # Finish run
                finish_event = AGUIEvent(
                    type=BrandIntelligenceEventType.RUN_FINISHED,
                    thread_id=thread_id,
                    run_id=run_id
                )
                yield self.bridge.encoder.encode(finish_event)
            
            return EventSourceResponse(event_generator())
            
    async def _process_brand_intelligence_workflow(self, messages: List[Dict], state: Dict, thread_id: str, run_id: str) -> AsyncGenerator[str, None]:
        """Process brand intelligence workflow and yield AG UI events"""
        
        # Extract user intent from latest message
        latest_message = messages[-1] if messages else {}
        user_content = latest_message.get("content", "")
        
        # Brand intelligence workflow logic
        if "start workshop" in user_content.lower():
            # Extract brand ID from state or message
            brand_id = state.get("brand_id") or "default-brand"
            participants = state.get("participants", ["user"])
            
            # Start workshop via Danni facilitator
            session_id = await self.facilitator.start_workshop_session(
                brand_id, participants, thread_id
            )
            
            # Update state
            state_event = AGUIEvent(
                type=BrandIntelligenceEventType.STATE_DELTA,
                thread_id=thread_id,
                run_id=run_id
            )
            state_event.state_update = {
                "workshop_session_id": session_id,
                "workshop_active": True
            }
            yield self.bridge.encoder.encode(state_event)
            
        elif "analyze brand" in user_content.lower():
            # Brand analysis workflow
            brand_id = state.get("brand_id") or "default-brand"
            
            # Emit text message
            text_event = AGUIEvent(
                type=BrandIntelligenceEventType.TEXT_MESSAGE_CONTENT,
                thread_id=thread_id,
                run_id=run_id
            )
            text_event.content = "🔍 Analyzing brand coherence and dimensions..."
            yield self.bridge.encoder.encode(text_event)
            
            # Trigger coherence analysis
            context = {"thread_id": thread_id, "run_id": run_id}
            await self.bridge.on_fastmcp_tool_start("analyze_brand_coherence", {"brand_id": brand_id}, context)
            
            # Simulate analysis result (in real implementation, this would be actual FastMCP tool execution)
            analysis_result = {
                "success": True,
                "brand_id": brand_id,
                "analysis": {
                    "overall_coherence": 0.75,
                    "contradictions": ["value_proposition vs competitive_positioning"],
                    "recommendations": ["Strengthen emotional landscape connections"]
                }
            }
            await self.bridge.on_fastmcp_tool_end("analyze_brand_coherence", analysis_result, context)
            
        else:
            # Default response
            text_event = AGUIEvent(
                type=BrandIntelligenceEventType.TEXT_MESSAGE_CONTENT,
                thread_id=thread_id,
                run_id=run_id
            )
            text_event.content = "Hi! I'm Danni, your AI brand intelligence facilitator. Try saying 'start workshop' or 'analyze brand' to begin exploring your brand!"
            yield self.bridge.encoder.encode(text_event)