"""
Main controller - Reads configuration from config/config.yaml
Orchestrates text and special character generation
"""

import subprocess
import sys
import os
import re
from src.config_loader import load_config

# Load configuration from YAML
config = load_config("config/config.yaml")

# Print configuration summary
config.print_summary()

# Calculate samples from config
TOTAL_SAMPLES = config.dataset.total_samples
TEXT_PERCENTAGE = config.dataset.text_percentage
TEXT_SAMPLES = int(TOTAL_SAMPLES * TEXT_PERCENTAGE / 100)
SPECIAL_SAMPLES = TOTAL_SAMPLES - TEXT_SAMPLES

print(f"📝 Generating {TEXT_SAMPLES:,} text images...")
print(f"🔢 Generating {SPECIAL_SAMPLES:,} special images...")
print()


def run_generator(script_name, num_samples):
    script_path = os.path.join("src", script_name)
    with open(script_path, "r") as f:
        content = f.read()

    content = re.sub(r"NUM_IMAGES = \d+", f"NUM_IMAGES = {num_samples}", content)

    temp_file = f"_temp_{script_name}"
    with open(temp_file, "w") as f:
        f.write(content)

    subprocess.run([sys.executable, temp_file])
    os.remove(temp_file)


if __name__ == "__main__":
    print("🚀 Starting dataset generation...\n")

    if TEXT_SAMPLES > 0:
        print("=" * 70)
        print("GENERATING TEXT IMAGES")
        print("=" * 70)
        run_generator("text_generator.py", TEXT_SAMPLES)

    if SPECIAL_SAMPLES > 0:
        print("\n" + "=" * 70)
        print("GENERATING SPECIAL CHARACTER IMAGES")
        print("=" * 70)
        run_generator("special_generator.py", SPECIAL_SAMPLES)

    print("\n" + "=" * 70)
    print("✅ GENERATION COMPLETE!")
    print("=" * 70)
    print(f"Total images created: {TOTAL_SAMPLES:,}")
    print(f"  ├─ Text images: {TEXT_SAMPLES:,}")
    print(f"  └─ Special images: {SPECIAL_SAMPLES:,}")
    print(f"\nOutput directory: {config.dataset.output_dir}/")
    print(f"Configuration used: config.yaml")
    print("=" * 70)
