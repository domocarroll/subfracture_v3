"""
SUBFRACTURE Metrics and Monitoring

Prometheus metrics for monitoring FastMCP server performance
and brand intelligence operations.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# Tool execution metrics
TOOL_EXECUTION_COUNTER = Counter(
    'subfracture_tool_executions_total', 
    'Total tool executions', 
    ['tool_name', 'status']
)

TOOL_EXECUTION_DURATION = Histogram(
    'subfracture_tool_execution_duration_seconds', 
    'Tool execution duration in seconds', 
    ['tool_name'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# System metrics
ACTIVE_SESSIONS = Gauge(
    'subfracture_active_sessions', 
    'Number of active workshop sessions'
)

BRANDS_TOTAL = Gauge(
    'subfracture_brands_total', 
    'Total number of brands in system'
)

CONCURRENT_USERS = Gauge(
    'subfracture_concurrent_users',
    'Number of concurrent users'
)

DATABASE_CONNECTIONS = Gauge(
    'subfracture_database_connections',
    'Number of active database connections'
)

# Business metrics
WORKSHOP_SESSIONS_TOTAL = Counter(
    'subfracture_workshop_sessions_total',
    'Total number of workshop sessions created',
    ['session_type']
)

DIMENSION_EVOLUTIONS_TOTAL = Counter(
    'subfracture_dimension_evolutions_total',
    'Total number of dimension evolutions',
    ['dimension_name', 'evolution_type']
)

COLLABORATION_EVENTS_TOTAL = Counter(
    'subfracture_collaboration_events_total',
    'Total collaboration events',
    ['event_type', 'participant_type']
)

# Server info
SERVER_INFO = Info(
    'subfracture_server_info',
    'SUBFRACTURE server information'
)