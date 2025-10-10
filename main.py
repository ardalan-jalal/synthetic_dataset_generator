"""
Main controller - Set total samples and percentage split
"""

import subprocess
import sys
import os
import re

# ============================================================================
# CONFIGURATION
# ============================================================================
TOTAL_SAMPLES = 500
TEXT_PERCENTAGE = 85
# ============================================================================

TEXT_SAMPLES = int(TOTAL_SAMPLES * TEXT_PERCENTAGE / 100)
SPECIAL_SAMPLES = TOTAL_SAMPLES - TEXT_SAMPLES


def run_generator(script_name, num_samples):
    with open(script_name, "r") as f:
        content = f.read()

    content = re.sub(r"NUM_IMAGES = \d+", f"NUM_IMAGES = {num_samples}", content)

    temp_file = f"_temp_{script_name}"
    with open(temp_file, "w") as f:
        f.write(content)

    subprocess.run([sys.executable, temp_file])
    os.remove(temp_file)


if __name__ == "__main__":
    if TEXT_SAMPLES > 0:
        run_generator("text_generator.py", TEXT_SAMPLES)

    if SPECIAL_SAMPLES > 0:
        run_generator("special_generator.py", SPECIAL_SAMPLES)
