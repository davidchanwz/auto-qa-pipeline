#!/usr/bin/env python3

"""
Codebook Tree Visualization Generator

Creates an interactive HTML visualization of the codebook organized by frame functions,
showing hierarchical parent-child relationships with evidence details and tree statistics.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def load_codebook(file_path: str) -> Dict[str, Any]:
    """Load codebook from JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Codebook file not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in codebook file: {e}")
        return None


class CodeNode:
    """Represents a code node in the tree structure."""

    def __init__(self, code_data: Dict[str, Any]):
        self.code_id = code_data.get("code_id")
        self.name = code_data.get("name", "Unnamed Code")
        self.function = code_data.get("function", "UNKNOWN")
        self.evidence = code_data.get("evidence", {})
        self.created_at = code_data.get("created_at", "")
        self.updated_at = code_data.get("updated_at", "")
        self.parent_code_id = code_data.get("parent_code_id")
        self.children = []
        self.level = 0  # Tree depth level

    def add_child(self, child_node):
        """Add a child node."""
        self.children.append(child_node)
        child_node.level = self.level + 1

    def get_evidence_count(self):
        """Get total evidence count for this code."""
        total = 0
        for article_quotes in self.evidence.values():
            total += len(article_quotes)
        return total

    def get_tree_depth(self):
        """Get maximum depth of tree rooted at this node."""
        if not self.children:
            return 1
        return 1 + max(child.get_tree_depth() for child in self.children)


def build_code_trees(codebook_data: Dict[str, Any]) -> Dict[str, List[CodeNode]]:
    """Build hierarchical trees organized by frame function."""
    codes = codebook_data.get("codes", {})

    # Create all nodes first
    all_nodes = {}
    for code_id, code_data in codes.items():
        node = CodeNode(code_data)
        all_nodes[code_id] = node

    # Build parent-child relationships
    root_nodes_by_function = {
        "PROBLEM_DEFINITION": [],
        "CAUSAL_ATTRIBUTION": [],
        "MORAL_EVALUATION": [],
        "TREATMENT_ADVOCACY": [],
        "OTHER": [],
    }

    for code_id, node in all_nodes.items():
        if node.parent_code_id and str(node.parent_code_id) in all_nodes:
            # This node has a parent
            parent = all_nodes[str(node.parent_code_id)]
            parent.add_child(node)
        else:
            # This is a root node
            function = node.function
            if function in root_nodes_by_function:
                root_nodes_by_function[function].append(node)
            else:
                root_nodes_by_function["OTHER"].append(node)

    return root_nodes_by_function


def get_tree_statistics(trees: Dict[str, List[CodeNode]]) -> Dict[str, Any]:
    """Calculate statistics about the tree structure."""
    stats = {
        "total_codes": 0,
        "root_codes": 0,
        "max_depth": 0,
        "codes_by_level": {},
        "function_stats": {},
    }

    for function, roots in trees.items():
        if not roots:  # Skip empty functions
            continue

        function_stats = {
            "total_codes": 0,
            "root_codes": len(roots),
            "max_depth": 0,
            "codes_by_level": {},
        }

        stats["root_codes"] += len(roots)

        # Traverse each tree to collect statistics
        for root in roots:
            tree_depth = root.get_tree_depth()
            function_stats["max_depth"] = max(function_stats["max_depth"], tree_depth)
            stats["max_depth"] = max(stats["max_depth"], tree_depth)

            # Count nodes at each level
            def count_levels(node, level=0):
                function_stats["total_codes"] += 1
                stats["total_codes"] += 1

                if level not in function_stats["codes_by_level"]:
                    function_stats["codes_by_level"][level] = 0
                if level not in stats["codes_by_level"]:
                    stats["codes_by_level"][level] = 0

                function_stats["codes_by_level"][level] += 1
                stats["codes_by_level"][level] += 1

                for child in node.children:
                    count_levels(child, level + 1)

            count_levels(root)

        stats["function_stats"][function] = function_stats

    return stats


def render_tree_node_html(node: CodeNode, is_root: bool = False) -> str:
    """Render a single tree node as HTML."""
    evidence_count = node.get_evidence_count()
    has_children = len(node.children) > 0

    # Create evidence details
    evidence_html = ""
    if node.evidence:
        evidence_html = "<div class='evidence-details' style='display: none;'>"
        for article_id, quotes in node.evidence.items():
            evidence_html += f"<div class='article-evidence'>"
            evidence_html += f"<strong>Article {article_id}:</strong>"
            evidence_html += "<ul class='quotes-list'>"
            for quote in quotes:
                # Truncate long quotes for display
                display_quote = quote[:200] + "..." if len(quote) > 200 else quote
                evidence_html += f"<li>{display_quote}</li>"
            evidence_html += "</ul></div>"
        evidence_html += "</div>"

    node_class = "tree-node"
    if is_root:
        node_class += " root-node"
    if has_children:
        node_class += " has-children"

    node_html = f"""
    <div class="{node_class}" data-level="{node.level}">
        <div class="node-header" onclick="toggleNode(this)">
            <span class="node-toggle">{'▼' if has_children else '●'}</span>
            <span class="node-name">{node.name}</span>
            <span class="node-meta">
                ID: {node.code_id} | Evidence: {evidence_count} quotes
                {f' | Children: {len(node.children)}' if has_children else ''}
            </span>
        </div>
        {evidence_html}
    """

    if has_children:
        node_html += "<div class='children-container'>"
        for child in node.children:
            node_html += render_tree_node_html(child, False)
        node_html += "</div>"

    node_html += "</div>"
    return node_html


def generate_html_visualization(
    trees: Dict[str, List[CodeNode]], stats: Dict[str, Any]
) -> str:
    """Generate interactive HTML visualization with tree structure."""

    # Function descriptions
    function_descriptions = {
        "PROBLEM_DEFINITION": "Codes that define and identify problems, issues, or challenges",
        "CAUSAL_ATTRIBUTION": "Codes that explain causes, reasons, or factors behind issues",
        "MORAL_EVALUATION": "Codes that express values, judgments, or evaluations",
        "TREATMENT_ADVOCACY": "Codes that suggest solutions, treatments, or recommendations",
    }

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebook Tree Visualization</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(45deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .stats-panel {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
        }}
        
        .levels-breakdown {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .levels-breakdown h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .level-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .level-label {{
            width: 80px;
            font-weight: bold;
            color: #666;
        }}
        
        .level-progress {{
            flex: 1;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            margin: 0 15px;
            overflow: hidden;
        }}
        
        .level-fill {{
            height: 100%;
            background: linear-gradient(45deg, #3498db, #2980b9);
            transition: width 0.3s ease;
        }}
        
        .level-count {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .function-section {{
            margin-bottom: 40px;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .function-header {{
            background: linear-gradient(45deg, #34495e, #2c3e50);
            color: white;
            padding: 20px;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .function-header:hover {{
            background: linear-gradient(45deg, #3d566e, #34495e);
        }}
        
        .function-title {{
            font-size: 1.4rem;
            font-weight: 600;
        }}
        
        .function-stats {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .function-description {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .function-toggle {{
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }}
        
        .function-content {{
            background: white;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .function-content.expanded {{
            max-height: 10000px;
        }}
        
        .tree-container {{
            padding: 20px;
        }}
        
        .tree-node {{
            margin-bottom: 8px;
            border-left: 2px solid #e9ecef;
            position: relative;
        }}
        
        .tree-node.root-node {{
            border-left: 3px solid #3498db;
        }}
        
        .node-header {{
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .node-header:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}
        
        .root-node .node-header {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        
        .node-toggle {{
            color: #666;
            font-weight: bold;
            min-width: 20px;
        }}
        
        .node-name {{
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }}
        
        .node-meta {{
            font-size: 0.85rem;
            color: #666;
            background: white;
            padding: 4px 8px;
            border-radius: 12px;
        }}
        
        .children-container {{
            margin-left: 30px;
            margin-top: 8px;
            padding-left: 15px;
            border-left: 1px dashed #ccc;
        }}
        
        .evidence-details {{
            margin: 10px 15px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        }}
        
        .article-evidence {{
            margin-bottom: 15px;
        }}
        
        .article-evidence:last-child {{
            margin-bottom: 0;
        }}
        
        .article-evidence strong {{
            color: #856404;
            display: block;
            margin-bottom: 8px;
        }}
        
        .quotes-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .quotes-list li {{
            background: white;
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 4px;
            border-left: 3px solid #ffc107;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        
        .quotes-list li:last-child {{
            margin-bottom: 0;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .children-container {{
                margin-left: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🌳 Codebook Tree Visualization</h1>
            <p>Hierarchical view of qualitative codes organized by frame functions</p>
        </header>
        
        <div class="stats-panel">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_codes']}</div>
                    <div class="stat-label">Total Codes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['root_codes']}</div>
                    <div class="stat-label">Root Codes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['total_codes'] - stats['root_codes']}</div>
                    <div class="stat-label">Child Codes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['max_depth']}</div>
                    <div class="stat-label">Max Tree Depth</div>
                </div>
            </div>
            
            <div class="levels-breakdown">
                <h3>📊 Codes by Tree Level</h3>
    """

    # Add level breakdown
    if stats["codes_by_level"]:
        max_count = max(stats["codes_by_level"].values())
        for level in sorted(stats["codes_by_level"].keys()):
            count = stats["codes_by_level"][level]
            percentage = (count / max_count) * 100
            html += f"""
                <div class="level-bar">
                    <div class="level-label">Level {level}</div>
                    <div class="level-progress">
                        <div class="level-fill" style="width: {percentage}%"></div>
                    </div>
                    <div class="level-count">{count} codes</div>
                </div>
            """

    html += """
            </div>
        </div>
        
        <div class="content">
    """

    # Generate function sections
    for function, roots in trees.items():
        if not roots:  # Skip empty functions
            continue

        function_stats = stats["function_stats"].get(function, {})
        description = function_descriptions.get(
            function, "Other or uncategorized codes"
        )

        html += f"""
            <div class="function-section">
                <div class="function-header" onclick="toggleFunction(this)">
                    <div>
                        <div class="function-title">{function.replace('_', ' ').title()}</div>
                        <div class="function-description">{description}</div>
                    </div>
                    <div>
                        <div class="function-stats">
                            {function_stats.get('total_codes', 0)} codes | 
                            Max depth: {function_stats.get('max_depth', 0)} | 
                            Roots: {function_stats.get('root_codes', 0)}
                        </div>
                        <div class="function-toggle">▼</div>
                    </div>
                </div>
                <div class="function-content">
                    <div class="tree-container">
        """

        # Render trees for this function
        for root in roots:
            html += render_tree_node_html(root, True)

        html += """
                    </div>
                </div>
            </div>
        """

    html += f"""
        </div>
    </div>
    
    <script>
        function toggleFunction(header) {{
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.function-toggle');
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                toggle.textContent = '▼';
                toggle.style.transform = 'rotate(0deg)';
            }} else {{
                content.classList.add('expanded');
                toggle.textContent = '▲';
                toggle.style.transform = 'rotate(180deg)';
            }}
        }}
        
        function toggleNode(header) {{
            const node = header.parentElement;
            const evidenceDetails = node.querySelector('.evidence-details');
            const childrenContainer = node.querySelector('.children-container');
            const toggle = header.querySelector('.node-toggle');
            
            // Toggle evidence details
            if (evidenceDetails) {{
                if (evidenceDetails.style.display === 'none' || evidenceDetails.style.display === '') {{
                    evidenceDetails.style.display = 'block';
                }} else {{
                    evidenceDetails.style.display = 'none';
                }}
            }}
            
            // Toggle children container
            if (childrenContainer) {{
                if (childrenContainer.style.display === 'none') {{
                    childrenContainer.style.display = 'block';
                    toggle.textContent = '▼';
                }} else {{
                    childrenContainer.style.display = 'none';
                    toggle.textContent = '▶';
                }}
            }}
        }}
        
        // Initialize all function sections as collapsed
        document.addEventListener('DOMContentLoaded', function() {{
            const functionContents = document.querySelectorAll('.function-content');
            functionContents.forEach(content => {{
                content.classList.add('expanded'); // Start expanded
            }});
        }});
    </script>
</body>
</html>
    """

    return html


def create_codebook_tree_visualization(
    codebook_path: str, output_path: str = None
) -> str:
    """Main function to create tree visualization."""

    # Load codebook
    codebook_data = load_codebook(codebook_path)
    if not codebook_data:
        return None

    # Build trees
    print("Building code trees...")
    trees = build_code_trees(codebook_data)

    # Calculate statistics
    print("Calculating tree statistics...")
    stats = get_tree_statistics(trees)

    # Print statistics to console
    print(f"\n📊 Tree Statistics:")
    print(f"Total codes: {stats['total_codes']}")
    print(f"Root codes: {stats['root_codes']}")
    print(f"Child codes: {stats['total_codes'] - stats['root_codes']}")
    print(f"Maximum tree depth: {stats['max_depth']}")

    print(f"\n📈 Codes by level:")
    for level in sorted(stats["codes_by_level"].keys()):
        print(f"  Level {level}: {stats['codes_by_level'][level]} codes")

    print(f"\n🎯 Function breakdown:")
    for function, function_stats in stats["function_stats"].items():
        if function_stats["total_codes"] > 0:
            print(
                f"  {function}: {function_stats['total_codes']} codes (depth: {function_stats['max_depth']})"
            )

    # Generate HTML
    print("Generating HTML visualization...")
    html_content = generate_html_visualization(trees, stats)

    # Save to file
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"codebook_tree_visualization_{timestamp}.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Tree visualization saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys

    # Default path
    codebook_path = "data/updated_codebook.json"

    # Allow command line argument
    if len(sys.argv) > 1:
        codebook_path = sys.argv[1]

    if os.path.exists(codebook_path):
        output_file = create_codebook_tree_visualization(codebook_path)
        if output_file:
            print(
                f"\n🌐 Open the file in your browser to view the interactive tree visualization!"
            )
    else:
        print(f"❌ Codebook file not found: {codebook_path}")
        print("Usage: python visualize_codebook_tree.py [path_to_codebook.json]")
