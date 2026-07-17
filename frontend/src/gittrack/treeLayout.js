/**
 * Computes tree layout positions for a git commit history graph.
 * Returns { laneMap, nodePositions }
 */
export function computeGitPositions(commits, customPositions = {}) {
  const laneMap = {};
  const nodePositions = {};
  if (!commits || !Array.isArray(commits) || commits.length === 0) {
    return { laneMap, nodePositions };
  }

  const reversed = [...commits].reverse();
  const occupied = new Set();

  function nextFree(start) {
    let lane = start;
    while (occupied.has(lane)) lane++;
    return lane;
  }

  reversed.forEach(commit => {
    const hash = commit.hash_short;
    const parents = commit.parents_short || [];

    let lane;
    if (parents.length === 0) {
      lane = nextFree(0);
    } else {
      const firstParent = parents[0];
      lane = laneMap[firstParent] !== undefined ? laneMap[firstParent] : nextFree(0);
    }

    laneMap[hash] = lane;
    occupied.add(lane);

    parents.forEach((p, i) => {
      if (laneMap[p] === undefined) {
        laneMap[p] = i === 0 ? lane : nextFree(lane + 1);
        if (i !== 0) occupied.add(laneMap[p]);
      }
    });
  });

  const BASE_X = 70;
  const LANE_WIDTH = 36;
  const NODE_Y_START = 50;
  const NODE_Y_STEP = 54;

  commits.forEach((commit, i) => {
    const hash = commit.hash_short;
    const lane = laneMap[hash] || 0;
    const saved = customPositions[hash];
    nodePositions[hash] = saved
      ? { x: saved.x, y: saved.y }
      : { x: BASE_X + lane * LANE_WIDTH, y: NODE_Y_START + i * NODE_Y_STEP };
  });

  return { laneMap, nodePositions };
}
