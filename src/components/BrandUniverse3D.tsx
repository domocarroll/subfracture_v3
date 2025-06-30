/**
 * SUBFRACTURE 3D Brand Universe Visualization
 * Interactive 3D representation of living brand ecosystems
 */

import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Sphere, Box, Line } from '@react-three/drei';
import { Vector3 } from 'three';
import * as THREE from 'three';

interface BrandDimension {
  name: string;
  depth: number;
  coherence: number;
  position: [number, number, number];
  color: string;
}

interface GravityRule {
  name: string;
  force: number;
  position: [number, number, number];
  connections: string[];
}

interface BrandUniverseProps {
  brandName: string;
  dimensions: Record<string, any>;
  gravityRules: any[];
  metrics: {
    world_coherence: number;
    attraction_force: number;
  };
  interactive?: boolean;
  showGravityForces?: boolean;
  animationSpeed?: number;
}

/**
 * Individual brand dimension visualization
 */
const BrandDimensionSphere: React.FC<{
  dimension: BrandDimension;
  onHover?: (dimension: BrandDimension | null) => void;
  onClick?: (dimension: BrandDimension) => void;
  interactive?: boolean;
}> = ({ dimension, onHover, onClick, interactive = true }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      // Gentle floating animation
      meshRef.current.position.y = dimension.position[1] + Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
      
      // Rotate based on coherence
      meshRef.current.rotation.y += dimension.coherence * 0.005;
      
      // Scale based on hover state
      const targetScale = hovered ? 1.2 : 1.0;
      meshRef.current.scale.lerp(new Vector3(targetScale, targetScale, targetScale), 0.1);
    }
  });

  return (
    <group position={dimension.position}>
      <Sphere
        ref={meshRef}
        args={[dimension.depth * 0.5 + 0.3, 32, 32]}
        onPointerOver={() => {
          if (interactive) {
            setHovered(true);
            onHover?.(dimension);
          }
        }}
        onPointerOut={() => {
          if (interactive) {
            setHovered(false);
            onHover?.(null);
          }
        }}
        onClick={() => interactive && onClick?.(dimension)}
      >
        <meshStandardMaterial
          color={dimension.color}
          opacity={0.7 + dimension.coherence * 0.3}
          transparent
          roughness={0.3}
          metalness={0.1}
        />
      </Sphere>
      
      {/* Dimension label */}
      <Text
        position={[0, dimension.depth * 0.5 + 0.8, 0]}
        fontSize={0.2}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {dimension.name.replace('_', ' ').toUpperCase()}
      </Text>
      
      {/* Coherence indicator */}
      <Text
        position={[0, -dimension.depth * 0.5 - 0.5, 0]}
        fontSize={0.12}
        color="#888"
        anchorX="center"
        anchorY="middle"
      >
        {(dimension.coherence * 100).toFixed(0)}% coherent
      </Text>
    </group>
  );
};

/**
 * Gravity force visualization
 */
const GravityForce: React.FC<{
  rule: GravityRule;
  dimensions: BrandDimension[];
  showConnections: boolean;
}> = ({ rule, dimensions, showConnections }) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      // Pulse animation based on force strength
      const scale = 1.0 + Math.sin(state.clock.elapsedTime * 2) * rule.force * 0.1;
      groupRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group ref={groupRef} position={rule.position}>
      {/* Gravity center */}
      <Box args={[0.2, 0.2, 0.2]}>
        <meshStandardMaterial
          color="#ff6b6b"
          emissive="#ff6b6b"
          emissiveIntensity={rule.force * 0.3}
        />
      </Box>
      
      {/* Gravity field visualization */}
      <Sphere args={[rule.force * 2, 16, 16]}>
        <meshBasicMaterial
          color="#ff6b6b"
          transparent
          opacity={0.1}
          side={THREE.DoubleSide}
        />
      </Sphere>
      
      {/* Rule label */}
      <Text
        position={[0, rule.force * 2 + 0.3, 0]}
        fontSize={0.15}
        color="#ff6b6b"
        anchorX="center"
        anchorY="middle"
      >
        {rule.name.toUpperCase()}
      </Text>
      
      {/* Connection lines to influenced dimensions */}
      {showConnections && rule.connections.map((connectionName, index) => {
        const targetDimension = dimensions.find(d => d.name === connectionName);
        if (!targetDimension) return null;
        
        const points = [
          new Vector3(...rule.position),
          new Vector3(...targetDimension.position)
        ];
        
        return (
          <Line
            key={index}
            points={points}
            color="#ff6b6b"
            lineWidth={2}
            transparent
            opacity={0.3}
          />
        );
      })}
    </group>
  );
};

/**
 * Brand coherence visualization
 */
const CoherenceField: React.FC<{
  coherence: number;
  dimensions: BrandDimension[];
}> = ({ coherence, dimensions }) => {
  const fieldRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (fieldRef.current) {
      // Rotate the coherence field
      fieldRef.current.rotation.y += 0.002;
      
      // Pulse based on coherence
      const scale = 1.0 + Math.sin(state.clock.elapsedTime) * coherence * 0.1;
      fieldRef.current.scale.setScalar(scale);
    }
  });

  return (
    <Sphere ref={fieldRef} args={[8, 32, 32]}>
      <meshBasicMaterial
        color={coherence > 0.8 ? "#4CAF50" : coherence > 0.6 ? "#FFC107" : "#F44336"}
        transparent
        opacity={0.05}
        side={THREE.BackSide}
      />
    </Sphere>
  );
};

/**
 * Main Brand Universe component
 */
export const BrandUniverse3D: React.FC<BrandUniverseProps> = ({
  brandName,
  dimensions,
  gravityRules,
  metrics,
  interactive = true,
  showGravityForces = true,
  animationSpeed = 1.0
}) => {
  const [hoveredDimension, setHoveredDimension] = useState<BrandDimension | null>(null);
  const [selectedDimension, setSelectedDimension] = useState<BrandDimension | null>(null);

  // Convert dimensions to visualization format
  const visualDimensions: BrandDimension[] = Object.entries(dimensions).map(([name, data], index) => {
    const angle = (index / Object.keys(dimensions).length) * Math.PI * 2;
    const radius = 3;
    
    return {
      name,
      depth: data.depth || 0.5,
      coherence: data.coherence || 0.5,
      position: [
        Math.cos(angle) * radius,
        (data.depth - 0.5) * 2,
        Math.sin(angle) * radius
      ] as [number, number, number],
      color: getDimensionColor(name)
    };
  });

  // Convert gravity rules to visualization format
  const visualGravityRules: GravityRule[] = gravityRules.map((rule, index) => {
    const angle = (index / gravityRules.length) * Math.PI * 2 + Math.PI / 4;
    const radius = 5;
    
    return {
      name: rule.name,
      force: rule.force || 0.5,
      position: [
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius
      ] as [number, number, number],
      connections: rule.active_conditions || []
    };
  });

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 5, 10], fov: 75 }}
        style={{ background: 'linear-gradient(to bottom, #000428, #004e92)' }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.8} />
        <pointLight position={[-10, -10, -10]} intensity={0.3} color="#4CAF50" />

        {/* Brand universe elements */}
        <CoherenceField 
          coherence={metrics.world_coherence} 
          dimensions={visualDimensions} 
        />
        
        {/* Brand dimensions */}
        {visualDimensions.map((dimension) => (
          <BrandDimensionSphere
            key={dimension.name}
            dimension={dimension}
            onHover={setHoveredDimension}
            onClick={setSelectedDimension}
            interactive={interactive}
          />
        ))}
        
        {/* Gravity forces */}
        {showGravityForces && visualGravityRules.map((rule) => (
          <GravityForce
            key={rule.name}
            rule={rule}
            dimensions={visualDimensions}
            showConnections={true}
          />
        ))}
        
        {/* Brand name */}
        <Text
          position={[0, 6, 0]}
          fontSize={0.5}
          color="white"
          anchorX="center"
          anchorY="middle"
          font="/fonts/helvetiker_bold.typeface.json"
        >
          {brandName.toUpperCase()}
        </Text>
        
        {/* Coherence score */}
        <Text
          position={[0, -6, 0]}
          fontSize={0.3}
          color={metrics.world_coherence > 0.8 ? "#4CAF50" : "#FFC107"}
          anchorX="center"
          anchorY="middle"
        >
          {(metrics.world_coherence * 100).toFixed(0)}% COHERENT
        </Text>

        {/* Controls */}
        <OrbitControls
          enablePan={interactive}
          enableZoom={interactive}
          enableRotate={interactive}
          maxDistance={20}
          minDistance={5}
        />
      </Canvas>
      
      {/* Hover information panel */}
      {hoveredDimension && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '15px',
          borderRadius: '8px',
          fontFamily: 'Arial, sans-serif',
          maxWidth: '300px'
        }}>
          <h3 style={{ margin: '0 0 10px 0', textTransform: 'capitalize' }}>
            {hoveredDimension.name.replace('_', ' ')}
          </h3>
          <p style={{ margin: '5px 0' }}>
            <strong>Depth:</strong> {(hoveredDimension.depth * 100).toFixed(0)}%
          </p>
          <p style={{ margin: '5px 0' }}>
            <strong>Coherence:</strong> {(hoveredDimension.coherence * 100).toFixed(0)}%
          </p>
        </div>
      )}
      
      {/* Brand metrics panel */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        right: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '15px',
        borderRadius: '8px',
        fontFamily: 'Arial, sans-serif'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>Brand Metrics</h4>
        <p style={{ margin: '5px 0' }}>
          <strong>Coherence:</strong> {(metrics.world_coherence * 100).toFixed(0)}%
        </p>
        <p style={{ margin: '5px 0' }}>
          <strong>Attraction:</strong> {(metrics.attraction_force * 100).toFixed(0)}%
        </p>
        <p style={{ margin: '5px 0' }}>
          <strong>Dimensions:</strong> {visualDimensions.length}
        </p>
        <p style={{ margin: '5px 0' }}>
          <strong>Gravity Rules:</strong> {visualGravityRules.length}
        </p>
      </div>
    </div>
  );
};

/**
 * Helper function to get dimension-specific colors
 */
function getDimensionColor(dimensionName: string): string {
  const colorMap: Record<string, string> = {
    market_position: '#2196F3',
    value_proposition: '#4CAF50',
    brand_narrative: '#FF9800',
    emotional_landscape: '#E91E63',
    visual_identity: '#9C27B0',
    experiential_design: '#00BCD4',
    digital_presence: '#607D8B',
    innovation_capacity: '#FF5722'
  };
  
  return colorMap[dimensionName] || '#9E9E9E';
}

export default BrandUniverse3D;