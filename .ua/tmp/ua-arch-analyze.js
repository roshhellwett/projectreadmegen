const fs = require('fs');

// ─── Read input ───────────────────────────────────────────────────────────────
const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
  console.error('Usage: node ua-arch-analyze.js <input.json> <output.json>');
  process.exit(1);
}

let input;
try {
  input = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
} catch (e) {
  console.error(`Failed to read input: ${e.message}`);
  process.exit(1);
}

const { fileNodes, importEdges, allEdges } = input;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getNode(id) {
  return fileNodes.find(n => n.id === id);
}

function getFilePath(id) {
  const n = getNode(id);
  return n ? n.filePath || n.filePath || '' : '';
}

function getNodeType(id) {
  const n = getNode(id);
  return n ? n.type || 'file' : 'file';
}

// ─── A. Directory Grouping ────────────────────────────────────────────────────
// Compute common path prefix
let allPaths = fileNodes.map(n => (n.filePath || n.filePath || '').replace(/\\/g, '/'));
const commonPrefix = findCommonPrefix(allPaths);
const prefixLen = commonPrefix.length;

function findCommonPrefix(paths) {
  if (paths.length === 0) return '';
  let prefix = paths[0];
  for (let i = 1; i < paths.length; i++) {
    while (paths[i].indexOf(prefix) !== 0) {
      prefix = prefix.substring(0, prefix.length - 1);
      if (prefix === '') return '';
    }
  }
  return prefix;
}

// Group by first directory segment after common prefix
const directoryGroups = {};
const flatFiles = [];

for (const node of fileNodes) {
  let p = (node.filePath || '').replace(/\\/g, '/');
  let relativePath = p.substring(prefixLen);
  if (relativePath.startsWith('/')) relativePath = relativePath.substring(1);

  const parts = relativePath.split('/');
  let group;

  if (parts.length >= 2 && parts[0] !== '') {
    group = parts[0]; // first directory segment
  } else if (parts.length === 1 && parts[0] !== '') {
    // File in root of common prefix
    group = 'root';
  } else {
    group = 'root';
  }

  // Special handling: if the path starts with src/projectreadmegen we already have src grouping
  // But actually, let's keep it simple
  if (group === 'src') {
    // second segment for src/... files
    if (parts.length >= 3) {
      group = parts[1]; // e.g. src/projectreadmegen -> projectreadmegen
    } else if (parts.length === 2) {
      group = parts[0];
    }
  }

  // Handle tests subdirs: tests/unit, tests/smoke, tests/e2e, tests (root)
  if (group === 'tests' && parts.length >= 3) {
    group = 'tests-' + parts[1]; // tests-unit, tests-smoke, tests-e2e
  }

  if (!directoryGroups[group]) {
    directoryGroups[group] = [];
  }
  directoryGroups[group].push(node.id);
}

// B. Node Type Grouping
const nodeTypeGroups = {};
for (const node of fileNodes) {
  const type = node.type || 'file';
  if (!nodeTypeGroups[type]) nodeTypeGroups[type] = [];
  nodeTypeGroups[type].push(node.id);
}

// C. Import Adjacency Matrix
const fanOut = {};
const fanIn = {};
const adjImports = {}; // source -> targets

for (const node of fileNodes) {
  fanOut[node.id] = 0;
  fanIn[node.id] = 0;
  adjImports[node.id] = [];
}

for (const edge of importEdges) {
  if (!fanOut[edge.source]) fanOut[edge.source] = 0;
  if (!fanIn[edge.target]) fanIn[edge.target] = 0;
  fanOut[edge.source]++;
  fanIn[edge.target]++;
  adjImports[edge.source].push(edge.target);
}

// Group-level imports
function getGroup(id) {
  let p = (getFilePath(id) || '').replace(/\\/g, '/');
  if (!p) return 'root';
  let relativePath = p.substring(prefixLen);
  if (relativePath.startsWith('/')) relativePath = relativePath.substring(1);
  const parts = relativePath.split('/');
  if (parts.length >= 2 && parts[0] !== '') return parts[0];
  return 'root';
}

const interGroupImports = {};
const intraGroupCounts = {};
const groupTotalEdges = {};

for (const edge of importEdges) {
  const srcGroup = getGroup(edge.source);
  const tgtGroup = getGroup(edge.target);

  if (!interGroupImports[srcGroup]) interGroupImports[srcGroup] = {};
  if (!interGroupImports[srcGroup][tgtGroup]) interGroupImports[srcGroup][tgtGroup] = 0;
  interGroupImports[srcGroup][tgtGroup]++;

  if (!groupTotalEdges[srcGroup]) groupTotalEdges[srcGroup] = 0;
  groupTotalEdges[srcGroup]++;

  if (srcGroup === tgtGroup) {
    if (!intraGroupCounts[srcGroup]) intraGroupCounts[srcGroup] = 0;
    intraGroupCounts[srcGroup]++;
  }
}

// Format interGroupImports as array
const interGroupImportsArr = [];
for (const [from, toMap] of Object.entries(interGroupImports)) {
  for (const [to, count] of Object.entries(toMap)) {
    interGroupImportsArr.push({ from, to, count });
  }
}

// E. Inter-Group Import Frequency (same as above, already computed)
// F. Intra-Group Import Density
const intraGroupDensity = {};
for (const [group, nodes] of Object.entries(directoryGroups)) {
  const internalEdges = intraGroupCounts[group] || 0;
  const totalEdges = groupTotalEdges[group] || 0;
  intraGroupDensity[group] = {
    internalEdges,
    totalEdges,
    density: totalEdges > 0 ? internalEdges / totalEdges : 0
  };
}

// G. Directory Pattern Matching
const patternMap = {
  'routes': 'api', 'api': 'api', 'controllers': 'api', 'endpoints': 'api', 'handlers': 'api',
  'services': 'service', 'core': 'service', 'domain': 'service', 'logic': 'service',
  'models': 'data', 'db': 'data', 'data': 'data', 'persistence': 'data', 'repository': 'data', 'entities': 'data',
  'migrations': 'data', 'sql': 'data', 'database': 'data', 'schema': 'data',
  'components': 'ui', 'views': 'ui', 'pages': 'ui', 'ui': 'ui', 'layouts': 'ui', 'screens': 'ui',
  'middleware': 'middleware', 'plugins': 'middleware',
  'utils': 'utility', 'helpers': 'utility', 'common': 'utility', 'shared': 'utility', 'tools': 'utility',
  'pkg': 'utility', 'templatetags': 'utility',
  'config': 'config', 'constants': 'config', 'env': 'config', 'settings': 'config',
  'tests': 'test', 'test': 'test', 'spec': 'test', '__tests__': 'test',
  'types': 'types', 'interfaces': 'types', 'schemas': 'types', 'contracts': 'types', 'dtos': 'types',
  'dto': 'types', 'request': 'types', 'response': 'types',
  'hooks': 'hooks',
  'store': 'state', 'state': 'state', 'reducers': 'state', 'actions': 'state', 'slices': 'state',
  'assets': 'assets', 'static': 'assets', 'public': 'assets',
  'management': 'config', 'commands': 'config',
  'signals': 'service', 'composables': 'service', 'mailers': 'service', 'jobs': 'service', 'channels': 'service',
  'serializers': 'api',
  'cmd': 'entry', 'bin': 'entry', 'entry': 'entry',
  'internal': 'service',
  'controller': 'api', 'routers': 'api', 'blueprints': 'api',
  'docs': 'documentation', 'documentation': 'documentation', 'wiki': 'documentation',
  'deploy': 'infrastructure', 'deployment': 'infrastructure', 'infra': 'infrastructure', 'infrastructure': 'infrastructure',
  'k8s': 'infrastructure', 'kubernetes': 'infrastructure', 'helm': 'infrastructure', 'charts': 'infrastructure',
  'terraform': 'infrastructure', 'tf': 'infrastructure', 'docker': 'infrastructure',
  '.github': 'ci-cd', '.gitlab': 'ci-cd', '.circleci': 'ci-cd',
  'frontend': 'ui',
  'projectreadmegen': 'service',
  'smoke': 'test', 'unit': 'test', 'e2e': 'test',
  'tests-unit': 'test', 'tests-smoke': 'test', 'tests-e2e': 'test',
  'examples': 'test',
  'Sample': 'assets',
  'root': 'config',
  'templates': 'ui',
  'public': 'assets',
  'dist': 'assets',
};

const patternMatches = {};
const overridePatterns = {};

// File-level pattern matching
for (const node of fileNodes) {
  const name = node.name || '';
  const fpath = (node.filePath || '').replace(/\\/g, '/');

  // Test files
  if (name.includes('test_') || name.includes('_test') || name.endsWith('Test.java') || name.endsWith('Tests.cs')) {
    if (name.endsWith('.py') || name.endsWith('.js') || name.endsWith('.ts')) {
      if (fpath.includes('/tests/') || fpath.includes('/test/')) {
        overridePatterns[node.id] = 'test';
      }
    }
  }

  // Entry points
  if (name === '__main__.py' || name === 'main.py') {
    overridePatterns[node.id] = 'entry';
  }

  // Config files
  if (name === 'pyproject.toml' || name === 'requirements.txt' || name === 'MANIFEST.in' ||
      name === '.gitignore' || name === 'readmegen.config.json' || name === 'vite.config.js' ||
      name === 'package.json' || name === 'tsconfig.json') {
    overridePatterns[node.id] = 'config';
  }

  // Documentation
  if (name === 'readme.md' || name === 'contributing.md' || name === 'security.md' || name === 'license' ||
      name === 'README.md' || name === 'README_old.txt' || name === 'TEST_README.md' ||
      name === 'TEST_INTERACTIVE.md') {
    overridePatterns[node.id] = 'documentation';
  }

  // Jinja2 templates
  if (name.endsWith('.j2')) {
    overridePatterns[node.id] = 'ui';
  }
}

// Match groups
for (const [group, nodes] of Object.entries(directoryGroups)) {
  patternMatches[group] = patternMap[group] || 'other';
}

// H. Deployment Topology Detection
const infraFiles = [];
let hasDockerfile = false;
let hasCompose = false;
let hasK8s = false;
let hasTerraform = false;
let hasCI = false;

for (const node of fileNodes) {
  const name = node.name || '';
  const fpath = (node.filePath || '').replace(/\\/g, '/');

  if (name === 'Dockerfile' || name.startsWith('Dockerfile.')) {
    hasDockerfile = true;
    infraFiles.push(fpath);
  }
  if (name.startsWith('docker-compose')) {
    hasCompose = true;
    infraFiles.push(fpath);
  }
  if (name.endsWith('.k8s.yaml') || name.endsWith('.k8s.yml') || name.endsWith('.yaml') && fpath.includes('/k8s/')) {
    hasK8s = true;
    infraFiles.push(fpath);
  }
  if (name.endsWith('.tf') || name.endsWith('.tfvars')) {
    hasTerraform = true;
    infraFiles.push(fpath);
  }
  if (fpath.includes('.github/workflows') || name === '.gitlab-ci.yml' || name === 'Jenkinsfile') {
    hasCI = true;
    infraFiles.push(fpath);
  }
}

// I. Data Pipeline Detection
const schemaFiles = [];
const migrationFiles = [];
const dataModelFiles = [];
const apiHandlerFiles = [];

for (const node of fileNodes) {
  const name = node.name || '';
  const fpath = (node.filePath || '').replace(/\\/g, '/');

  if (name.endsWith('.sql') || name.endsWith('.graphql') || name.endsWith('.proto') || name.endsWith('.prisma')) {
    schemaFiles.push(fpath);
  }
  if (fpath.includes('/migrations/') || name.startsWith('migration_')) {
    migrationFiles.push(fpath);
  }
}

// J. Documentation Coverage
function getGroupForNode(nodeId) {
  const p = (getFilePath(nodeId) || '').replace(/\\/g, '/');
  if (!p) return 'root';
  let relativePath = p.substring(prefixLen);
  if (relativePath.startsWith('/')) relativePath = relativePath.substring(1);
  const parts = relativePath.split('/');
  if (parts.length >= 2 && parts[0] !== '') return parts[0];
  return 'root';
}

const groupsWithDocs = new Set();
const totalGroups = Object.keys(directoryGroups).length;
const groupDocFiles = {};

for (const node of fileNodes) {
  const name = node.name || '';
  const g = getGroupForNode(node.id);

  if (!groupDocFiles[g]) groupDocFiles[g] = [];
  if (name.toLowerCase() === 'readme.md' || name.toLowerCase() === 'readme' || name.endsWith('.md') || name === 'license') {
    groupDocFiles[g].push(node.id);
  }
}

for (const [g, docs] of Object.entries(groupDocFiles)) {
  if (docs.length > 0) groupsWithDocs.add(g);
}

const undocumentedGroups = Object.keys(directoryGroups).filter(g => !groupsWithDocs.has(g));

// K. Dependency Direction
const dependencyDirection = [];
const findDependencyDirection = () => {
  // Calculate net dependency between groups
  const netDeps = {};
  for (const item of interGroupImportsArr) {
    const key = [item.from, item.to].sort().join('->');
    if (!netDeps[key]) netDeps[key] = { a: item.from, b: item.to, aToB: 0, bToA: 0 };
    netDeps[key].aToB += item.count;
  }
  // Also check reverse direction
  for (const item of interGroupImportsArr) {
    const key = [item.from, item.to].sort().join('->');
    if (item.from === netDeps[key].b) {
      netDeps[key].bToA += item.count;
    }
  }
  for (const [, dep] of Object.entries(netDeps)) {
    if (dep.aToB > dep.bToA) {
      dependencyDirection.push({ dependent: dep.a, dependsOn: dep.b });
    } else if (dep.bToA > dep.aToB) {
      dependencyDirection.push({ dependent: dep.b, dependsOn: dep.a });
    }
    // If equal, skip
  }
};
findDependencyDirection();

// File stats
const fileFanIn = {};
const fileFanOut = {};
for (const [id, count] of Object.entries(fanIn)) {
  if (count > 0) fileFanIn[id] = count;
}
for (const [id, count] of Object.entries(fanOut)) {
  if (count > 0) fileFanOut[id] = count;
}

// Cross Category Edges
const crossCategoryEdges = [];
const catEdgeCounts = {};
for (const edge of allEdges) {
  const srcType = getNodeType(edge.source);
  const tgtType = getNodeType(edge.target);
  const key = `${srcType}->${tgtType}:${edge.type}`;
  if (!catEdgeCounts[key]) catEdgeCounts[key] = { fromType: srcType, toType: tgtType, edgeType: edge.type, count: 0 };
  catEdgeCounts[key].count++;
}
for (const item of Object.values(catEdgeCounts)) {
  crossCategoryEdges.push(item);
}

// Sort fan-in/fan-out by count
const sortedFanIn = Object.entries(fileFanIn).sort((a, b) => b[1] - a[1]).slice(0, 20);
const sortedFanOut = Object.entries(fileFanOut).sort((a, b) => b[1] - a[1]).slice(0, 20);

const result = {
  scriptCompleted: true,
  directoryGroups,
  nodeTypeGroups,
  crossCategoryEdges,
  interGroupImports: interGroupImportsArr,
  intraGroupDensity,
  patternMatches,
  deploymentTopology: {
    hasDockerfile,
    hasCompose,
    hasK8s,
    hasTerraform,
    hasCI,
    infraFiles
  },
  dataPipeline: {
    schemaFiles,
    migrationFiles,
    dataModelFiles,
    apiHandlerFiles
  },
  docCoverage: {
    groupsWithDocs: groupsWithDocs.size,
    totalGroups,
    coverageRatio: totalGroups > 0 ? groupsWithDocs.size / totalGroups : 0,
    undocumentedGroups
  },
  dependencyDirection,
  fileStats: {
    totalFileNodes: fileNodes.length,
    filesPerGroup: Object.fromEntries(Object.entries(directoryGroups).map(([k, v]) => [k, v.length])),
    nodeTypeCounts: Object.fromEntries(Object.entries(nodeTypeGroups).map(([k, v]) => [k, v.length]))
  },
  fileFanIn: Object.fromEntries(sortedFanIn),
  fileFanOut: Object.fromEntries(sortedFanOut)
};

try {
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf-8');
  console.log('Analysis complete. Results written to', outputPath);
  process.exit(0);
} catch (e) {
  console.error(`Failed to write output: ${e.message}`);
  process.exit(1);
}
