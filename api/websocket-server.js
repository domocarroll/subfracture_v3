/**
 * Serverless API endpoint for SUBFRACTURE Real-Time Brand Intelligence
 * Cloud-optimized with client-side state management
 */

const { v4: uuidv4 } = require('uuid');

// Create fresh demo brand session (serverless functions are stateless)
function createBrandSession(brandId) {
  const session = {
    brandId,
    created: new Date(),
    lastUpdate: new Date(),
    dimensions: [
      { name: 'market_position', signalStrength: 0.5, coherence: 0.7, connections: [] },
      { name: 'value_proposition', signalStrength: 0.6, coherence: 0.8, connections: [] },
      { name: 'emotional_landscape', signalStrength: 0.4, coherence: 0.6, connections: [] },
      { name: 'brand_narrative', signalStrength: 0.7, coherence: 0.9, connections: [] },
      { name: 'target_audience', signalStrength: 0.3, coherence: 0.5, connections: [] },
      { name: 'competitive_differentiation', signalStrength: 0.5, coherence: 0.6, connections: [] }
    ],
    contradictions: [],
    gaps: [],
    cognitiveState: {
      analytical: 0.5,
      intuitive: 0.5,
      efficiency: 0.7
    },
    dialogue: [],
    instructions: {
      note: "This is a serverless demo API. Real state is managed client-side via localStorage.",
      clientStorage: "Use localStorage.setItem('brand_' + brandId, JSON.stringify(state)) to persist state",
      realTime: "State updates trigger BroadcastChannel events for cross-window sync"
    }
  };
  
  return session;
}

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { url, method } = req;
  
  try {
    // Parse URL path
    const urlPath = url.replace('/api/websocket-server', '').replace('/api/', '');
    const pathParts = urlPath.split('/').filter(Boolean);
    
    if (pathParts[0] === 'brand') {
      // GET /api/brand/:brandId/state
      if (method === 'GET' && pathParts[2] === 'state') {
        const brandId = pathParts[1] || 'demo-brand';
        const session = createBrandSession(brandId);
        
        return res.status(200).json({
          success: true,
          brandId,
          state: session
        });
      }
    }
    
    if (pathParts[0] === 'workshop') {
      // POST /api/workshop/process
      if (method === 'POST' && pathParts[1] === 'process') {
        const { brandId, signals = [], contradictions = [], gaps = [] } = req.body;
        
        if (!brandId) {
          return res.status(400).json({ error: 'Brand ID is required' });
        }
        
        const session = createBrandSession(brandId);
        
        // Process signals
        signals.forEach(signal => {
          const dimension = session.dimensions.find(d => 
            d.name === signal.category || 
            d.name.includes(signal.category?.toLowerCase())
          );
          if (dimension) {
            dimension.signalStrength = signal.confidence || 0.5;
            dimension.coherence = Math.min(dimension.coherence + 0.05, 1.0);
          }
        });
        
        // Process contradictions
        session.contradictions = [...session.contradictions, ...contradictions];
        
        // Process gaps
        session.gaps = [...session.gaps, ...gaps];
        
        session.lastUpdate = new Date();
        
        return res.status(200).json({
          success: true,
          message: 'Workshop data processed successfully',
          brandId,
          updatedState: session
        });
      }
    }
    
    if (pathParts[0] === 'ai') {
      // POST /api/ai/cognitive-state
      if (method === 'POST' && pathParts[1] === 'cognitive-state') {
        const { brandId, analytical, intuitive, efficiency, context } = req.body;
        
        if (!brandId) {
          return res.status(400).json({ error: 'Brand ID is required' });
        }
        
        const session = createBrandSession(brandId);
        
        session.cognitiveState = {
          analytical: analytical || session.cognitiveState.analytical,
          intuitive: intuitive || session.cognitiveState.intuitive,
          efficiency: efficiency || session.cognitiveState.efficiency,
          context: context || {}
        };
        
        session.lastUpdate = new Date();
        
        return res.status(200).json({
          success: true,
          message: 'Cognitive state updated successfully',
          brandId,
          cognitiveState: session.cognitiveState
        });
      }
    }
    
    if (pathParts[0] === 'refinement') {
      // POST /api/refinement/dialogue
      if (method === 'POST' && pathParts[1] === 'dialogue') {
        const { brandId, speaker, message, messageType } = req.body;
        
        if (!brandId) {
          return res.status(400).json({ error: 'Brand ID is required' });
        }
        
        const session = createBrandSession(brandId);
        
        const dialogueEntry = {
          id: uuidv4(),
          speaker,
          message,
          messageType,
          timestamp: new Date()
        };
        
        session.dialogue.push(dialogueEntry);
        session.lastUpdate = new Date();
        
        return res.status(200).json({
          success: true,
          message: 'Dialogue entry added successfully',
          brandId,
          dialogueEntry
        });
      }
    }
    
    // Default response for unmatched routes
    return res.status(404).json({
      error: 'Endpoint not found',
      availableEndpoints: [
        'GET /api/brand/:brandId/state',
        'POST /api/workshop/process',
        'POST /api/ai/cognitive-state',
        'POST /api/refinement/dialogue'
      ]
    });
    
  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
};