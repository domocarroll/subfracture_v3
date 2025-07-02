/**
 * MCP Bridge API - Connects Vercel web app to FastMCP SUBFRACTURE server
 * Translates web app API calls to MCP tool calls
 */

const { spawn } = require('child_process');
const fs = require('fs');

// FastMCP Server Configuration
const FASTMCP_SERVER_PATH = '/mnt/e/Projects/fastmcp-subfracture-poc/subfracture_server.py';
const FASTMCP_VENV_PYTHON = '/mnt/e/Projects/fastmcp-subfracture-poc/venv/bin/python';

class MCPBridge {
  constructor() {
    this.mcpProcess = null;
    this.isConnected = false;
    this.messageQueue = [];
    this.requestId = 0;
    this.pendingRequests = new Map();
  }

  async startMCPServer() {
    if (this.mcpProcess) {
      return true; // Already running
    }

    try {
      console.log('🚀 Starting FastMCP SUBFRACTURE server...');
      
      this.mcpProcess = spawn(FASTMCP_VENV_PYTHON, [FASTMCP_SERVER_PATH], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { 
          ...process.env,
          PYTHONPATH: '/mnt/e/Projects/fastmcp-subfracture-poc'
        }
      });

      // Set up message handling
      this.mcpProcess.stdout.on('data', (data) => {
        this.handleMCPMessage(data.toString());
      });

      this.mcpProcess.stderr.on('data', (data) => {
        console.error('MCP Server Error:', data.toString());
      });

      this.mcpProcess.on('close', (code) => {
        console.log(`MCP server exited with code ${code}`);
        this.isConnected = false;
        this.mcpProcess = null;
      });

      // Initialize MCP connection
      await this.initializeMCP();
      
      this.isConnected = true;
      console.log('✅ FastMCP server connected');
      return true;

    } catch (error) {
      console.error('❌ Failed to start MCP server:', error);
      return false;
    }
  }

  async initializeMCP() {
    // Send MCP initialization message
    const initMessage = {
      jsonrpc: "2.0",
      id: ++this.requestId,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {
          tools: {}
        },
        clientInfo: {
          name: "SUBFRACTURE-Web-Bridge",
          version: "1.0.0"
        }
      }
    };

    return this.sendMCPMessage(initMessage);
  }

  async sendMCPMessage(message) {
    return new Promise((resolve, reject) => {
      if (!this.mcpProcess) {
        reject(new Error('MCP server not running'));
        return;
      }

      const requestId = message.id;
      this.pendingRequests.set(requestId, { resolve, reject });

      const messageStr = JSON.stringify(message) + '\n';
      this.mcpProcess.stdin.write(messageStr);

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('MCP request timeout'));
        }
      }, 10000);
    });
  }

  handleMCPMessage(data) {
    try {
      const lines = data.trim().split('\n');
      
      for (const line of lines) {
        if (!line.trim()) continue;
        
        const message = JSON.parse(line);
        
        if (message.id && this.pendingRequests.has(message.id)) {
          const { resolve, reject } = this.pendingRequests.get(message.id);
          this.pendingRequests.delete(message.id);
          
          if (message.error) {
            reject(new Error(message.error.message || 'MCP Error'));
          } else {
            resolve(message.result);
          }
        }
      }
    } catch (error) {
      console.error('Failed to parse MCP message:', error);
    }
  }

  async callMCPTool(toolName, args) {
    const message = {
      jsonrpc: "2.0",
      id: ++this.requestId,
      method: "tools/call",
      params: {
        name: toolName,
        arguments: args
      }
    };

    return this.sendMCPMessage(message);
  }

  // Web API to MCP Tool Mappings
  async getBrandDimensions(brandId, includeMetrics = true) {
    try {
      const result = await this.callMCPTool('get_brand_dimensions', {
        brand_id: brandId,
        include_metrics: includeMetrics
      });
      
      return {
        success: true,
        brandId,
        state: this.formatBrandStateForWeb(result)
      };
    } catch (error) {
      console.error('Error getting brand dimensions:', error);
      throw error;
    }
  }

  async evolveBrandDimension(brandId, dimensionName, signalStrength, reason) {
    try {
      const result = await this.callMCPTool('evolve_brand_dimension', {
        brand_id: brandId,
        dimension_name: dimensionName,
        signal_strength: signalStrength,
        evolution_reason: reason
      });
      
      return {
        success: true,
        message: 'Brand dimension evolved successfully',
        brandId,
        evolution: result
      };
    } catch (error) {
      console.error('Error evolving brand dimension:', error);
      throw error;
    }
  }

  async processWorkshopSignals(sessionId, participantId, signals) {
    try {
      const result = await this.callMCPTool('process_workshop_signals', {
        session_id: sessionId,
        participant_id: participantId,
        signals: signals
      });
      
      return {
        success: true,
        message: 'Workshop signals processed successfully',
        sessionId,
        result
      };
    } catch (error) {
      console.error('Error processing workshop signals:', error);
      throw error;
    }
  }

  async createWorkshopSession(brandId, facilitator, participants = []) {
    try {
      const result = await this.callMCPTool('create_workshop_session', {
        brand_id: brandId,
        facilitator: facilitator,
        participants: participants
      });
      
      return {
        success: true,
        message: 'Workshop session created successfully',
        brandId,
        session: result
      };
    } catch (error) {
      console.error('Error creating workshop session:', error);
      throw error;
    }
  }

  async analyzeCoherence(brandId, analysisDepth = 'comprehensive') {
    try {
      const result = await this.callMCPTool('analyze_brand_coherence', {
        brand_id: brandId,
        analysis_depth: analysisDepth
      });
      
      return {
        success: true,
        brandId,
        coherence: result
      };
    } catch (error) {
      console.error('Error analyzing coherence:', error);
      throw error;
    }
  }

  // Format MCP results for web app compatibility
  formatBrandStateForWeb(mcpResult) {
    return {
      brandId: mcpResult.brand_id || 'demo-brand',
      name: mcpResult.brand?.name || 'Brand Intelligence Demo',
      created: new Date(),
      lastUpdate: new Date(),
      dimensions: this.formatDimensions(mcpResult.brand?.dimensions || []),
      metrics: mcpResult.metrics || {},
      cognitiveState: {
        analytical: 0.7,
        intuitive: 0.7,
        efficiency: 0.8
      },
      instructions: {
        note: "Connected to FastMCP SUBFRACTURE server",
        realTime: "Live MCP integration active"
      }
    };
  }

  formatDimensions(mcpDimensions) {
    return mcpDimensions.map(dim => ({
      name: dim.name,
      signalStrength: dim.signal_strength || 0.5,
      coherence: dim.coherence || 0.7,
      connections: dim.connections || []
    }));
  }

  async stop() {
    if (this.mcpProcess) {
      this.mcpProcess.kill();
      this.mcpProcess = null;
      this.isConnected = false;
    }
  }
}

// Global MCP bridge instance
let mcpBridge = null;

// Serverless API handler
module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Initialize MCP bridge if needed
    if (!mcpBridge) {
      mcpBridge = new MCPBridge();
    }

    // Ensure MCP server is running
    if (!mcpBridge.isConnected) {
      const started = await mcpBridge.startMCPServer();
      if (!started) {
        return res.status(503).json({
          error: 'FastMCP server unavailable',
          fallback: 'Using mock data'
        });
      }
    }

    const { url, method } = req;
    const urlPath = url.replace('/api/mcp-bridge', '').replace('/api/', '');
    const pathParts = urlPath.split('/').filter(Boolean);

    // Route web app calls to MCP tools
    if (pathParts[0] === 'brand') {
      // GET /api/brand/:brandId/state -> get_brand_dimensions
      if (method === 'GET' && pathParts[2] === 'state') {
        const brandId = pathParts[1] || 'demo-brand';
        const result = await mcpBridge.getBrandDimensions(brandId, true);
        return res.status(200).json(result);
      }
    }
    
    if (pathParts[0] === 'workshop') {
      // POST /api/workshop/process -> process_workshop_signals  
      if (method === 'POST' && pathParts[1] === 'process') {
        const { brandId, signals = [], sessionId = 'web-session', participantId = 'web-user' } = req.body;
        
        if (!brandId) {
          return res.status(400).json({ error: 'Brand ID is required' });
        }
        
        const result = await mcpBridge.processWorkshopSignals(sessionId, participantId, signals);
        return res.status(200).json(result);
      }
    }

    if (pathParts[0] === 'evolution') {
      // POST /api/evolution/dimension -> evolve_brand_dimension
      if (method === 'POST' && pathParts[1] === 'dimension') {
        const { brandId, dimensionName, signalStrength, reason } = req.body;
        
        if (!brandId || !dimensionName) {
          return res.status(400).json({ error: 'Brand ID and dimension name are required' });
        }
        
        const result = await mcpBridge.evolveBrandDimension(brandId, dimensionName, signalStrength, reason);
        return res.status(200).json(result);
      }
    }

    if (pathParts[0] === 'coherence') {
      // GET /api/coherence/:brandId -> analyze_brand_coherence
      if (method === 'GET') {
        const brandId = pathParts[1] || 'demo-brand';
        const result = await mcpBridge.analyzeCoherence(brandId);
        return res.status(200).json(result);
      }
    }

    // Default: Health check
    return res.status(200).json({
      status: 'FastMCP Bridge Active',
      connected: mcpBridge.isConnected,
      endpoints: [
        'GET /api/brand/:brandId/state -> get_brand_dimensions',
        'POST /api/workshop/process -> process_workshop_signals',
        'POST /api/evolution/dimension -> evolve_brand_dimension', 
        'GET /api/coherence/:brandId -> analyze_brand_coherence'
      ]
    });

  } catch (error) {
    console.error('MCP Bridge Error:', error);
    return res.status(500).json({
      error: 'MCP Bridge error',
      message: error.message,
      fallback: 'Check FastMCP server status'
    });
  }
};