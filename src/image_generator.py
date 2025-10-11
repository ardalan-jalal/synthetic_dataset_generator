"""
Unified OCR image generator - handles both text and special character generation
"""

from PIL import Image, ImageDraw, ImageFont
import os
import random
import glob
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from src.config_loader import get_config
from src.background_augmentation import apply_realistic_background
from src.augmentation import augment_image
from src.text_processing import split_long_lines


logger = logging.getLogger(__name__)


class OCRImageGenerator:
    """Generates synthetic OCR training images with ground truth"""

    def __init__(self, config=None, mode="text"):
        """
        Initialize generator

        Args:
            config: Configuration object (loads default if None)
            mode: "text" or "special" - determines input file and naming prefix
        """
        self.config = config or get_config()
        self.mode = mode.lower()

        if self.mode not in ["text", "special"]:
            raise ValueError(f"Mode must be 'text' or 'special', got: {mode}")

        # Set paths based on mode
        self.output_dir = Path(self.config.dataset.output_dir)
        self.font_dir = Path(self.config.fonts.directory)

        # Input file selection
        if self.mode == "text":
            self.input_file = Path(self.config.input.text_file)
            self.max_line_length = self.config.text_processing.max_line_length_text
            self.prefix = "t"  # Text prefix
        else:
            self.input_file = Path(self.config.input.special_file)
            self.max_line_length = self.config.text_processing.max_line_length_special
            self.prefix = "s"  # Special prefix

        # Load configuration
        self._load_settings()

        # Initialize state
        self.font_files = []
        self.font_to_index = {}
        self.texts = []
        self.generated_combinations = set()

    def _load_settings(self):
        """Load all settings from config"""
        self.target_text_height = self.config.fonts.target_text_height
        self.padding = self.config.fonts.padding
        self.augmentation_percentage = self.config.augmentation.percentage
        self.background_percentage = self.config.background.percentage
        self.background_intensity = self.config.background.intensity
        self.progress_interval = self.config.output.progress_interval
        self.random_seed = self.config.advanced.random_seed

    def setup(self):
        """Setup generator - load fonts, texts, create directories"""
        logger.info(f"Setting up {self.mode} generator...")

        # Set random seed
        if self.random_seed is not None:
            random.seed(self.random_seed)
            logger.info(f"Random seed set to: {self.random_seed}")
        else:
            random.seed()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")

        # Load fonts
        self._load_fonts()

        # Load texts
        self._load_texts()

        logger.info(
            f"Setup complete: {len(self.font_files)} fonts, {len(self.texts)} text samples"
        )

    def _load_fonts(self):
        """Load and index all font files"""
        patterns = ["*.ttf", "*.TTF", "*.otf", "*.OTF"]
        self.font_files = []

        for pattern in patterns:
            self.font_files.extend(self.font_dir.glob(pattern))

        # Sort for consistent indexing
        self.font_files = sorted(self.font_files)

        if not self.font_files:
            raise FileNotFoundError(
                f"No font files found in {self.font_dir}. "
                f"Please add .ttf or .otf files to the fonts directory."
            )

        # Create font-to-index mapping (1-based)
        self.font_to_index = {
            str(font_path): idx + 1 for idx, font_path in enumerate(self.font_files)
        }

        # Save font index
        self._save_font_index()

        logger.info(
            f"Loaded {len(self.font_files)} fonts: {[f.name for f in self.font_files]}"
        )

    def _save_font_index(self):
        """Save font index mapping to JSON"""
        font_mapping = {
            f"f{idx:02d}": {
                "font_file": Path(font_path).name,
                "index": idx,
            }
            for font_path, idx in self.font_to_index.items()
        }

        font_index_file = self.font_dir / "font_index.json"
        with open(font_index_file, "w", encoding="utf-8") as f:
            json.dump(font_mapping, f, indent=2, ensure_ascii=False)

        logger.debug(f"Font index saved to {font_index_file}")

    def _load_texts(self):
        """Load and preprocess text samples"""
        if not self.input_file.exists():
            raise FileNotFoundError(
                f"Input file not found: {self.input_file}. "
                f"Please create the file with text samples."
            )

        with open(self.input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter empty lines
        raw_texts = [line.strip() for line in lines if line.strip()]

        if not raw_texts:
            raise ValueError(f"No valid text found in {self.input_file}")

        # Split long lines
        self.texts = []
        for text in raw_texts:
            self.texts.extend(split_long_lines(text, self.max_line_length))

        logger.info(
            f"Loaded {len(raw_texts)} lines, expanded to {len(self.texts)} samples after splitting"
        )

    def generate(self, num_images: int) -> dict:
        """
        Generate synthetic images

        Args:
            num_images: Number of images to generate

        Returns:
            dict: Statistics about generation (successful, failed, skipped)
        """
        logger.info(f"Starting generation of {num_images} {self.mode} images...")

        # Shuffle text indices for better distribution
        shuffled_indices = list(range(len(self.texts)))
        random.shuffle(shuffled_indices)

        # Statistics
        stats = {
            "requested": num_images,
            "successful": 0,
            "skipped_duplicates": 0,
            "failed": 0,
        }

        max_attempts = num_images * 100
        attempts = 0

        while stats["successful"] < num_images and attempts < max_attempts:
            attempts += 1

            try:
                # Select text and font
                text_index = shuffled_indices[stats["successful"] % len(self.texts)]
                text = self.texts[text_index]
                font_path = random.choice(self.font_files)
                font_index = self.font_to_index[str(font_path)]

                # Check for duplicates
                combination = (text_index, font_index)
                if combination in self.generated_combinations:
                    stats["skipped_duplicates"] += 1
                    continue

                # Generate image
                self._generate_single_image(
                    text=text,
                    font_path=font_path,
                    font_index=font_index,
                    counter=stats["successful"],
                )

                # Mark as generated
                self.generated_combinations.add(combination)
                stats["successful"] += 1

                # Progress update
                if stats["successful"] % self.progress_interval == 0:
                    logger.info(
                        f"Generated {stats['successful']}/{num_images} images..."
                    )

            except Exception as e:
                logger.error(f"Failed to generate image: {e}", exc_info=True)
                stats["failed"] += 1

        # Final statistics
        if stats["successful"] < num_images:
            logger.warning(
                f"Only generated {stats['successful']}/{num_images} images. "
                f"Reached max attempts ({max_attempts}). "
                f"Consider adding more text samples or fonts."
            )

        logger.info(f"Generation complete: {stats}")
        return stats

    def _generate_single_image(
        self, text: str, font_path: Path, font_index: int, counter: int
    ):
        """Generate a single image with ground truth"""
        # Calculate optimal font size
        optimal_font_size = self._get_optimal_font_size(font_path, text)
        font = ImageFont.truetype(str(font_path), optimal_font_size)

        # Calculate image dimensions
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        img_width = text_width + (self.padding * 2)
        img_height = max(
            text_height + (self.padding * 2),
            self.target_text_height + (self.padding * 2),
        )

        # Create image with text
        img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y_offset = (img_height - text_height) // 2 - bbox[1]
        draw.text((self.padding, y_offset), text, fill=(0, 0, 0), font=font)

        # Apply augmentations
        should_augment = random.random() * 100 < self.augmentation_percentage
        if should_augment:
            img = augment_image(img)
            prefix = "a"  # Augmented
        else:
            prefix = self.prefix  # Original prefix (t or s)

        # Apply background
        should_apply_background = random.random() * 100 < self.background_percentage
        if should_apply_background:
            img = apply_realistic_background(img, intensity=self.background_intensity)

        # Save image and ground truth
        filename = f"{prefix}{counter:04d}c01f{font_index:02d}"
        img_path = self.output_dir / f"{filename}.tif"
        gt_path = self.output_dir / f"{filename}.gt.txt"

        img.save(str(img_path), dpi=(300, 300))

        with open(gt_path, "w", encoding="utf-8") as f:
            f.write(text)

    def _get_optimal_font_size(self, font_path: Path, sample_text: str) -> int:
        """Calculate font size that produces text close to target height"""
        for size in range(20, 100):
            test_font = ImageFont.truetype(str(font_path), size)
            bbox = test_font.getbbox(sample_text)
            text_height = bbox[3] - bbox[1]
            if text_height >= self.target_text_height:
                return size
        return 32  # Default fallback
