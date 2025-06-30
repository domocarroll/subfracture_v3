/**
 * SUBFRACTURE Client Presentation App
 * Main application for client-facing brand presentations
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import BrandUniverse3D from './components/BrandUniverse3D';

interface BrandData {
  brandName: string;
  dimensions: Record<string, any>;
  gravityRules: any[];
  metrics: {
    world_coherence: number;
    attraction_force: number;
  };
  presentation: {
    executiveSummary: string;
    brandNarrative: string;
    keyInsights: string[];
  };
}

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Arial', sans-serif;
  overflow: hidden;
`;

const Header = styled(motion.header)`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 20px 40px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Logo = styled.div`
  color: white;
  font-size: 24px;
  font-weight: bold;
  letter-spacing: 2px;
`;

const Navigation = styled.nav`
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 30px;
`;

const NavButton = styled(motion.button)<{ active?: boolean }>`
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.2)' : 'transparent'};
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 10px 20px;
  border-radius: 25px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
`;

const MainContent = styled(motion.main)`
  width: 100%;
  height: 100%;
  position: relative;
`;

const VisualizationContainer = styled.div`
  width: 100%;
  height: 100%;
`;

const SidePanel = styled(motion.div)`
  position: absolute;
  left: 0;
  top: 80px;
  bottom: 0;
  width: 400px;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(15px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  padding: 30px;
  overflow-y: auto;
  z-index: 50;
`;

const PanelSection = styled.div`
  margin-bottom: 30px;
`;

const PanelTitle = styled.h3`
  color: white;
  margin: 0 0 15px 0;
  font-size: 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 10px;
`;

const PanelContent = styled.div`
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  font-size: 14px;
`;

const MetricCard = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
`;

const MetricLabel = styled.div`
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 5px;
`;

const MetricValue = styled.div`
  color: white;
  font-size: 24px;
  font-weight: bold;
`;

const ControlPanel = styled(motion.div)`
  position: absolute;
  bottom: 30px;
  right: 30px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 20px;
  z-index: 50;
`;

const ControlButton = styled(motion.button)<{ active?: boolean }>`
  background: ${props => props.active ? '#4CAF50' : 'rgba(255, 255, 255, 0.1)'};
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  margin: 0 5px 5px 0;
  transition: all 0.3s ease;

  &:hover {
    background: ${props => props.active ? '#45a049' : 'rgba(255, 255, 255, 0.2)'};
  }
`;

type ViewMode = 'universe' | 'narrative' | 'insights' | 'evolution';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('universe');
  const [showSidePanel, setShowSidePanel] = useState(true);
  const [showGravityForces, setShowGravityForces] = useState(true);
  const [brandData, setBrandData] = useState<BrandData | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data - in production this would come from API
  useEffect(() => {
    const mockBrandData: BrandData = {
      brandName: "EcoFlow Technologies",
      dimensions: {
        market_position: { depth: 0.85, coherence: 0.92 },
        value_proposition: { depth: 0.78, coherence: 0.88 },
        brand_narrative: { depth: 0.82, coherence: 0.75 },
        emotional_landscape: { depth: 0.90, coherence: 0.85 },
        visual_identity: { depth: 0.75, coherence: 0.95 },
        experiential_design: { depth: 0.68, coherence: 0.82 },
        digital_presence: { depth: 0.88, coherence: 0.78 },
        innovation_capacity: { depth: 0.92, coherence: 0.88 }
      },
      gravityRules: [
        { name: "authenticity", force: 0.9, active_conditions: ["transparent_communication", "consistent_values"] },
        { name: "innovation", force: 0.85, active_conditions: ["tech_leadership", "creative_solutions"] },
        { name: "community", force: 0.88, active_conditions: ["active_engagement", "shared_values"] },
        { name: "experience", force: 0.82, active_conditions: ["seamless_journey", "emotional_resonance"] }
      ],
      metrics: {
        world_coherence: 0.84,
        attraction_force: 0.86
      },
      presentation: {
        executiveSummary: "EcoFlow Technologies represents a breakthrough in sustainable technology, combining environmental responsibility with cutting-edge innovation to create solutions that benefit both business and planet.",
        brandNarrative: "Born from the belief that technology should heal rather than harm, EcoFlow Technologies emerged as a beacon of hope in the sustainability space. Our brand embodies the perfect harmony between innovation and environmental stewardship.",
        keyInsights: [
          "93% brand coherence across all dimensions",
          "Strong gravitational pull through authenticity (90% force)",
          "Innovation capacity leads market positioning",
          "Emotional landscape drives customer connection"
        ]
      }
    };

    setTimeout(() => {
      setBrandData(mockBrandData);
      setLoading(false);
    }, 1000);
  }, []);

  const handleViewChange = (view: ViewMode) => {
    setCurrentView(view);
  };

  if (loading) {
    return (
      <AppContainer>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%',
          color: 'white',
          fontSize: '24px'
        }}>
          Loading Brand Universe...
        </div>
      </AppContainer>
    );
  }

  if (!brandData) {
    return (
      <AppContainer>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%',
          color: 'white',
          fontSize: '24px'
        }}>
          No brand data available
        </div>
      </AppContainer>
    );
  }

  return (
    <AppContainer>
      <Header
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8 }}
      >
        <Logo>SUBFRACTURE</Logo>
        <Navigation>
          <NavButton
            active={currentView === 'universe'}
            onClick={() => handleViewChange('universe')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Universe
          </NavButton>
          <NavButton
            active={currentView === 'narrative'}
            onClick={() => handleViewChange('narrative')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Narrative
          </NavButton>
          <NavButton
            active={currentView === 'insights'}
            onClick={() => handleViewChange('insights')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Insights
          </NavButton>
          <NavButton
            active={currentView === 'evolution'}
            onClick={() => handleViewChange('evolution')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Evolution
          </NavButton>
        </Navigation>
      </Header>

      <MainContent
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        <VisualizationContainer>
          <BrandUniverse3D
            brandName={brandData.brandName}
            dimensions={brandData.dimensions}
            gravityRules={brandData.gravityRules}
            metrics={brandData.metrics}
            interactive={true}
            showGravityForces={showGravityForces}
          />
        </VisualizationContainer>

        <AnimatePresence>
          {showSidePanel && (
            <SidePanel
              initial={{ x: -400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -400, opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              <PanelSection>
                <PanelTitle>Brand Overview</PanelTitle>
                <PanelContent>
                  <strong>{brandData.brandName}</strong> is a living brand ecosystem with {Object.keys(brandData.dimensions).length} active dimensions and {brandData.gravityRules.length} gravity rules creating natural market attraction.
                </PanelContent>
              </PanelSection>

              <PanelSection>
                <PanelTitle>Key Metrics</PanelTitle>
                <MetricCard>
                  <MetricLabel>World Coherence</MetricLabel>
                  <MetricValue>{(brandData.metrics.world_coherence * 100).toFixed(0)}%</MetricValue>
                </MetricCard>
                <MetricCard>
                  <MetricLabel>Attraction Force</MetricLabel>
                  <MetricValue>{(brandData.metrics.attraction_force * 100).toFixed(0)}%</MetricValue>
                </MetricCard>
                <MetricCard>
                  <MetricLabel>Active Dimensions</MetricLabel>
                  <MetricValue>{Object.keys(brandData.dimensions).length}</MetricValue>
                </MetricCard>
              </PanelSection>

              {currentView === 'narrative' && (
                <PanelSection>
                  <PanelTitle>Brand Narrative</PanelTitle>
                  <PanelContent>
                    {brandData.presentation.brandNarrative}
                  </PanelContent>
                </PanelSection>
              )}

              {currentView === 'insights' && (
                <PanelSection>
                  <PanelTitle>Key Insights</PanelTitle>
                  <PanelContent>
                    {brandData.presentation.keyInsights.map((insight, index) => (
                      <div key={index} style={{ marginBottom: '10px', paddingLeft: '15px' }}>
                        • {insight}
                      </div>
                    ))}
                  </PanelContent>
                </PanelSection>
              )}

              <PanelSection>
                <PanelTitle>Executive Summary</PanelTitle>
                <PanelContent>
                  {brandData.presentation.executiveSummary}
                </PanelContent>
              </PanelSection>
            </SidePanel>
          )}
        </AnimatePresence>

        <ControlPanel
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          <div style={{ color: 'white', fontSize: '12px', marginBottom: '10px' }}>
            Visualization Controls
          </div>
          <ControlButton
            active={showSidePanel}
            onClick={() => setShowSidePanel(!showSidePanel)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Info Panel
          </ControlButton>
          <ControlButton
            active={showGravityForces}
            onClick={() => setShowGravityForces(!showGravityForces)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Gravity Forces
          </ControlButton>
          <ControlButton
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Full Screen
          </ControlButton>
          <ControlButton
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Export View
          </ControlButton>
        </ControlPanel>
      </MainContent>
    </AppContainer>
  );
};

export default App;