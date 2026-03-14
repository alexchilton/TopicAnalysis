import { useEffect, useRef, useState } from 'react';
import type { TopicGraph, TopicCluster } from '../../types';

interface ForceGraphProps {
  graph: TopicGraph;
  width?: number;
  height?: number;
  onNodeClick?: (topic: TopicCluster) => void;
}

interface SimNode extends TopicCluster {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface SimLink {
  source: SimNode;
  target: SimNode;
  weight: number;
}

export function ForceGraph({ graph, width = 600, height = 400, onNodeClick }: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<SimNode[]>([]);
  const [links, setLinks] = useState<SimLink[]>([]);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (!graph.nodes.length) return;

    const simNodes: SimNode[] = graph.nodes
      .filter((n) => n.topic_id !== -1)
      .map((n) => ({
        ...n,
        x: width / 2 + (Math.random() - 0.5) * 200,
        y: height / 2 + (Math.random() - 0.5) * 200,
        vx: 0,
        vy: 0,
      }));

    const nodeMap = new Map(simNodes.map((n) => [n.topic_id, n]));
    const simLinks: SimLink[] = graph.links
      .filter((l) => nodeMap.has(l.source) && nodeMap.has(l.target))
      .map((l) => ({
        source: nodeMap.get(l.source)!,
        target: nodeMap.get(l.target)!,
        weight: l.weight,
      }));

    // Simple force simulation
    const alpha = { value: 1 };
    const centerX = width / 2;
    const centerY = height / 2;

    function tick() {
      if (alpha.value < 0.001) return;
      alpha.value *= 0.99;

      // Repulsion
      for (let i = 0; i < simNodes.length; i++) {
        for (let j = i + 1; j < simNodes.length; j++) {
          const a = simNodes[i]!;
          const b = simNodes[j]!;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (500 * alpha.value) / (dist * dist);
          a.vx -= (dx / dist) * force;
          a.vy -= (dy / dist) * force;
          b.vx += (dx / dist) * force;
          b.vy += (dy / dist) * force;
        }
      }

      // Attraction (links)
      for (const link of simLinks) {
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * 0.01 * alpha.value * link.weight;
        link.source.vx += (dx / dist) * force;
        link.source.vy += (dy / dist) * force;
        link.target.vx -= (dx / dist) * force;
        link.target.vy -= (dy / dist) * force;
      }

      // Center gravity
      for (const node of simNodes) {
        node.vx += (centerX - node.x) * 0.01 * alpha.value;
        node.vy += (centerY - node.y) * 0.01 * alpha.value;
        node.vx *= 0.9;
        node.vy *= 0.9;
        node.x += node.vx;
        node.y += node.vy;
      }

      setNodes([...simNodes]);
      setLinks([...simLinks]);
      animRef.current = requestAnimationFrame(tick);
    }

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [graph, width, height]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((prev) => ({
      ...prev,
      k: Math.max(0.2, Math.min(3, prev.k * scaleFactor)),
    }));
  };

  const getNodeRadius = (size: number) => Math.max(8, Math.min(30, Math.sqrt(size) * 3));

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.6) return 'var(--success)';
    if (sentiment < 0.4) return 'var(--danger)';
    return 'var(--warning)';
  };

  if (!graph.nodes.length || nodes.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No topic graph data available
      </div>
    );
  }

  return (
    <svg
      ref={svgRef}
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      onWheel={handleWheel}
      style={{ cursor: 'grab' }}
      role="img"
      aria-label="Topic cluster force-directed graph"
    >
      <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
        {/* Links */}
        {links.map((link, i) => (
          <line
            key={`link-${i}`}
            x1={link.source.x}
            y1={link.source.y}
            x2={link.target.x}
            y2={link.target.y}
            stroke="var(--border)"
            strokeWidth={Math.max(1, link.weight * 3)}
            strokeOpacity={0.4}
          />
        ))}

        {/* Nodes */}
        {nodes.map((node) => {
          const r = getNodeRadius(node.size);
          const isHovered = hoveredNode === node.topic_id;

          return (
            <g key={node.topic_id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={r}
                fill={getSentimentColor(node.avg_sentiment)}
                fillOpacity={isHovered ? 1 : 0.7}
                stroke={isHovered ? 'var(--text-primary)' : 'var(--bg-card)'}
                strokeWidth={isHovered ? 2 : 1}
                onMouseEnter={() => setHoveredNode(node.topic_id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => onNodeClick?.(node)}
                style={{ cursor: 'pointer', transition: 'fill-opacity 0.2s' }}
                role="button"
                tabIndex={0}
                aria-label={`Topic: ${node.label}, Size: ${node.size}`}
              />
              {(isHovered || node.size > 20) && (
                <text
                  x={node.x}
                  y={node.y + r + 14}
                  textAnchor="middle"
                  fill="var(--text-secondary)"
                  fontSize={10}
                  fontWeight={isHovered ? 600 : 400}
                >
                  {node.label.length > 20 ? node.label.slice(0, 20) + '…' : node.label}
                </text>
              )}
              {isHovered && (
                <text
                  x={node.x}
                  y={node.y + r + 26}
                  textAnchor="middle"
                  fill="var(--text-muted)"
                  fontSize={9}
                >
                  {node.size} entries • sentiment: {node.avg_sentiment.toFixed(2)}
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
}
