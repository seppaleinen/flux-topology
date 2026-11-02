"""HTML renderer for visualization.

Creates a self-contained single-file HTML with vis-network inlined.
Uses the second-brain inlining pattern: template with __PAYLOAD__ token,
JSON payload embedded as JSON.parse("...") with < escaped to \u003c.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

# The vis-network JavaScript code (vendored)
_VIS_NETWORK_JS = None

# The CSS styles
_VIS_NETWORK_CSS = None


def _load_vis_network_js() -> str:
    """Load the vendored vis-network JavaScript.

    Raises FileNotFoundError if the asset is not present (fail-fast).
    """
    global _VIS_NETWORK_JS
    if _VIS_NETWORK_JS is not None:
        return _VIS_NETWORK_JS

    # Try to load from package data
    try:
        # Python 3.9+ importlib.resources
        with resources.files("flux_topology.viz.assets").joinpath(
            "vis-network.min.js"
        ).open("r", encoding="utf-8") as f:
            _VIS_NETWORK_JS = f.read()
    except (FileNotFoundError, AttributeError):
        # Fallback for older Python or packaging issues
        asset_path = Path(__file__).parent / "assets" / "vis-network.min.js"
        if asset_path.exists():
            _VIS_NETWORK_JS = asset_path.read_text(encoding="utf-8")
        else:
            raise FileNotFoundError(
                "vis-network.min.js not found in package data. "
                'Install the visualization extra: pip install "flux-topology[render]"'
            )

    if _VIS_NETWORK_JS is None:
        raise FileNotFoundError(
            "vis-network.min.js not found in package data. "
            'Install the visualization extra: pip install "flux-topology[render]"'
        )

    return _VIS_NETWORK_JS


def _load_vis_network_css() -> str:
    """Load the vendored vis-network CSS."""
    global _VIS_NETWORK_CSS
    if _VIS_NETWORK_CSS is not None:
        return _VIS_NETWORK_CSS

    try:
        with resources.files("flux_topology.viz.assets").joinpath(
            "vis-network.min.css"
        ).open("r", encoding="utf-8") as f:
            _VIS_NETWORK_CSS = f.read()
    except (FileNotFoundError, AttributeError):
        asset_path = Path(__file__).parent / "assets" / "vis-network.min.css"
        if asset_path.exists():
            _VIS_NETWORK_CSS = asset_path.read_text(encoding="utf-8")
        else:
            _VIS_NETWORK_CSS = ""  # CSS is optional, JS is required

    return _VIS_NETWORK_CSS or ""


def _escape_json_string(s: str) -> str:
    """Escape a string for safe embedding in JSON.parse().

    Escapes < as \\u003c to prevent script tag breakout.
    """
    # First, JSON-encode the string
    encoded = json.dumps(s)
    # Then escape < to prevent script tag breakout
    escaped = encoded.replace("<", "\\u003c")
    return escaped


def _build_domain_options(sorted_domains: list[str]) -> str:
    """Build the HTML for domain selector options."""
    options = []
    options.append('                <option value="">All Domains</option>\n')
    for d in sorted_domains:
        options.append(f'                <option value="{d}">{d}</option>\n')
    return "".join(options)


def _build_js_code(vis_network_js: str, nodes_json: str, edges_json: str) -> str:
    """Build the JavaScript code for the visualization."""
    return f"""
{vis_network_js}

// Data payload
const nodesData = JSON.parse("{nodes_json}");
const edgesData = JSON.parse("{edges_json}");

// Create network
const container = document.getElementById('network');
const nodes = new vis.DataSet(nodesData);
const edges = new vis.DataSet(edgesData);

// Network options
const options = {{
    physics: {{
        enabled: true,
        solver: 'forceAtlas2Based',
        stabilization: {{ iterations: 150 }}
    }},
    nodes: {{
        shape: 'dot',
        size: 20,
        font: {{ size: 12, color: '#fff', face: 'sans-serif' }},
        borderWidth: 2,
        shadow: true
    }},
    edges: {{
        smooth: {{ type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 }},
        width: 2,
        shadow: true,
        arrows: {{
            to: {{ enabled: true, scaleFactor: 0.5 }}
        }}
    }},
    interaction: {{
        hover: true,
        select: true,
        navigationButtons: true,
        multiselect: false,
        tooltipDelay: 100
    }},
    layout: {{
        randomSeed: 42
    }}
}};

const network = new vis.Network(container, {{ nodes, edges }}, options);

// Stats
document.getElementById('stats').innerHTML = '<span>Nodes: ' + nodes.length + '</span><span>Edges: ' + edges.length + '</span>';

// Sidebar toggle
function toggleSidebar() {{
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}}

// Node click handler
network.on('click', function(params) {{
    if (params.body && params.body.node) {{
        const nodeId = params.body.node;
        const node = nodes.get(nodeId);
        if (node) {{
            showNodeDetails(nodeId, node);
        }}
    }}
}});

function showNodeDetails(nodeId, node) {{
    document.getElementById('sidebar-title').textContent = node.label + ' (' + node.domain + ')';
    
    // App details
    var appDetails = document.getElementById('app-details');
    var evidenceHtml = (node.evidence) ? '<div class="node-key" style="margin-top:8px;">' + escapeHtml(node.evidence) + '</div>' : '';
    appDetails.innerHTML = '<div class="node-key">ID: ' + escapeHtml(node.id) + '</div>' +
                           '<div class="node-key">Domain: ' + escapeHtml(node.domain) + '</div>' +
                           evidenceHtml;
    
    // Get edges - use a simpler approach
    var nodeEdges = [];
    edges.forEach(function(e) {{
        if (e.from === nodeId || e.to === nodeId) {{
            nodeEdges.push(e);
        }}
    }});
    
    // In edges
    var inEdgesDiv = document.getElementById('in-edges');
    inEdgesDiv.innerHTML = '';
    var inEdges = nodeEdges.filter(function(e) {{ return e.to === nodeId; }});
    if (inEdges.length === 0) {{
        inEdgesDiv.innerHTML = '<div style="color:#666;">(none)</div>';
    }} else {{
        inEdges.forEach(function(e) {{
            var div = document.createElement('div');
            div.className = 'edge-item';
            div.innerHTML = '<span class="edge-type">→</span> ' + escapeHtml(e.from) + '<br><small>' + escapeHtml(e.evidence || '') + '</small>';
            inEdgesDiv.appendChild(div);
        }});
    }}
    
    // Out edges
    var outEdgesDiv = document.getElementById('out-edges');
    outEdgesDiv.innerHTML = '';
    var outEdges = nodeEdges.filter(function(e) {{ return e.from === nodeId; }});
    if (outEdges.length === 0) {{
        outEdgesDiv.innerHTML = '<div style="color:#666;">(none)</div>';
    }} else {{
        outEdges.forEach(function(e) {{
            var div = document.createElement('div');
            div.className = 'edge-item';
            div.innerHTML = '<span class="edge-type">←</span> ' + escapeHtml(e.to) + '<br><small>' + escapeHtml(e.evidence || '') + '</small>';
            outEdgesDiv.appendChild(div);
        }});
    }}
    
    document.getElementById('sidebar').classList.add('active');
}}

// Helper to escape HTML
function escapeHtml(text) {{
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}}

// Search functionality
document.getElementById('search-input').addEventListener('input', function(e) {{
    var term = e.target.value.toLowerCase();
    nodes.forEach(function(n) {{
        var label = (n.label || '').toLowerCase();
        var id = (n.id || '').toLowerCase();
        if (label.includes(term) || id.includes(term)) {{
            n.hidden = false;
        }} else {{
            n.hidden = true;
        }}
    }});
    nodes.update(nodes);
}});

// Domain filter
document.getElementById('domain-select').addEventListener('change', function(e) {{
    var domain = e.target.value;
    nodes.forEach(function(n) {{
        if (domain === '' || n.domain === domain) {{
            n.hidden = false;
        }} else {{
            n.hidden = true;
        }}
    }});
    nodes.update(nodes);
}});

// Type filter
document.getElementById('type-select').addEventListener('change', function(e) {{
    var type = e.target.value;
    edges.forEach(function(edge) {{
        if (type === '' || edge.type === type) {{
            edge.hidden = false;
        }} else {{
            edge.hidden = true;
        }}
    }});
    edges.update(edges);
}});
"""


def _build_html_template(
    vis_network_css: str,
    js_code: str,
    domain_options: str,
    built_at: str,
) -> str:
    """Build the HTML template with all assets inlined."""
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Flux Topology</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #1a1a2e; color: #eee; height: 100vh; overflow: hidden; }}
        #container {{ display: flex; height: 100vh; flex-direction: row; }}
        #toolbar {{ flex: 0 0 320px; background: #16213e; padding: 16px; overflow-y: auto; 
                  border-right: 1px solid #333; }}
        #network {{ flex: 1; position: relative; }}
        #sidebar {{ flex: 0 0 320px; background: #16213e; padding: 16px; overflow-y: auto;
                   border-left: 1px solid #333; display: none; position: relative; }}
        #sidebar.active {{ display: block; }}
        h1 {{ font-size: 18px; margin-bottom: 12px; color: #fff; }}
        h2 {{ font-size: 14px; margin: 12px 0 8px; color: #aaa; }}
        label {{ display: block; margin-bottom: 8px; font-size: 12px; color: #888; }}
        input, select {{ width: 100%; padding: 8px; font-size: 12px; 
                        background: #0f3460; border: 1px solid #333; color: #eee; }}
        input:focus, select:focus {{ outline: none; border-color: #4a90d9; }}
        #legend {{ margin-top: 16px; padding: 12px; background: #0f3460; 
                  border-radius: 4px; }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 11px; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 2px; margin-right: 8px; }}
        #node-info {{ margin-top: 16px; }}
        .node-key {{ font-family: monospace; font-size: 12px; color: #4a90d9; 
                    word-break: break-all; margin-top: 4px; }}
        .edge-list {{ font-size: 11px; margin-top: 8px; }}
        .edge-item {{ padding: 4px 0; border-bottom: 1px solid #222; }}
        .edge-type {{ font-weight: bold; margin-right: 8px; }}
        #stats {{ display: flex; justify-content: space-between; padding: 12px;
                 background: #0f3460; font-size: 12px; color: #888; }}
        #toggle-sidebar {{ position: absolute; top: 12px; right: 12px; 
                          background: #4a90d9; border: none; color: white;
                          width: 24px; height: 24px; border-radius: 50%;
                          cursor: pointer; font-size: 14px; }}
        #search-container {{ margin-bottom: 16px; position: relative; }}
        #search-icon {{ position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
                       color: #888; font-size: 12px; }}
        #build-info {{ position: absolute; bottom: 8px; left: 8px; 
                      font-size: 10px; color: #666; }}
        #app-details {{ font-size: 12px; margin-bottom: 12px; }}
    </style>
    <!-- Vendored vis-network CSS -->
    <style id="vis-css">
{vis_network_css}
    </style>
</head>
<body>
    <div id="container">
        <div id="toolbar">
            <h1>Flux Topology</h1>
            <div id="stats"></div>
            <div id="search-container">
                <span id="search-icon">🔍</span>
                <input type="text" id="search-input" placeholder="Search apps...">
            </div>
            <div id="domain-filter">
                <label for="domain-select">Filter by Domain:</label>
                <select id="domain-select">
{domain_options}                </select>
            </div>
            <div id="type-filter">
                <label for="type-select">Filter by Edge Type:</label>
                <select id="type-select">
                    <option value="">All Types</option>
                    <option value="dependsOn">dependsOn (solid)</option>
                    <option value="dns-ref">dns-ref (dashed)</option>
                    <option value="external-ref">external-ref (dotted)</option>
                </select>
            </div>
            <div id="legend">
                <h2>Legend</h2>
                <div class="legend-item"><div class="legend-color" style="background:#1f77b4"></div><span>dependsOn (solid)</span></div>
                <div class="legend-item"><div class="legend-color" style="background:#ff7f0e"></div><span>dns-ref (dashed)</span></div>
                <div class="legend-item"><div class="legend-color" style="background:#d62728"></div><span>external-ref (dotted)</span></div>
            </div>
        </div>
        <div id="network"></div>
        <div id="sidebar">
            <button id="toggle-sidebar" onclick="toggleSidebar()">✕</button>
            <h1 id="sidebar-title"></h1>
            <div id="node-info">
                <h2>Node Details</h2>
                <div id="app-details"></div>
                <h2>Incoming Edges</h2>
                <div id="in-edges" class="edge-list"></div>
                <h2>Outgoing Edges</h2>
                <div id="out-edges" class="edge-list"></div>
            </div>
            <div id="build-info">Built: {built_at}</div>
        </div>
    </div>
    <script>
{js_code}
    </script>
</body>
</html>'''


def render_html(payload: dict, vis_network_js: str | None = None) -> str:
    """Render the complete HTML file from the payload.

    Args:
        payload: Dict with 'nodes', 'edges', 'filtered', 'domain_color_map', etc.
        vis_network_js: Optional pre-loaded vis-network JS (for testing). If None, loads from package.

    Returns:
        Complete HTML string with all assets inlined.
    """
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    sorted_domains = payload.get("sorted_domains", [])
    built_at = payload.get("built_at", "unknown")

    # Build the nodes array for JavaScript
    nodes_json = _escape_json_string(json.dumps(nodes))

    # Build the edges array for JavaScript
    edges_json = _escape_json_string(json.dumps(edges))

    # Load vis-network JS
    if vis_network_js is None:
        vis_network_js = _load_vis_network_js()

    # Load CSS
    vis_network_css = _load_vis_network_css()

    # Build domain options
    domain_options = _build_domain_options(sorted_domains)

    # Build JavaScript code
    js_code = _build_js_code(vis_network_js, nodes_json, edges_json)

    # Build HTML template
    html = _build_html_template(vis_network_css, js_code, domain_options, built_at)

    return html