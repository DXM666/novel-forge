import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

/**
 * 知识图谱可视化组件
 * @param {Object} props
 * @param {Array} props.elements - Cytoscape 元素数组（nodes/edges）
 */
const KnowledgeGraphView = ({ elements }) => {
  const cyRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (cyRef.current) {
      cyRef.current.destroy();
    }
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#6366f1',
            'label': 'data(label)',
            'color': '#fff',
            'text-valign': 'center',
            'text-outline-width': 2,
            'text-outline-color': '#6366f1',
            'font-size': 14,
            'width': 36,
            'height': 36
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#a5b4fc',
            'target-arrow-color': '#a5b4fc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': 12,
            'color': '#6366f1',
            'text-background-color': '#fff',
            'text-background-opacity': 0.7,
            'text-background-padding': 2
          }
        }
      ],
      layout: { name: 'cose', animate: false }
    });
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [elements]);

  return (
    <div className="w-full h-80 bg-indigo-50 rounded shadow-inner mt-2" ref={containerRef}></div>
  );
};

export default KnowledgeGraphView;
