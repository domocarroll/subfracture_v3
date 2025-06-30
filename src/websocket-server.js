#!/usr/bin/env node
/**
 * SUBFRACTURE Real-Time Brand Intelligence WebSocket Server
 * Connects workshop processing, AI engine, and 3D visualization
 */

const WebSocket = require('ws');
const express = require('express');
const http = require('http');
const path = require('path');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');

class SubfractureWebSocketServer {
  constructor(port = 8080) {
    this.port = port;
    this.clients = new Map();
    this.brandSessions = new Map();
    this.aiStates = new Map();
    
    this.setupServer();
    this.setupWebSocket();
    this.startServer();
  }

  setupServer() {
    this.app = express();
    this.app.use(cors());
    this.app.use(express.json());
    
    // Serve static files
    this.app.use(express.static(path.join(__dirname, '../')));
    
    // API endpoints
    this.app.post('/api/workshop/process', this.handleWorkshopData.bind(this));
    this.app.post('/api/ai/cognitive-state', this.handleCognitiveState.bind(this));
    this.app.post('/api/refinement/dialogue', this.handleRefinementDialogue.bind(this));
    this.app.get('/api/brand/:id/state', this.getBrandState.bind(this));
    
    this.server = http.createServer(this.app);
  }

  setupWebSocket() {
    this.wss = new WebSocket.Server({ server: this.server });
    
    this.wss.on('connection', (ws, req) => {
      const clientId = uuidv4();
      const clientInfo = {
        id: clientId,
        ws: ws,
        connectedAt: new Date(),
        brandId: null,
        userAgent: req.headers['user-agent'],
        ip: req.connection.remoteAddress
      };
      
      this.clients.set(clientId, clientInfo);
      
      console.log(`🔗 Client connected: ${clientId} (${this.clients.size} total)`);
      
      // Send welcome message
      this.sendToClient(clientId, {
        type: 'welcome',
        clientId: clientId,
        message: 'Connected to SUBFRACTURE Brand Intelligence Network'
      });

      // Handle messages
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleClientMessage(clientId, message);
        } catch (error) {
          console.error(`❌ Invalid message from ${clientId}:`, error);
        }
      });

      // Handle disconnect
      ws.on('close', () => {
        console.log(`❌ Client disconnected: ${clientId}`);
        this.clients.delete(clientId);
      });

      // Handle errors
      ws.on('error', (error) => {
        console.error(`🚨 WebSocket error for ${clientId}:`, error);
      });
    });
  }

  handleClientMessage(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    console.log(`📨 Message from ${clientId}:`, message.type);

    switch (message.type) {
      case 'join_brand':
        this.handleJoinBrand(clientId, message.brandId);
        break;
      
      case 'update_dimension':
        this.handleDimensionUpdate(clientId, message);
        break;
      
      case 'trigger_refinement':
        this.handleRefinementTrigger(clientId, message);
        break;
      
      case 'ai_query':
        this.handleAIQuery(clientId, message);
        break;
      
      default:
        console.log(`🤷 Unknown message type: ${message.type}`);
    }
  }

  handleJoinBrand(clientId, brandId) {
    const client = this.clients.get(clientId);
    if (!client) return;

    client.brandId = brandId;
    
    // Send current brand state
    const brandState = this.brandSessions.get(brandId) || this.createBrandSession(brandId);
    
    this.sendToClient(clientId, {
      type: 'brand_state',
      brandId: brandId,
      state: brandState
    });

    console.log(`🎯 Client ${clientId} joined brand ${brandId}`);
  }

  createBrandSession(brandId) {
    const session = {
      id: brandId,
      name: `Brand ${brandId.substring(0, 8)}`,
      createdAt: new Date(),
      dimensions: this.generateInitialDimensions(),
      connections: this.generateInitialConnections(),
      contradictions: [],
      gaps: [],
      cognitiveState: {
        analytical: 0.7,
        intuitive: 0.7,
        efficiency: 0.75
      },
      metrics: {
        coherence: 0.84,
        evolution_rate: 'moderate',
        signal_strength: 0.78
      }
    };

    this.brandSessions.set(brandId, session);
    return session;
  }

  generateInitialDimensions() {
    return [
      {
        name: 'market_position',
        depth: 0.85,
        coherence: 0.92,
        color: 0x2196F3,
        viscosity: 0.8,
        refraction: 1.52,
        signalStrength: 0.85,
        lastUpdated: new Date()
      },
      {
        name: 'value_proposition',
        depth: 0.78,
        coherence: 0.88,
        color: 0x4CAF50,
        viscosity: 0.75,
        refraction: 1.48,
        signalStrength: 0.78,
        lastUpdated: new Date()
      },
      {
        name: 'brand_narrative',
        depth: 0.82,
        coherence: 0.75,
        color: 0xFF9800,
        viscosity: 0.9,
        refraction: 1.54,
        signalStrength: 0.82,
        lastUpdated: new Date()
      },
      {
        name: 'emotional_landscape',
        depth: 0.90,
        coherence: 0.85,
        color: 0xE91E63,
        viscosity: 0.95,
        refraction: 1.55,
        signalStrength: 0.90,
        lastUpdated: new Date()
      },
      {
        name: 'visual_identity',
        depth: 0.75,
        coherence: 0.95,
        color: 0x9C27B0,
        viscosity: 0.7,
        refraction: 1.49,
        signalStrength: 0.75,
        lastUpdated: new Date()
      },
      {
        name: 'digital_presence',
        depth: 0.88,
        coherence: 0.78,
        color: 0x607D8B,
        viscosity: 0.8,
        refraction: 1.51,
        signalStrength: 0.88,
        lastUpdated: new Date()
      },
      {
        name: 'innovation_capacity',
        depth: 0.92,
        coherence: 0.88,
        color: 0xFF5722,
        viscosity: 0.85,
        refraction: 1.53,
        signalStrength: 0.92,
        lastUpdated: new Date()
      }
    ];
  }

  generateInitialConnections() {
    return [
      {
        from: 'market_position',
        to: 'value_proposition',
        strength: 0.9,
        type: 'strategic',
        active: true
      },
      {
        from: 'brand_narrative',
        to: 'emotional_landscape',
        strength: 0.85,
        type: 'experiential',
        active: true
      },
      {
        from: 'visual_identity',
        to: 'digital_presence',
        strength: 0.8,
        type: 'implementation',
        active: true
      }
    ];
  }

  // API Handlers
  async handleWorkshopData(req, res) {
    try {
      const { brandId, signals, contradictions, gaps } = req.body;
      
      console.log(`📊 Workshop data received for brand ${brandId}`);
      
      // Update brand session
      let brandSession = this.brandSessions.get(brandId);
      if (!brandSession) {
        brandSession = this.createBrandSession(brandId);
      }

      // Process signals into dimension updates
      if (signals && signals.length > 0) {
        signals.forEach(signal => {
          const dimension = brandSession.dimensions.find(d => 
            d.name === signal.category || 
            d.name.includes(signal.category?.toLowerCase())
          );
          
          if (dimension) {
            // Update based on signal confidence and frequency
            dimension.signalStrength = signal.confidence;
            dimension.coherence = Math.min(dimension.coherence + 0.05, 1.0);
            dimension.lastUpdated = new Date();
          }
        });
      }

      // Process contradictions
      if (contradictions && contradictions.length > 0) {
        brandSession.contradictions = contradictions.map(c => ({
          ...c,
          id: uuidv4(),
          detected: new Date()
        }));
      }

      // Process gaps
      if (gaps && gaps.length > 0) {
        brandSession.gaps = gaps.map(g => ({
          ...g,
          id: uuidv4(),
          identified: new Date()
        }));
      }

      // Broadcast updates to all clients watching this brand
      this.broadcastToBrand(brandId, {
        type: 'workshop_update',
        brandId: brandId,
        updates: {
          signals: signals?.length || 0,
          contradictions: contradictions?.length || 0,
          gaps: gaps?.length || 0
        },
        newState: brandSession
      });

      res.json({ success: true, brandId: brandId });
    } catch (error) {
      console.error('❌ Workshop data processing error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  async handleCognitiveState(req, res) {
    try {
      const { brandId, analytical, intuitive, efficiency, context } = req.body;
      
      console.log(`🧠 Cognitive state update for brand ${brandId}`);
      
      let brandSession = this.brandSessions.get(brandId);
      if (!brandSession) {
        brandSession = this.createBrandSession(brandId);
      }

      // Update cognitive state
      brandSession.cognitiveState = {
        analytical: analytical || 0.7,
        intuitive: intuitive || 0.7,
        efficiency: efficiency || 0.75,
        lastUpdate: new Date(),
        context: context || {}
      };

      // Broadcast cognitive state changes
      this.broadcastToBrand(brandId, {
        type: 'cognitive_update',
        brandId: brandId,
        cognitiveState: brandSession.cognitiveState
      });

      res.json({ success: true, brandId: brandId });
    } catch (error) {
      console.error('❌ Cognitive state processing error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  async handleRefinementDialogue(req, res) {
    try {
      const { brandId, speaker, message, messageType } = req.body;
      
      console.log(`💬 Refinement dialogue for brand ${brandId} from ${speaker}`);
      
      // Broadcast dialogue to all clients
      this.broadcastToBrand(brandId, {
        type: 'dialogue_message',
        brandId: brandId,
        dialogue: {
          speaker: speaker,
          message: message,
          messageType: messageType || 'question',
          timestamp: new Date()
        }
      });

      res.json({ success: true, brandId: brandId });
    } catch (error) {
      console.error('❌ Refinement dialogue error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  getBrandState(req, res) {
    const brandId = req.params.id;
    const brandSession = this.brandSessions.get(brandId) || this.createBrandSession(brandId);
    res.json(brandSession);
  }

  // Broadcasting utilities
  broadcastToBrand(brandId, message) {
    this.clients.forEach((client, clientId) => {
      if (client.brandId === brandId && client.ws.readyState === WebSocket.OPEN) {
        this.sendToClient(clientId, message);
      }
    });
  }

  broadcast(message) {
    this.clients.forEach((client, clientId) => {
      if (client.ws.readyState === WebSocket.OPEN) {
        this.sendToClient(clientId, message);
      }
    });
  }

  sendToClient(clientId, message) {
    const client = this.clients.get(clientId);
    if (client && client.ws.readyState === WebSocket.OPEN) {
      try {
        client.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error(`❌ Failed to send to client ${clientId}:`, error);
      }
    }
  }

  startServer() {
    this.server.listen(this.port, () => {
      console.log(`🚀 SUBFRACTURE WebSocket Server running on port ${this.port}`);
      console.log(`🌐 WebSocket endpoint: ws://localhost:${this.port}`);
      console.log(`📡 API endpoint: http://localhost:${this.port}/api`);
      console.log(`🎮 Demo available at: http://localhost:${this.port}/demo-liquid-glass.html`);
    });
  }

  // Graceful shutdown
  shutdown() {
    console.log('🛑 Shutting down SUBFRACTURE WebSocket Server...');
    
    this.clients.forEach((client, clientId) => {
      client.ws.close();
    });
    
    this.server.close(() => {
      console.log('✅ Server shut down complete');
    });
  }
}

// Start server if run directly
if (require.main === module) {
  const server = new SubfractureWebSocketServer(8888);
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    server.shutdown();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    server.shutdown();
    process.exit(0);
  });
}

module.exports = SubfractureWebSocketServer;