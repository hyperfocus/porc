import argparse
import json
from dag_tool import process_blueprint

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render DAG from Terraform Blueprint")
    parser.add_argument("file", help="Path to blueprint JSON file")
    parser.add_argument("--output", default="dag_output", help="Prefix for output files")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        blueprint = json.load(f)

    order, image = process_blueprint(blueprint, args.output)
    print("Execution Order:")
    for step in order:
        print(f" - {step}")
    print(f"DAG image saved as: {image}")