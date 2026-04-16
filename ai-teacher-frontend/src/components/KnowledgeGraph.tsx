import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { KnowledgePointProgress } from '../types';
import './KnowledgeGraph.css';

interface KnowledgeGraphProps {
  knowledgePoints: KnowledgePointProgress[];
  onNodeClick?: (kp: KnowledgePointProgress) => void;
  showAllLayers?: boolean;
  levelDescriptions?: Record<number, string>;
}

interface GraphNode {
  id: string;
  name: string;
  level: number;
  status: string;
  type: string;
  progress: number;
  dependencies?: string[];
  x: number;
  y: number;
  fx?: number;
  fy?: number;
}

interface LevelInfo {
  level: number;
  y: number;
  height: number;
  centerX: number;
  nodes: GraphNode[];
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  knowledgePoints,
  onNodeClick,
  showAllLayers = false,
  levelDescriptions = {},
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<KnowledgePointProgress | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const hoveredNodeIdRef = useRef<string | null>(null);

  // 递归获取所有前置依赖节点ID
  const getAllPrerequisites = (nodeId: string, links: { source: string; target: string }[]): Set<string> => {
    const prerequisites = new Set<string>();
    
    const findPrerequisites = (id: string) => {
      // 找到所有指向当前节点的连线
      const directPrereqs = links
        .filter(link => link.target === id)
        .map(link => link.source);
      
      directPrereqs.forEach(prereqId => {
        if (!prerequisites.has(prereqId)) {
          prerequisites.add(prereqId);
          // 递归查找前置依赖的前置依赖
          findPrerequisites(prereqId);
        }
      });
    };
    
    findPrerequisites(nodeId);
    return prerequisites;
  };

  useEffect(() => {
    if (!svgRef.current || !knowledgePoints || knowledgePoints.length === 0) return;

    try {
      // 清除旧内容
      d3.select(svgRef.current).selectAll('*').remove();

      const width = svgRef.current.clientWidth || 900;
      const height = 700;
      const nodeWidth = 140;
      const nodeHeight = 60;
      const levelGap = 160; // 增加层级间距
      const nodeGap = 20;
      const boxPadding = 20;
      const levelDescriptionHeight = 30; // 层级描述的高度

      // 过滤节点
      const filteredPoints = knowledgePoints.filter(kp => showAllLayers || kp.status !== 'locked');

      // 按层级分组
      const levelGroups = new Map<number, KnowledgePointProgress[]>();
      filteredPoints.forEach(kp => {
        if (!levelGroups.has(kp.level)) {
          levelGroups.set(kp.level, []);
        }
        levelGroups.get(kp.level)!.push(kp);
      });

      // 按层级排序
      const levels = Array.from(levelGroups.keys()).sort((a, b) => a - b);

      // 为每个层级和节点计算位置
      const levelInfos: LevelInfo[] = [];
      const nodes: GraphNode[] = [];

      levels.forEach((level, levelIndex) => {
        const kpsInLevel = levelGroups.get(level)!;
        const y = 100 + levelIndex * levelGap + levelDescriptionHeight/2; // 增加层级描述高度的偏移
        
        // 计算该层级所需的总宽度
        const totalWidth = kpsInLevel.length * nodeWidth + (kpsInLevel.length - 1) * nodeGap;
        const startX = (width - totalWidth) / 2;

        const levelNodes: GraphNode[] = [];
        kpsInLevel.forEach((kp, index) => {
          const x = startX + index * (nodeWidth + nodeGap) + nodeWidth / 2;
          const node: GraphNode = {
            id: kp.id,
            name: kp.name,
            level: kp.level,
            status: kp.status,
            type: kp.type,
            progress: kp.progress,
            dependencies: kp.dependencies,
            x: x,
            y: y,
            fx: x,
            fy: y,
          };
          nodes.push(node);
          levelNodes.push(node);
        });

        levelInfos.push({
          level,
          y: y - nodeHeight/2 - boxPadding - levelDescriptionHeight,
          height: nodeHeight + boxPadding * 2 + levelDescriptionHeight,
          centerX: width / 2,
          nodes: levelNodes,
        });
      });

      // 创建 SVG
      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      // 添加缩放功能
      const g = svg.append('g');

      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.5, 2])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });

      svg.call(zoom);

      // 绘制层级框
      levelInfos.forEach((levelInfo, index) => {
        // 计算框的位置
        const minX = Math.min(...levelInfo.nodes.map(n => n.x)) - nodeWidth/2 - boxPadding;
        const maxX = Math.max(...levelInfo.nodes.map(n => n.x)) + nodeWidth/2 + boxPadding;
        const boxWidth = maxX - minX;

        // 添加层级背景框
        g.append('rect')
          .attr('class', 'level-box')
          .attr('x', minX)
          .attr('y', levelInfo.y)
          .attr('width', boxWidth)
          .attr('height', levelInfo.height)
          .attr('rx', 16)
          .attr('ry', 16);

        // 添加层级标签
        g.append('text')
          .attr('class', 'level-label')
          .attr('x', minX - 10)
          .attr('y', levelInfo.y + levelInfo.height / 2 + 5)
          .attr('text-anchor', 'end')
          .text(`L${index + 1}`);

        // 添加层级描述
        const levelDesc = levelDescriptions[levelInfo.level] || `Level ${index + 1}`;
        g.append('text')
          .attr('class', 'level-description')
          .attr('x', minX + boxWidth / 2)
          .attr('y', levelInfo.y + 20)
          .attr('text-anchor', 'middle')
          .text(levelDesc);

        // 绘制层级间的连接线
        if (index < levelInfos.length - 1) {
          g.append('line')
            .attr('class', 'level-connector')
            .attr('x1', levelInfo.centerX)
            .attr('y1', levelInfo.y + levelInfo.height)
            .attr('x2', levelInfo.centerX)
            .attr('y2', levelInfos[index + 1].y);
        }
      });

      // 准备依赖连线数据
      const dependencyLinks: { source: string; target: string }[] = [];
      knowledgePoints.forEach(kp => {
        if (kp.dependencies && kp.dependencies.length > 0) {
          kp.dependencies.forEach(depId => {
            if (nodes.find(n => n.id === depId) && nodes.find(n => n.id === kp.id)) {
              dependencyLinks.push({ source: depId, target: kp.id });
            }
          });
        }
      });

      // 创建依赖连线组（默认隐藏）
      const dependencyGroup = g.append('g').attr('class', 'dependency-links');
      
      const dependencyPaths = dependencyGroup.selectAll('path')
        .data(dependencyLinks)
        .enter()
        .append('path')
        .attr('class', d => {
          const targetNode = nodes.find(n => n.id === d.target);
          if (targetNode?.status === 'completed') return 'dependency-link completed';
          if (targetNode?.status === 'current' || targetNode?.status === 'in_progress') return 'dependency-link active';
          return 'dependency-link';
        })
        .attr('d', d => {
          const source = nodes.find(n => n.id === d.source);
          const target = nodes.find(n => n.id === d.target);
          if (!source || !target) return '';

          const dy = target.y - source.y;
          // 使用贝塞尔曲线
          return `M${source.x},${source.y + nodeHeight/2}Q${source.x},${source.y + dy/2} ${target.x},${target.y - nodeHeight/2}`;
        })
        .style('opacity', 0); // 默认隐藏

      // 绘制节点组
      const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node-group')
        .attr('transform', d => `translate(${d.x},${d.y})`)
        .on('click', (event, d) => {
          event.stopPropagation();
          
          // 切换选中状态
          const newSelectedId = selectedNode === d.id ? null : d.id;
          setSelectedNode(newSelectedId);

          // 显示/隐藏依赖连线（显示所有前置依赖链）
          const allPrereqIds = newSelectedId ? getAllPrerequisites(newSelectedId, dependencyLinks) : new Set<string>();
          
          dependencyPaths.style('opacity', function(linkData) {
            if (!newSelectedId) return 0;
            
            const sourceId = linkData.source;
            const targetId = linkData.target;
            
            // 显示所有前置依赖链中的连线
            if (targetId === newSelectedId || allPrereqIds.has(targetId)) {
              return 1;
            }
            return 0;
          });

          // 高亮所有前置依赖节点
          node.selectAll('.node-rect')
            .style('opacity', function(nodeData: unknown) {
              const data = nodeData as GraphNode;
              if (!newSelectedId) return 1;
              if (data.id === newSelectedId) return 1;

              // 高亮所有前置依赖节点（包括间接依赖）
              return allPrereqIds.has(data.id) ? 1 : 0.3;
            });

          const kp = knowledgePoints.find(k => k.id === d.id);
          if (kp && kp.status !== 'locked' && onNodeClick) {
            onNodeClick(kp);
          }
        })
        .on('mouseenter', (event, d) => {
          // 更新悬浮节点ID
          hoveredNodeIdRef.current = d.id;
          
          // 如果没有选中节点，悬浮时显示所有前置依赖连线
          if (!selectedNode) {
            const allPrereqIds = getAllPrerequisites(d.id, dependencyLinks);
            
            dependencyPaths.style('opacity', function(linkData) {
              const targetId = linkData.target;
              
              // 显示所有前置依赖链中的连线
              if (targetId === d.id || allPrereqIds.has(targetId)) {
                return 1;
              }
              return 0;
            });

            // 高亮所有前置依赖节点
            node.selectAll('.node-rect')
              .style('opacity', function(nodeData: unknown) {
                const data = nodeData as GraphNode;
                if (data.id === d.id) return 1;

                // 高亮所有前置依赖节点（包括间接依赖）
                return allPrereqIds.has(data.id) ? 1 : 0.3;
              });
          }

          const kp = knowledgePoints.find(k => k.id === d.id);
          if (kp) {
            setHoveredNode(kp);
            setTooltipPos({ x: event.clientX, y: event.clientY });
          }
        })
        .on('mouseleave', () => {
          // 清除悬浮节点ID
          hoveredNodeIdRef.current = null;
          
          // 如果没有选中节点，离开时隐藏依赖连线
          if (!selectedNode) {
            dependencyPaths.style('opacity', 0);
            node.selectAll('.node-rect').style('opacity', 1);
          }

          setHoveredNode(null);
        });

      // 添加节点背景矩形
      node.append('rect')
        .attr('class', d => `node-rect ${d.status}`)
        .attr('width', nodeWidth)
        .attr('height', nodeHeight)
        .attr('x', -nodeWidth/2)
        .attr('y', -nodeHeight/2)
        .attr('rx', 12)
        .attr('ry', 12);

      // 添加节点名称
      node.append('text')
        .attr('class', 'node-name')
        .attr('text-anchor', 'middle')
        .attr('dy', '-5')
        .text(d => d.name.length > 8 ? d.name.substring(0, 8) + '...' : d.name);

      // 添加节点状态
      node.append('text')
        .attr('class', d => `node-status ${d.status}`)
        .attr('text-anchor', 'middle')
        .attr('dy', '15')
        .text(d => {
          if (d.status === 'completed') return '✓ 已掌握';
          if (d.status === 'current') return '◉ 进行中';
          if (d.status === 'in_progress') return '◐ 学习中';
          return '○ 未解锁';
        });

      // 点击空白处取消选中
      svg.on('click', () => {
        setSelectedNode(null);
        dependencyPaths.style('opacity', 0);
        node.selectAll('.node-rect').style('opacity', 1);
      });

    } catch (error) {
      console.error('初始化知识图谱失败:', error);
    }
  }, [knowledgePoints, showAllLayers]);

  return (
    <div className="knowledge-graph-wrapper">
      {!knowledgePoints || knowledgePoints.length === 0 ? (
        <div className="knowledge-graph-empty">
          <div className="empty-icon">📊</div>
          <div className="empty-text">暂无知识点数据</div>
        </div>
      ) : (
        <svg ref={svgRef} className="knowledge-graph-svg" />
      )}
      
      {/* 悬停提示框 */}
      {hoveredNode && (
        <div
          className="graph-tooltip"
          style={{
            left: tooltipPos.x + 15,
            top: tooltipPos.y + 15,
          }}
        >
          <div className="tooltip-header">
            <h4>{hoveredNode.name}</h4>
            <span className={`tooltip-status ${hoveredNode.status}`}>
              {hoveredNode.status === 'completed' ? '已掌握' : 
               hoveredNode.status === 'current' ? '进行中' : 
               hoveredNode.status === 'in_progress' ? '学习中' : '未解锁'}
            </span>
          </div>
          <div className="tooltip-body">
            <div className="tooltip-row">
              <span className="tooltip-label">类型：</span>
              <span className="tooltip-value">{hoveredNode.type}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">进度：</span>
              <span className="tooltip-value">{hoveredNode.progress}%</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">层级：</span>
              <span className="tooltip-value">L{hoveredNode.level}</span>
            </div>
            {hoveredNode.dependencies && hoveredNode.dependencies.length > 0 && (
              <div className="tooltip-row">
                <span className="tooltip-label">前置：</span>
                <span className="tooltip-value">{hoveredNode.dependencies.length} 个知识点</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;
