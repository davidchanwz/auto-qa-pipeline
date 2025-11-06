"""
Converter script to transform sample_codes.json from custom format
to standard Codebook format that can be loaded by the Codebook class.
"""

import json
from datetime import datetime


def convert_sample_codes_to_codebook_format(input_path: str, output_path: str):
    """
    Convert sample_codes.json format to Codebook-compatible format

    Input format (sample_codes.json):
    {
        "codebook": {
            "metadata": {...},
            "codes": {...},
            "articles": {...},
            "function_distribution": {...}
        }
    }

    Output format (Codebook compatible):
    {
        "metadata": {...},
        "codes": {...}
    }
    """
    try:
        print(f"📖 Reading {input_path}...")
        with open(input_path, "r") as f:
            sample_data = json.load(f)

        # Extract the codebook data from the wrapper
        codebook_section = sample_data["codebook"]

        print(f"🔄 Converting format...")

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

        print(f"💾 Writing to {output_path}...")
        with open(output_path, "w") as f:
            json.dump(converted_data, f, indent=2)

        print(f"✅ Successfully converted!")
        print(f"📊 Converted {converted_data['metadata']['total_codes']} codes")

        # Show function distribution
        functions = {}
        for code_data in converted_data["codes"].values():
            func = code_data["function"]
            functions[func] = functions.get(func, 0) + 1

        print(f"📈 Function distribution: {functions}")

    except Exception as e:
        print(f"❌ Error during conversion: {e}")


def main():
    print("🔧 Sample Codes Format Converter")
    print("=" * 40)

    # Convert the existing sample_codes.json
    convert_sample_codes_to_codebook_format(
        input_path="data/sample_codes.json", output_path="data/reference_codebook.json"
    )

    print("\n🎯 Now you can load the reference codebook with:")
    print("   exploration.load_reference_codebook('data/reference_codebook.json')")


if __name__ == "__main__":
    main()
