#!/usr/bin/env node
/**
 * Workshop Data Simulator
 * Simulates real workshop processing to test real-time brand intelligence
 */

const axios = require('axios');

class WorkshopSimulator {
  constructor(apiBaseUrl = 'http://localhost:8888/api') {
    this.apiBaseUrl = apiBaseUrl;
    this.brandId = 'demo-brand-' + Math.random().toString(36).substr(2, 9);
    
    console.log(`🎬 Workshop Simulator initialized for brand: ${this.brandId}`);
  }

  async simulateWorkshopSession() {
    console.log('🎭 Starting simulated workshop session...');
    
    // Phase 1: Initial signal extraction
    await this.simulateSignalExtraction();
    await this.delay(2000);
    
    // Phase 2: Contradiction discovery
    await this.simulateContradictionDiscovery();
    await this.delay(3000);
    
    // Phase 3: Gap identification
    await this.simulateGapIdentification();
    await this.delay(2000);
    
    // Phase 4: Refinement dialogue
    await this.simulateRefinementDialogue();
    await this.delay(3000);
    
    // Phase 5: Cognitive state evolution
    await this.simulateCognitiveEvolution();
    
    console.log('✅ Workshop simulation complete!');
  }

  async simulateSignalExtraction() {
    console.log('📊 Simulating signal extraction...');
    
    const signals = [
      {
        signal: 'We want to be the most trusted brand in sustainable technology',
        confidence: 0.92,
        frequency: 4,
        context: 'Strategic positioning discussion',
        stakeholder: 'CEO',
        sentiment: 'positive',
        category: 'market_position'
      },
      {
        signal: 'Our core value is environmental responsibility above profit',
        confidence: 0.88,
        frequency: 3,
        context: 'Values clarification session',
        stakeholder: 'CTO',
        sentiment: 'strong_positive',
        category: 'value_proposition'
      },
      {
        signal: 'We need to feel innovative but also reliable and established',
        confidence: 0.85,
        frequency: 2,
        context: 'Brand personality workshop',
        stakeholder: 'Marketing Director',
        sentiment: 'thoughtful',
        category: 'emotional_landscape'
      },
      {
        signal: 'Our story is about transforming waste into valuable resources',
        confidence: 0.90,
        frequency: 5,
        context: 'Narrative development',
        stakeholder: 'Founder',
        sentiment: 'passionate',
        category: 'brand_narrative'
      }
    ];

    const response = await this.sendWorkshopData({
      signals: signals,
      contradictions: [],
      gaps: []
    });

    console.log('  ✅ Signal extraction sent successfully');
    return response;
  }

  async simulateContradictionDiscovery() {
    console.log('⚡ Simulating contradiction discovery...');
    
    const contradictions = [
      {
        signal1: {
          signal: 'We want to be the premium choice in our category',
          confidence: 0.85
        },
        signal2: {
          signal: 'We need to be accessible to everyone, not just the wealthy',
          confidence: 0.78
        },
        conflictType: 'positioning_accessibility',
        severity: 'high',
        requiresResolution: true,
        suggestedResolution: 'Define premium value differently - premium quality at fair prices'
      },
      {
        signal1: {
          signal: 'Innovation and cutting-edge technology define us',
          confidence: 0.90
        },
        signal2: {
          signal: 'Reliability and proven solutions are what customers want',
          confidence: 0.82
        },
        conflictType: 'innovation_reliability',
        severity: 'medium',
        requiresResolution: true,
        suggestedResolution: 'Position as "proven innovation" - tested cutting-edge solutions'
      }
    ];

    const response = await this.sendWorkshopData({
      signals: [],
      contradictions: contradictions,
      gaps: []
    });

    console.log('  ✅ Contradiction discovery sent successfully');
    return response;
  }

  async simulateGapIdentification() {
    console.log('🕳️ Simulating gap identification...');
    
    const gaps = [
      {
        category: 'target_audience',
        missingElement: 'Specific demographic and psychographic profiles',
        importance: 'critical',
        suggestedQuestions: [
          'Who exactly is your primary customer?',
          'What are their key pain points and motivations?',
          'How do they currently think about sustainability?'
        ]
      },
      {
        category: 'competitive_differentiation',
        missingElement: 'Clear differentiation from other sustainable tech companies',
        importance: 'important',
        suggestedQuestions: [
          'How are you different from competitors like Tesla, Patagonia, or Interface?',
          'What unique value do you provide that others cannot?'
        ]
      },
      {
        category: 'brand_personality',
        missingElement: 'Specific personality traits and tone of voice',
        importance: 'important',
        suggestedQuestions: [
          'If your brand was a person, how would they speak?',
          'What personality traits would they have?'
        ]
      }
    ];

    const response = await this.sendWorkshopData({
      signals: [],
      contradictions: [],
      gaps: gaps
    });

    console.log('  ✅ Gap identification sent successfully');
    return response;
  }

  async simulateRefinementDialogue() {
    console.log('💬 Simulating refinement dialogue...');
    
    const dialogues = [
      {
        speaker: 'danni',
        message: 'I noticed a contradiction between wanting to be premium and accessible. Can you help me understand how you define "premium" in your context?',
        messageType: 'clarification'
      },
      {
        speaker: 'team_member',
        message: 'We see premium as meaning high-quality and well-designed, not necessarily expensive. We want to democratize good sustainable technology.',
        messageType: 'response'
      },
      {
        speaker: 'danni',
        message: 'That\'s a great clarification! So premium quality at fair prices. This helps resolve the positioning tension. Now, can you tell me more about your target audience?',
        messageType: 'follow_up'
      }
    ];

    for (const dialogue of dialogues) {
      await this.sendRefinementDialogue(dialogue);
      await this.delay(1500);
    }

    console.log('  ✅ Refinement dialogue sent successfully');
  }

  async simulateCognitiveEvolution() {
    console.log('🧠 Simulating cognitive evolution...');
    
    const cognitiveStates = [
      {
        analytical: 0.75,
        intuitive: 0.70,
        efficiency: 0.78,
        context: { phase: 'analysis', focus: 'contradiction_resolution' }
      },
      {
        analytical: 0.68,
        intuitive: 0.85,
        efficiency: 0.82,
        context: { phase: 'synthesis', focus: 'creative_integration' }
      },
      {
        analytical: 0.80,
        intuitive: 0.75,
        efficiency: 0.88,
        context: { phase: 'validation', focus: 'coherence_check' }
      }
    ];

    for (const state of cognitiveStates) {
      await this.sendCognitiveState(state);
      await this.delay(2000);
    }

    console.log('  ✅ Cognitive evolution sent successfully');
  }

  async sendWorkshopData(data) {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/workshop/process`, {
        brandId: this.brandId,
        ...data
      });
      return response.data;
    } catch (error) {
      console.error('❌ Error sending workshop data:', error.message);
      throw error;
    }
  }

  async sendRefinementDialogue(dialogue) {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/refinement/dialogue`, {
        brandId: this.brandId,
        ...dialogue
      });
      return response.data;
    } catch (error) {
      console.error('❌ Error sending refinement dialogue:', error.message);
      throw error;
    }
  }

  async sendCognitiveState(state) {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/ai/cognitive-state`, {
        brandId: this.brandId,
        ...state
      });
      return response.data;
    } catch (error) {
      console.error('❌ Error sending cognitive state:', error.message);
      throw error;
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async runContinuousSimulation(intervalMs = 10000) {
    console.log(`🔄 Starting continuous simulation (every ${intervalMs/1000}s)`);
    
    while (true) {
      try {
        await this.simulateWorkshopSession();
        console.log(`⏱️ Waiting ${intervalMs/1000}s before next simulation...`);
        await this.delay(intervalMs);
      } catch (error) {
        console.error('❌ Simulation error:', error);
        await this.delay(5000); // Wait 5s before retrying
      }
    }
  }
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0] || 'single';
  
  const simulator = new WorkshopSimulator();
  
  switch (command) {
    case 'single':
      simulator.simulateWorkshopSession()
        .then(() => process.exit(0))
        .catch(error => {
          console.error('❌ Simulation failed:', error);
          process.exit(1);
        });
      break;
      
    case 'continuous':
      const interval = parseInt(args[1]) || 10000;
      simulator.runContinuousSimulation(interval);
      break;
      
    default:
      console.log('Usage:');
      console.log('  node workshop-simulator.js single           # Run one simulation');
      console.log('  node workshop-simulator.js continuous [ms]  # Run continuous simulation');
      break;
  }
}

module.exports = WorkshopSimulator;