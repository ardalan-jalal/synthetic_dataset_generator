from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import random
import glob
import re
import json
import numpy as np
from background_augmentation import apply_realistic_background

# Seed random for better randomization across runs
random.seed()

# Directory to save synthetic images
OUTPUT_DIR = "dataset"
FONT_DIR = "fonts"
TEXT_DIR = "input/raw_text"

# Number of images to generate
NUM_IMAGES = 500  # Set this to control how many images you want to generate

# Maximum characters per line Lines longer than this will be split
MAX_LINE_LENGTH = 20

# AUGMENTATION CONTROL
AUGMENTATION_PERCENTAGE = 30  # Percentage of images to augment (0-100)
# Recommended: 30% for mixed quality (scans + screenshots), 0% for clean only, 50% for heavy variance

# BACKGROUND AUGMENTATION CONTROL
BACKGROUND_AUGMENTATION_PERCENTAGE = (
    70  # Percentage of images to get realistic backgrounds (0-100)
)
# Recommended: 70% for realistic scanned documents, 0% for clean white backgrounds
BACKGROUND_INTENSITY = "medium"  # Options: 'light', 'medium', 'heavy'


# Split long lines into manageable chunks for better training
def split_long_lines(text, max_length=100):
    """Split text into chunks at sentence boundaries for realistic line lengths"""
    if len(text) <= max_length:
        return [text]

    # Step 1: Try splitting on punctuation boundaries
    # Kurdish/Arabic punctuation: ، (comma), ؛ (semicolon), . ! ?
    sentences = re.split(r"([.!?،؛])\s+", text)

    chunks = []
    current_chunk = ""

    for part in sentences:
        # Check if it's a punctuation mark
        if part in ".!?،؛":
            current_chunk += part
        else:
            # If adding this would exceed max length, save current chunk
            if current_chunk and len(current_chunk) + len(part) + 1 > max_length:
                chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk += (
                    (" " + part)
                    if current_chunk
                    and not current_chunk.endswith((".", "!", "?", "،", "؛"))
                    else part
                )

    # Add the last chunk
    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Step 2: CRITICAL - Validate and force-split any chunk still exceeding max_length
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            # Split on word boundaries
            words = chunk.split()
            temp_line = ""

            for word in words:
                # Check if adding this word would exceed limit
                test_line = (temp_line + " " + word) if temp_line else word

                if len(test_line) <= max_length:
                    temp_line = test_line
                else:
                    # Save current line if it exists
                    if temp_line:
                        final_chunks.append(temp_line)
                        temp_line = word
                    else:
                        # Single word exceeds max_length - hard split it
                        final_chunks.append(word[:max_length])
                        temp_line = word[max_length:]

            # Don't forget the last line
            if temp_line:
                final_chunks.append(temp_line)

    # Fallback: if somehow still empty, hard split original text
    return (
        final_chunks
        if final_chunks
        else [text[i : i + max_length] for i in range(0, len(text), max_length)]
    )


# Augmentation functions for realistic document variations
def add_noise(image, noise_level=0.01):
    """Add Gaussian noise to simulate scan artifacts"""
    img_array = np.array(image)
    noise = np.random.normal(0, noise_level * 255, img_array.shape)
    noisy = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


def rotate_image(image, angle_range=(-2, 2)):
    """Apply slight rotation to simulate scan skew"""
    angle = random.uniform(*angle_range)
    return image.rotate(angle, fillcolor=(255, 255, 255), expand=True)


def adjust_brightness(image, factor_range=(0.88, 1.12)):
    """Adjust brightness to simulate lighting variations"""
    factor = random.uniform(*factor_range)
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image, factor_range=(0.9, 1.1)):
    """Adjust contrast to simulate scan quality variations"""
    factor = random.uniform(*factor_range)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def add_blur(image, radius_range=(0.5, 0.8)):
    """Add slight blur to simulate scan quality"""
    radius = random.uniform(*radius_range)
    return image.filter(ImageFilter.GaussianBlur(radius))


def augment_image(image):
    """
    Apply moderate augmentation for scanned paper simulation
    Randomly applies 2-4 different augmentations
    """
    augmented = image.copy()
    augmentations_applied = 0

    # Rotation (70% chance) - typical scan skew
    if random.random() < 0.7:
        augmented = rotate_image(augmented)
        augmentations_applied += 1

    # Noise (50% chance) - scan artifacts
    if random.random() < 0.5:
        augmented = add_noise(augmented, noise_level=0.01)
        augmentations_applied += 1

    # Blur (50% chance) - scan quality
    if random.random() < 0.5:
        augmented = add_blur(augmented)
        augmentations_applied += 1

    # Brightness (60% chance) - lighting differences
    if random.random() < 0.6:
        augmented = adjust_brightness(augmented)
        augmentations_applied += 1

    # Contrast (40% chance) - scan quality variations
    if random.random() < 0.4:
        augmented = adjust_contrast(augmented)
        augmentations_applied += 1

    return augmented


# Read special characters/numbers from input file
text_file_path = os.path.join(TEXT_DIR, "special.txt")
with open(text_file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Filter out empty lines and strip whitespace
raw_texts = [line.strip() for line in lines if line.strip()]

# For special characters, usually don't need to split since they're short
# But we keep the functionality in case
texts = []
for text in raw_texts:
    # Most special chars are short, so just add them directly
    if len(text) <= MAX_LINE_LENGTH:
        texts.append(text)
    else:
        # Only split if needed
        texts.extend(split_long_lines(text, MAX_LINE_LENGTH))

# Get all font files from fonts directory
font_files = (
    glob.glob(os.path.join(FONT_DIR, "*.ttf"))
    + glob.glob(os.path.join(FONT_DIR, "*.TTF"))
    + glob.glob(os.path.join(FONT_DIR, "*.otf"))
)
# Sort fonts alphabetically for consistent indexing
font_files = sorted(font_files)

# Create font-to-index mapping (1-based)
font_to_index = {font_path: idx + 1 for idx, font_path in enumerate(font_files)}

# Prepare font mapping for JSON
font_mapping = {
    f"f{idx:02d}": {
        "font_file": os.path.basename(font_path),
        "index": idx,
    }
    for font_path, idx in font_to_index.items()
}

# Save font index to JSON file
font_index_file = os.path.join("font_index.json")
with open(font_index_file, "w", encoding="utf-8") as f:
    json.dump(font_mapping, f, indent=2, ensure_ascii=False)


if not font_files:
    raise ValueError(f"No .ttf or .otf font files found in {FONT_DIR} directory")
print(f"Found {len(font_files)} fonts: {[os.path.basename(f) for f in font_files]}")

# Tesseract LSTM best practices
TARGET_TEXT_HEIGHT = 32  # Optimal text height for Tesseract (30-33px recommended)
PADDING = 10  # Padding around text (minimum 5-10px recommended)


# Find optimal font size to achieve target text height
def get_optimal_font_size(font_path, sample_text, target_height):
    """Calculate font size that produces text close to target height"""
    font_size = 32
    for size in range(20, 100):
        test_font = ImageFont.truetype(font_path, size)
        bbox = test_font.getbbox(sample_text)
        text_height = bbox[3] - bbox[1]
        if text_height >= target_height:
            return size
    return font_size


# Generate images - shuffle texts for better distribution
shuffled_indices = list(range(len(texts)))
random.shuffle(shuffled_indices)  # Randomize order

# Track combinations to prevent duplicates (same text + same font)
generated_combinations = set()
i = 0
attempts = 0
max_attempts = NUM_IMAGES * 100  # Safety limit

while i < NUM_IMAGES and attempts < max_attempts:
    # Pick from shuffled list (no duplicates until all texts are used)
    text_index = shuffled_indices[i % len(texts)]
    text = texts[text_index]

    # Randomly select a font for this image
    selected_font_path = random.choice(font_files)
    font_name = os.path.basename(selected_font_path)
    font_index = font_to_index[selected_font_path]  # Get font index

    # Check if this exact combination (text + font) already exists
    combination = (text_index, font_index)
    if combination in generated_combinations:
        attempts += 1
        continue  # Skip this duplicate and try again

    # Mark this combination as used
    generated_combinations.add(combination)

    # Calculate optimal font size for the selected font
    optimal_font_size = get_optimal_font_size(
        selected_font_path, text, TARGET_TEXT_HEIGHT
    )
    font = ImageFont.truetype(selected_font_path, optimal_font_size)

    # Calculate image size based on text length
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Add padding (2x on each side for safety)
    img_width = text_width + (PADDING * 2)
    img_height = text_height + (PADDING * 2)

    # Ensure minimum height for consistency
    if img_height < TARGET_TEXT_HEIGHT + (PADDING * 2):
        img_height = TARGET_TEXT_HEIGHT + (PADDING * 2)

    # Create a white background image
    img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))

    # Draw text on image (center vertically accounting for font bbox offset)
    draw = ImageDraw.Draw(img)
    # Account for the bounding box top offset for proper centering
    y_offset = (img_height - text_height) // 2 - bbox[1]
    draw.text((PADDING, y_offset), text, fill=(0, 0, 0), font=font)

    # Apply other augmentations FIRST (rotation, blur, etc. on white background)
    should_augment = random.random() * 100 < AUGMENTATION_PERCENTAGE
    if should_augment:
        img = augment_image(img)
        prefix = "a"  # Augmented
    else:
        prefix = "s"  # Clean special

    # Apply realistic background augmentation LAST (after rotation)
    # This way the background covers the entire rotated image including corners
    should_apply_background = random.random() * 100 < BACKGROUND_AUGMENTATION_PERCENTAGE
    if should_apply_background:
        img = apply_realistic_background(img, intensity=BACKGROUND_INTENSITY)

    # Create filename with unique counter to avoid overwrites
    filename = f"{prefix}{i:04d}c01f{font_index:02d}"

    # Save the image
    img_path = os.path.join(OUTPUT_DIR, f"{filename}.tif")
    img.save(img_path, dpi=(300, 300))

    # Save ground truth text file
    gt_path = os.path.join(OUTPUT_DIR, f"{filename}.gt.txt")
    with open(gt_path, "w", encoding="utf-8") as gt_file:
        gt_file.write(text)

    # Increment counter only after successful generation
    i += 1

    # Progress indicator
    if i % 50 == 0:
        print(f"Generated {i}/{NUM_IMAGES} special images...")
