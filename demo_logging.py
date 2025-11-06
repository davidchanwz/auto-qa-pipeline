#!/usr/bin/env python3

"""
Demo script showing the comprehensive JSON logging functionality
of the ExplorationLayer qualitative analysis pipeline.
"""

import json
import os
from config import get_llm_config
from services.agent import Agent
from services.strategic import StrategicLayer
from services.exploration import ExplorationLayer
from classes import ResearchFramework


def demo_logging():
    """
    Demo the logging functionality with a sample article analysis
    """
    print("=== ExplorationLayer Logging Demo ===\n")

    # Initialize components
    print("1. Initializing pipeline components...")
    llm_config = get_llm_config()
    agent = Agent(llm_config)
    strategic = StrategicLayer(ResearchFramework.THEMATIC_ANALYSIS)
    exploration = ExplorationLayer(agent, strategic)

    print(f"   ✓ Session ID: {exploration.session_id}")
    print(f"   ✓ Log file: {exploration.log_file}")
    print(f"   ✓ Framework: {strategic.get_framework().name}")

    # Sample articles for demonstration
    sample_articles = [
        {
            "id": 1,
            "title": "Remote Work Challenges During COVID-19",
            "content": "The pandemic forced many organizations to rapidly transition to remote work. Employees reported difficulties with communication, collaboration, and maintaining work-life balance. Technical infrastructure challenges also emerged as major barriers. However, some workers appreciated the flexibility and reduced commuting time.",
        },
        {
            "id": 2,
            "title": "Digital Learning in Higher Education",
            "content": "Universities had to quickly adapt their teaching methods for online delivery. Faculty faced steep learning curves with new technologies. Students struggled with engagement and motivation in virtual classrooms. Assessment methods needed complete redesign. Despite challenges, some innovative practices emerged.",
        },
    ]

    print(f"\n2. Analyzing {len(sample_articles)} sample articles...")
    print("   This will demonstrate INCREMENTAL processing where:")
    print("   - Each article is analyzed individually")
    print("   - Codebook is updated immediately after each article")
    print("   - Subsequent articles see changes from previous articles")
    print("   - LLM-based operation decisions with live codebook state")
    print("   - Real-time logging of incremental updates")

    # Run analysis with comprehensive logging
    try:
        updated_codebook = exploration.analyze_articles(sample_articles)

        # Save the updated codebook
        output_path = "demo_codebook.json"
        exploration.save_updated_codebook(updated_codebook, output_path)

        # Finalize the session to create summary
        session_log_path = exploration.finalize_session()

        print(f"\n3. Incremental Analysis complete! Check the logs:")
        print(f"   ✓ Detailed step log: {exploration.log_file}")
        print(f"   ✓ Session summary: {session_log_path}")
        print(f"   ✓ Updated codebook: {output_path}")

        # Show some log statistics
        if os.path.exists(exploration.log_file):
            with open(exploration.log_file, "r") as f:
                log_data = json.load(f)
                steps = log_data.get("steps", [])
                print(f"\n4. Logging Statistics:")
                print(f"   - Total log entries: {len(steps)}")

                # Count step types
                step_types = {}
                for step in steps:
                    step_type = step.get("step_type", "unknown")
                    step_types[step_type] = step_types.get(step_type, 0) + 1

                print("   - Step breakdown:")
                for step_type, count in sorted(step_types.items()):
                    print(f"     • {step_type}: {count}")

        # Show session summary
        if os.path.exists(session_log_path):
            with open(session_log_path, "r") as f:
                session_data = json.load(f)
                summary = session_data.get("summary", {})
                print(f"\n5. Session Summary:")
                print(
                    f"   - Articles processed: {summary.get('total_articles_processed', 0)}"
                )
                print(
                    f"   - Operations performed: {summary.get('total_operations_performed', 0)}"
                )
                print(f"   - Decisions made: {summary.get('total_decisions_made', 0)}")
                print(f"   - Errors encountered: {summary.get('total_errors', 0)}")

                final_stats = summary.get("final_codebook_stats", {})
                print(
                    f"   - Final codebook size: {final_stats.get('total_codes', 0)} codes"
                )

        print(f"\n✓ Incremental Demo completed successfully!")
        print(
            f"  Review the JSON log files to see the step-by-step incremental process:"
        )
        print(
            f"  - Each article processed individually with immediate codebook updates"
        )
        print(f"  - Subsequent articles see codes added by previous articles")
        print(f"  - Real-time tracking of codebook growth and changes")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print(f"   Check log files for detailed error information:")
        print(f"   - {exploration.log_file}")

        # Still try to finalize session to capture error logs
        try:
            session_log_path = exploration.finalize_session()
            print(f"   - {session_log_path}")
        except:
            pass


if __name__ == "__main__":
    demo_logging()
