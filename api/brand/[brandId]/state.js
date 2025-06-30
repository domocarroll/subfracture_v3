/**
 * GET /api/brand/[brandId]/state
 * Returns brand state data for visualization
 */

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { brandId } = req.query;
  
  // Create demo brand session
  const session = {
    brandId: brandId || 'demo-brand',
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
    serverless: true,
    note: "Demo API - Use client-side localStorage for persistence"
  };
  
  return res.status(200).json({
    success: true,
    brandId: brandId || 'demo-brand',
    state: session,
    timestamp: new Date().toISOString()
  });
}