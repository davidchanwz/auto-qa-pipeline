"""
Demo script showing how the Exploration Layer integrates with Agent and Strategic Layer
to analyze articles and update the codebook using your defined classes.
"""

import json
from services.agent import Agent
from services.strategic import StrategicLayer
from services.exploration import ExplorationLayer


def convert_sample_codes_to_codebook(sample_codes_path: str) -> str:
    """
    Convert sample_codes.json format to Codebook-compatible format
    Returns the converted JSON string
    """
    try:
        with open(sample_codes_path, "r") as f:
            sample_data = json.load(f)

        # Extract the codebook data from the wrapper
        codebook_section = sample_data["codebook"]

        # Convert to Codebook format
        converted_data = {
            "metadata": {
                "total_codes": codebook_section["metadata"]["total_codes"],
                "next_id": codebook_section["metadata"]["total_codes"]
                + 1,  # Next available ID
                "created_at": codebook_section["metadata"]["created_at"],
            },
            "codes": codebook_section["codes"],
        }

        return json.dumps(converted_data, indent=2)

    except Exception as e:
        print(f"❌ Error converting sample codes: {e}")
        return None


def main():
    # Initialize components
    print("🚀 Initializing Exploration Layer Demo...")

    # Create agent and strategic layer
    agent = Agent()
    strategic = StrategicLayer()

    # Show agent configuration
    agent_info = agent.get_info()
    print(
        f"🤖 Using model: {agent_info['model']} (default: {agent_info['default_model']})"
    )

    # Create exploration layer
    exploration = ExplorationLayer(agent, strategic)

    # Load reference codebook (from converted sample_codes.json)
    print("\n📚 Loading reference codebook...")
    try:
        # Load the converted reference codebook
        exploration.load_reference_codebook("data/reference_codebook.json")
    except Exception as e:
        print(f"❌ Error loading reference codebook: {e}")
        print("⚠️ Starting with empty codebook")

    # Load articles
    print("\n📰 Loading articles...")
    try:
        with open("data/articles.json", "r") as f:
            all_articles = json.load(f)

        # Skip article 1 for demo purposes
        articles = all_articles[1:]  # Start from index 1 (skip index 0)
        print(
            f"✅ Loaded {len(all_articles)} articles (analyzing {len(articles)} - skipping article 1)"
        )
    except FileNotFoundError:
        print("❌ Articles file not found")
        return

    # Analyze articles
    print("\n🔍 Starting article analysis...")
    updated_codebook = exploration.analyze_articles(articles)

    # Show results
    print("\n📊 Analysis Results:")
    stats = exploration.get_codebook_summary()
    print(f"Total codes: {stats['total_codes']}")
    print(f"Function distribution: {stats['function_distribution']}")
    print(f"Total evidence quotes: {stats['total_evidence_quotes']}")

    # Save updated codebook
    print("\n💾 Saving updated codebook...")
    exploration.save_updated_codebook(updated_codebook, "data/updated_codebook.json")

    # Generate visualization
    print("\n🎨 Generating interactive visualization...")
    try:
        from visualize_codebook import create_codebook_visualization

        viz_path = create_codebook_visualization("data/updated_codebook.json")
        if viz_path:
            print(f"✅ Visualization created: {viz_path}")
            print("🌐 Open the HTML file in your browser to explore the codebook!")
    except Exception as e:
        print(f"⚠️ Could not generate visualization: {e}")

    print("\n✅ Demo completed!")


if __name__ == "__main__":
    main()
