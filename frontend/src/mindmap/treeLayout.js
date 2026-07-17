/**
 * Computes positions for a collapsible tree layout.
 * Returns { positions, visibleNodeIds, visibleEdgeIds }
 */
export function computeTreePositions(graph, collapsedFolders) {
  const positions = {};
  const visibleNodeIds = new Set();
  const visibleEdgeIds = new Set();

  const rootNode = graph.nodes.find(n => n.type === 'root') || graph.nodes[0];
  if (!rootNode) return { positions, visibleNodeIds, visibleEdgeIds };

  const BASE_X = 60;
  const LEVEL_WIDTH = 260;
  const BASE_Y = 50;
  const NODE_HEIGHT = 56;

  // Build parent -> children map
  const childrenMap = {};
  graph.nodes.forEach(n => {
    if (n.parent) {
      if (!childrenMap[n.parent]) childrenMap[n.parent] = [];
      childrenMap[n.parent].push(n);
    }
  });

  // Sort: dirs first, then files, alphabetically
  function sortChildren(children) {
    children.sort((a, b) => {
      const aRank = a.type === 'dir' ? 0 : 1;
      const bRank = b.type === 'dir' ? 0 : 1;
      if (aRank !== bRank) return aRank - bRank;
      return (a.label || '').localeCompare(b.label || '');
    });
  }

  let yCursor = BASE_Y;

  function walk(nodeId, depth) {
    const node = graph.nodes.find(n => n.id === nodeId);
    if (!node) return;

    const x = BASE_X + depth * LEVEL_WIDTH;
    positions[nodeId] = { x, y: yCursor };
    visibleNodeIds.add(nodeId);
    yCursor += NODE_HEIGHT;

    if (node.type !== 'file' && !collapsedFolders.has(nodeId)) {
      const children = childrenMap[nodeId] || [];
      sortChildren(children);
      children.forEach(child => walk(child.id, depth + 1));
    }
  }

  walk(rootNode.id, 0);

  // Mark edges as visible only when both endpoints are visible
  graph.edges.forEach(e => {
    if (visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)) {
      visibleEdgeIds.add(`${e.source}->${e.target}`);
    }
  });

  return { positions, visibleNodeIds, visibleEdgeIds };
}
