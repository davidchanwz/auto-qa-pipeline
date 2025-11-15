#!/usr/bin/env python3

"""
Exploration Log Visualization Generator

Creates an interactive HTML visualization of the exploration session logs,
showing every step of the qualitative analysis process with filtering and navigation.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def load_exploration_log(file_path: str) -> Dict[str, Any]:
    """Load exploration log from JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Log file not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in log file: {e}")
        return None


def analyze_log_structure(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the structure and statistics of the log."""
    stats = {
        "total_steps": len(steps),
        "step_types": {},
        "timeline": {},
        "articles_processed": 0,
        "codes_generated": 0,
        "operations_performed": 0,
        "decisions_made": 0,
        "errors": 0,
    }

    # Count step types and extract key metrics
    for step in steps:
        step_type = step.get("step_type", "unknown")
        stats["step_types"][step_type] = stats["step_types"].get(step_type, 0) + 1

        # Extract specific metrics
        if step_type == "article_analysis_start":
            stats["articles_processed"] += 1
        elif step_type == "code_created":
            stats["codes_generated"] += 1
        elif step_type == "operation_success":
            stats["operations_performed"] += 1
        elif step_type == "llm_decision_complete":
            stats["decisions_made"] += 1
        elif "error" in step_type.lower():
            stats["errors"] += 1

    return stats


def get_step_category(step_type: str) -> str:
    """Categorize step types for better organization."""
    categories = {
        "session": [
            "session_start",
            "incremental_analysis_start",
            "incremental_analysis_complete",
        ],
        "article": [
            "article_analysis_start",
            "article_analysis_complete",
            "incremental_article_start",
            "incremental_article_complete",
            "incremental_article_no_operations",
            "incremental_article_no_codes",
        ],
        "prompt": [
            "prompt_generated",
            "context_set",
            "llm_response_received",
            "fallback_method_used",
        ],
        "code": ["code_created", "candidate_processing"],
        "similarity": ["similarity_search"],
        "decision": [
            "decision_context_set",
            "decision_prompt_generated",
            "llm_decision_start",
            "llm_decision_complete",
            "decision_fallback_used",
            "decision_error",
        ],
        "operation": [
            "operation_created",
            "operation_attempt",
            "operation_success",
            "operation_failure",
        ],
        "comparison": ["comparison_start", "comparison_complete"],
        "codebook": [
            "codebook_update_start",
            "codebook_update_complete",
            "codebook_save_start",
            "codebook_save_success",
        ],
        "update": ["incremental_update_start"],
    }

    for category, types in categories.items():
        if step_type in types:
            return category
    return "other"


def get_step_icon(step_type: str) -> str:
    """Get icon for step type."""
    icons = {
        "session": "🚀",
        "article": "📄",
        "prompt": "💬",
        "code": "🏷️",
        "similarity": "🔍",
        "decision": "🤔",
        "operation": "⚙️",
        "comparison": "⚖️",
        "codebook": "📚",
        "update": "🔄",
        "other": "📝",
    }
    category = get_step_category(step_type)
    return icons.get(category, "📝")


def format_step_data(data: Dict[str, Any]) -> str:
    """Format step data for display."""
    if not data:
        return "<em>No additional data</em>"

    # Special formatting for common data types
    formatted_items = []

    for key, value in data.items():
        if key == "timestamp":
            continue  # Skip timestamp as it's shown separately

        if isinstance(value, dict):
            value_str = json.dumps(value, indent=2)[:500]
            if len(json.dumps(value)) > 500:
                value_str += "..."
        elif isinstance(value, list):
            if len(value) <= 5:
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = (
                    f"{', '.join(str(v) for v in value[:5])}... ({len(value)} total)"
                )
        else:
            value_str = str(value)

        # Highlight important fields
        if key in ["article_id", "code_name", "operation_type", "decision", "error"]:
            formatted_items.append(
                f"<strong>{key}:</strong> <span class='highlight'>{value_str}</span>"
            )
        else:
            formatted_items.append(f"<strong>{key}:</strong> {value_str}")

    return "<br>".join(formatted_items)


def generate_html_visualization(log_data: Dict[str, Any], stats: Dict[str, Any]) -> str:
    """Generate interactive HTML visualization."""

    steps = log_data.get("steps", [])

    # Group steps by category for filtering
    steps_by_category = {}
    for step in steps:
        category = get_step_category(step.get("step_type", "unknown"))
        if category not in steps_by_category:
            steps_by_category[category] = []
        steps_by_category[category].append(step)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exploration Log Visualization</title>
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
        
        .controls {{
            background: white;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-group label {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .filter-select, .search-input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 0.9rem;
        }}
        
        .search-input {{
            min-width: 200px;
        }}
        
        .clear-filters {{
            background: #e74c3c;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
        }}
        
        .clear-filters:hover {{
            background: #c0392b;
        }}
        
        .content {{
            padding: 30px;
            max-height: 800px;
            overflow-y: auto;
        }}
        
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #3498db, #2980b9);
        }}
        
        .step-item {{
            position: relative;
            margin-bottom: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .step-item:hover {{
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .step-item::before {{
            content: '';
            position: absolute;
            left: -23px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: #3498db;
            border-radius: 50%;
            box-shadow: 0 0 0 4px white, 0 0 0 6px #3498db;
        }}
        
        .step-header {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .step-header:hover {{
            background: #e9ecef;
        }}
        
        .step-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .step-icon {{
            font-size: 1.2rem;
        }}
        
        .step-meta {{
            font-size: 0.85rem;
            color: #666;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .step-category {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }}
        
        .step-time {{
            font-family: monospace;
        }}
        
        .step-toggle {{
            color: #666;
            font-size: 1rem;
            transition: transform 0.3s ease;
        }}
        
        .step-content {{
            padding: 20px;
            background: white;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .step-content.expanded {{
            max-height: 1000px;
        }}
        
        .step-data {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        .highlight {{
            background: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }}
        
        .category-session {{ border-left-color: #e74c3c !important; }}
        .category-session .step-category {{ background: #e74c3c; }}
        .category-session::before {{ background: #e74c3c !important; box-shadow: 0 0 0 4px white, 0 0 0 6px #e74c3c !important; }}
        
        .category-article {{ border-left-color: #f39c12 !important; }}
        .category-article .step-category {{ background: #f39c12; }}
        .category-article::before {{ background: #f39c12 !important; box-shadow: 0 0 0 4px white, 0 0 0 6px #f39c12 !important; }}
        
        .category-code {{ border-left-color: #27ae60 !important; }}
        .category-code .step-category {{ background: #27ae60; }}
        .category-code::before {{ background: #27ae60 !important; box-shadow: 0 0 0 4px white, 0 0 0 6px #27ae60 !important; }}
        
        .category-decision {{ border-left-color: #9b59b6 !important; }}
        .category-decision .step-category {{ background: #9b59b6; }}
        .category-decision::before {{ background: #9b59b6 !important; box-shadow: 0 0 0 4px white, 0 0 0 6px #9b59b6 !important; }}
        
        .category-operation {{ border-left-color: #34495e !important; }}
        .category-operation .step-category {{ background: #34495e; }}
        .category-operation::before {{ background: #34495e !important; box-shadow: 0 0 0 4px white, 0 0 0 6px #34495e !important; }}
        
        .hidden {{
            display: none !important;
        }}
        
        .step-counter {{
            position: sticky;
            top: 0;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            margin: -30px -30px 20px -30px;
            border-bottom: 1px solid #e9ecef;
            font-weight: bold;
            color: #2c3e50;
            z-index: 10;
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
            
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .filter-group {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .timeline {{
                padding-left: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📊 Exploration Log Visualization</h1>
            <p>Interactive timeline of qualitative analysis process</p>
        </header>
        
        <div class="stats-panel">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_steps']}</div>
                    <div class="stat-label">Total Steps</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['articles_processed']}</div>
                    <div class="stat-label">Articles Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['codes_generated']}</div>
                    <div class="stat-label">Codes Generated</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['operations_performed']}</div>
                    <div class="stat-label">Operations Performed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['decisions_made']}</div>
                    <div class="stat-label">LLM Decisions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(stats['step_types'])}</div>
                    <div class="stat-label">Step Types</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <div class="filter-group">
                <label for="categoryFilter">Category:</label>
                <select id="categoryFilter" class="filter-select">
                    <option value="">All Categories</option>
                    <option value="session">🚀 Session</option>
                    <option value="article">📄 Article</option>
                    <option value="prompt">💬 Prompt</option>
                    <option value="code">🏷️ Code</option>
                    <option value="similarity">🔍 Similarity</option>
                    <option value="decision">🤔 Decision</option>
                    <option value="operation">⚙️ Operation</option>
                    <option value="comparison">⚖️ Comparison</option>
                    <option value="codebook">📚 Codebook</option>
                    <option value="update">🔄 Update</option>
                    <option value="other">📝 Other</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="searchInput">Search:</label>
                <input type="text" id="searchInput" class="search-input" placeholder="Search step type, data, or content...">
            </div>
            
            <button class="clear-filters" onclick="clearFilters()">Clear Filters</button>
            
            <div class="filter-group">
                <button class="clear-filters" onclick="expandAll()">Expand All</button>
                <button class="clear-filters" onclick="collapseAll()">Collapse All</button>
            </div>
        </div>
        
        <div class="content">
            <div class="step-counter">
                Showing <span id="visibleCount">{len(steps)}</span> of {len(steps)} steps
            </div>
            
            <div class="timeline" id="timeline">
    """

    # Generate timeline items
    for i, step in enumerate(steps):
        step_type = step.get("step_type", "unknown")
        timestamp = step.get("timestamp", "")
        data = step.get("data", {})

        category = get_step_category(step_type)
        icon = get_step_icon(step_type)

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%H:%M:%S.%f")[:-3]  # Show milliseconds
        except:
            formatted_time = timestamp

        formatted_data = format_step_data(data)

        html += f"""
                <div class="step-item category-{category}" data-category="{category}" data-step-type="{step_type}">
                    <div class="step-header" onclick="toggleStep(this)">
                        <div class="step-title">
                            <span class="step-icon">{icon}</span>
                            <span>{step_type.replace('_', ' ').title()}</span>
                        </div>
                        <div class="step-meta">
                            <span class="step-category">{category}</span>
                            <span class="step-time">{formatted_time}</span>
                            <span class="step-toggle">▼</span>
                        </div>
                    </div>
                    <div class="step-content">
                        <div class="step-data">
                            {formatted_data}
                        </div>
                    </div>
                </div>
        """

    html += f"""
            </div>
        </div>
    </div>
    
    <script>
        function toggleStep(header) {{
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.step-toggle');
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                toggle.textContent = '▼';
            }} else {{
                content.classList.add('expanded');
                toggle.textContent = '▲';
            }}
        }}
        
        function expandAll() {{
            const contents = document.querySelectorAll('.step-content');
            const toggles = document.querySelectorAll('.step-toggle');
            
            contents.forEach(content => content.classList.add('expanded'));
            toggles.forEach(toggle => toggle.textContent = '▲');
        }}
        
        function collapseAll() {{
            const contents = document.querySelectorAll('.step-content');
            const toggles = document.querySelectorAll('.step-toggle');
            
            contents.forEach(content => content.classList.remove('expanded'));
            toggles.forEach(toggle => toggle.textContent = '▼');
        }}
        
        function filterSteps() {{
            const categoryFilter = document.getElementById('categoryFilter').value;
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const steps = document.querySelectorAll('.step-item');
            let visibleCount = 0;
            
            steps.forEach(step => {{
                const category = step.dataset.category;
                const stepType = step.dataset.stepType;
                const content = step.textContent.toLowerCase();
                
                const categoryMatch = !categoryFilter || category === categoryFilter;
                const searchMatch = !searchInput || content.includes(searchInput);
                
                if (categoryMatch && searchMatch) {{
                    step.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    step.classList.add('hidden');
                }}
            }});
            
            document.getElementById('visibleCount').textContent = visibleCount;
        }}
        
        function clearFilters() {{
            document.getElementById('categoryFilter').value = '';
            document.getElementById('searchInput').value = '';
            filterSteps();
        }}
        
        // Add event listeners
        document.getElementById('categoryFilter').addEventListener('change', filterSteps);
        document.getElementById('searchInput').addEventListener('input', filterSteps);
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            // Auto-expand first few steps for better initial view
            const firstSteps = document.querySelectorAll('.step-item:nth-child(-n+3)');
            firstSteps.forEach(step => {{
                const content = step.querySelector('.step-content');
                const toggle = step.querySelector('.step-toggle');
                content.classList.add('expanded');
                toggle.textContent = '▲';
            }});
        }});
    </script>
</body>
</html>
    """

    return html


def create_exploration_log_visualization(log_path: str, output_path: str = None) -> str:
    """Main function to create exploration log visualization."""

    # Load log data
    log_data = load_exploration_log(log_path)
    if not log_data:
        return None

    steps = log_data.get("steps", [])
    if not steps:
        print("No steps found in log file")
        return None

    # Analyze log structure
    print("Analyzing log structure...")
    stats = analyze_log_structure(steps)

    # Print summary to console
    print(f"\n📊 Log Analysis Summary:")
    print(f"Total steps: {stats['total_steps']}")
    print(f"Articles processed: {stats['articles_processed']}")
    print(f"Codes generated: {stats['codes_generated']}")
    print(f"Operations performed: {stats['operations_performed']}")
    print(f"LLM decisions made: {stats['decisions_made']}")
    print(f"Errors encountered: {stats['errors']}")

    print(f"\n📈 Top step types:")
    sorted_steps = sorted(stats["step_types"].items(), key=lambda x: x[1], reverse=True)
    for step_type, count in sorted_steps[:10]:
        print(f"  {step_type}: {count}")

    # Generate HTML
    print("Generating HTML visualization...")
    html_content = generate_html_visualization(log_data, stats)

    # Save to file
    if not output_path:
        # Extract session ID from log path if possible
        session_id = "unknown"
        if "exploration_session_" in log_path:
            session_id = log_path.split("exploration_session_")[1].split(".")[0]
        output_path = f"exploration_log_visualization_{session_id}.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Exploration log visualization saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    import glob

    # Find most recent log file if no specific file provided
    log_path = None

    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    else:
        # Look for most recent exploration log
        log_files = glob.glob("logs/exploration_session_*.json")
        if log_files:
            log_path = max(log_files, key=os.path.getmtime)
            print(f"Using most recent log file: {log_path}")
        else:
            print("No exploration log files found in logs/ directory")
            sys.exit(1)

    if os.path.exists(log_path):
        output_file = create_exploration_log_visualization(log_path)
        if output_file:
            print(
                f"\n🌐 Open the file in your browser to view the interactive exploration log!"
            )
    else:
        print(f"❌ Log file not found: {log_path}")
        print("Usage: python visualize_exploration_log.py [path_to_log.json]")
