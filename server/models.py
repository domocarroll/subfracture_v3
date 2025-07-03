"""
SUBFRACTURE Database Models

SQLAlchemy models for brand intelligence data persistence
"""

from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, JSON, Text, Boolean, ForeignKey
from pydantic import BaseModel, Field, ConfigDict

# Database Models
class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

class Brand(Base):
    """Brand entity with dimensions and metadata"""
    __tablename__ = "brands"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Brand state as JSON for flexibility
    dimensions: Mapped[Dict] = mapped_column(JSON, default=dict)
    cognitive_state: Mapped[Dict] = mapped_column(JSON, default=dict) 
    contradictions: Mapped[List] = mapped_column(JSON, default=list)
    gaps: Mapped[List] = mapped_column(JSON, default=list)
    brand_metadata: Mapped[Dict] = mapped_column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Status and ownership
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String(255))

class BrandSnapshot(Base):
    """Temporal snapshots of brand state for analysis"""
    __tablename__ = "brand_snapshots"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(String, ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text)
    
    # Complete brand state at snapshot time
    brand_state: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

class WorkshopSession(Base):
    """Workshop collaboration sessions"""
    __tablename__ = "workshop_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(String, ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facilitator_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Session configuration and state
    participants: Mapped[List] = mapped_column(JSON, default=list)
    session_config: Mapped[Dict] = mapped_column(JSON, default=dict)
    current_state: Mapped[Dict] = mapped_column(JSON, default=dict)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, paused, completed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class WorkshopEvent(Base):
    """Individual events within workshop sessions"""
    __tablename__ = "workshop_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("workshop_sessions.id"), nullable=False)
    participant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # signal_added, dimension_evolved, etc.
    event_data: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Context and metadata
    context: Mapped[Optional[str]] = mapped_column(Text)
    brand_metadata: Mapped[Dict] = mapped_column("metadata", JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Pydantic models for validation and serialization
class BrandDimension(BaseModel):
    """Brand dimension with validation"""
    model_config = ConfigDict(extra='allow')
    
    name: str = Field(..., description="Dimension name")
    signal_strength: float = Field(ge=0, le=1, description="Signal strength 0-1")
    coherence: float = Field(ge=0, le=1, description="Coherence level 0-1") 
    connections: List[str] = Field(default=[], description="Connected dimensions")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BrandState(BaseModel):
    """Complete brand state model"""
    model_config = ConfigDict(extra='allow')
    
    id: str = Field(..., description="Brand ID")
    name: str = Field(..., description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    
    dimensions: List[BrandDimension] = Field(default=[], description="Brand dimensions")
    cognitive_state: Dict[str, float] = Field(
        default={"analytical": 0.5, "intuitive": 0.5, "efficiency": 0.7},
        description="AI cognitive state"
    )
    contradictions: List[Dict] = Field(default=[], description="Detected contradictions")
    gaps: List[Dict] = Field(default=[], description="Identified gaps")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkshopSignal(BaseModel):
    """Workshop signal with validation"""
    category: str = Field(..., description="Signal category/dimension")
    confidence: float = Field(ge=0, le=1, description="Signal confidence")
    source: str = Field(..., description="Signal source")
    context: Optional[str] = Field(None, description="Additional context")
    participant_id: Optional[str] = Field(None, description="Participant who provided signal")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))