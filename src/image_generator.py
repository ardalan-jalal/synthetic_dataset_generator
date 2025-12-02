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
            # Use preprocessed files if enabled
            if (
                hasattr(self.config.input, "use_preprocessed")
                and self.config.input.use_preprocessed
            ):
                self.input_file = Path(self.config.input.processed_dir) / "text.txt"
                self.use_metadata = True
            else:
                self.input_file = Path(self.config.input.text_file)
                self.use_metadata = False
            self.max_line_length = self.config.text_processing.max_line_length_text
            self.prefix = "t"  # Text prefix
        else:
            self.input_file = Path(self.config.input.special_file)
            self.max_line_length = self.config.text_processing.max_line_length_special
            self.prefix = "s"  # Special prefix
            self.use_metadata = False

        # Load configuration
        self._load_settings()

        # Initialize state
        self.font_files = []
        self.font_to_index = {}
        self.texts = []
        self.text_metadata = []  # Metadata for chunk tracking
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

    def _infer_font_style_from_name(self, family_style_name: str) -> str:
        """Infer style from a font's style name string."""
        name = family_style_name.lower()
        has_bold = "bold" in name
        has_italic = "italic" in name or "oblique" in name
        if has_bold and has_italic:
            return "bold_italic"
        if has_bold:
            return "bold"
        if has_italic:
            return "italic"
        return "regular"

    def _infer_font_style_from_filename(self, font_path: Path) -> str:
        """Infer style from the font file name when metadata is unavailable."""
        filename = font_path.name.lower()
        # Normalize common joined variants
        if "bolditalic" in filename or "bold_italic" in filename or "bi" in filename:
            return "bold_italic"
        if "bold" in filename:
            return "bold"
        if (
            "italic" in filename
            or "oblique" in filename
            or filename.endswith("i.ttf")
            or filename.endswith("i.otf")
        ):
            return "italic"
        # Many files explicitly include "regular"; otherwise default to regular
        return "regular"

    def _infer_font_style(self, font_path: Path) -> str:
        """Infer font style using font metadata if possible, otherwise filename."""
        try:
            font = ImageFont.truetype(str(font_path), 12)
            family, style = font.getname()
            return self._infer_font_style_from_name(style)
        except Exception:
            return self._infer_font_style_from_filename(font_path)

    def _save_font_index(self):
        """Save font index mapping to JSON"""
        font_mapping = {}
        style_counts = {"regular": 0, "bold": 0, "italic": 0, "bold_italic": 0}
        for font_path_str, idx in self.font_to_index.items():
            font_path = Path(font_path_str)
            style = self._infer_font_style(font_path)
            style_counts[style] = style_counts.get(style, 0) + 1
            font_mapping[f"f{idx:02d}"] = {
                "font_file": font_path.name,
                "index": idx,
                "style": style,
            }

        font_index_file = self.font_dir / "font_index.json"
        with open(font_index_file, "w", encoding="utf-8") as f:
            json.dump(font_mapping, f, indent=2, ensure_ascii=False)

        logger.debug(f"Font index saved to {font_index_file}")
        logger.info(
            "Font styles distribution - regular: %d, bold: %d, italic: %d, bold_italic: %d",
            style_counts.get("regular", 0),
            style_counts.get("bold", 0),
            style_counts.get("italic", 0),
            style_counts.get("bold_italic", 0),
        )

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

        # If using preprocessed files, load metadata
        if self.use_metadata:
            metadata_file = Path(self.config.input.processed_dir) / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata_list = json.load(f)
                # Store metadata indexed by chunk_id
                self.text_metadata = {m["chunk_id"]: m for m in metadata_list}
                self.texts = raw_texts  # Already chunked
                logger.info(
                    f"Loaded {len(raw_texts)} preprocessed chunks with metadata"
                )
            else:
                logger.warning(
                    f"Metadata file not found at {metadata_file}, using default chunking"
                )
                self.use_metadata = False
                self._load_texts_default(raw_texts)
        else:
            self._load_texts_default(raw_texts)

    def _load_texts_default(self, raw_texts):
        """Load texts with default splitting (no metadata)"""
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
        """Generate a single image with ground truth and character boxes"""
        # Calculate optimal font size
        optimal_font_size = self._get_optimal_font_size(font_path, text)
        font = ImageFont.truetype(str(font_path), optimal_font_size)

        # Calculate image dimensions
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Handle edge case: if text_width is 0 (e.g., only spaces), use minimum width
        if text_width == 0:
            text_width = len(text) * (
                font.size // 4
            )  # Estimate based on character count

        # Handle edge case: if text_height is 0, use font size
        if text_height == 0:
            text_height = font.size

        img_width = text_width + (self.padding * 2)
        img_height = max(
            text_height + (self.padding * 2),
            self.target_text_height + (self.padding * 2),
        )

        # Create image with text
        img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y_offset = (img_height - text_height) // 2 - bbox[1]

        # Compute character boxes BEFORE augmentation/background
        # For RTL text, PIL renders starting at self.padding and extends rightward
        # The rightmost position is self.padding + text_width
        x_end = self.padding + text_width  # Rightmost position for RTL
        character_boxes = self._compute_character_boxes_rtl(
            text, font, x_end, y_offset, img_height
        )

        # Render text
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

        # Determine chunk number (from metadata if available, otherwise default to 01)
        chunk_num = 1  # Default
        if self.use_metadata and counter in self.text_metadata:
            chunk_num = self.text_metadata[counter]["chunk_num"]

        # Save image, ground truth, and box file
        filename = f"{prefix}{counter:04d}c{chunk_num:02d}f{font_index:02d}"
        img_path = self.output_dir / f"{filename}.tif"
        gt_path = self.output_dir / f"{filename}.gt.txt"
        box_path = self.output_dir / f"{filename}.box"

        img.save(str(img_path), dpi=(300, 300))

        with open(gt_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Write .box file in Tesseract format: <char> left bottom right top 0
        with open(box_path, "w", encoding="utf-8") as f:
            for char, left, bottom, right, top in character_boxes:
                f.write(f"{char} {left} {bottom} {right} {top} 0\n")

    def _get_optimal_font_size(self, font_path: Path, sample_text: str) -> int:
        """Calculate font size that produces text close to target height"""
        for size in range(20, 100):
            test_font = ImageFont.truetype(str(font_path), size)
            bbox = test_font.getbbox(sample_text)
            text_height = bbox[3] - bbox[1]
            if text_height >= self.target_text_height:
                return size
        return 32  # Default fallback

    def _compute_character_boxes_rtl(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        x_end: int,
        y_offset: int,
        img_height: int,
    ) -> List[Tuple[str, int, int, int, int]]:
        """
        Compute character-level bounding boxes for RTL text.

        For RTL text, PIL renders from right to left. The x_end parameter is where
        the text ends (rightmost position), and text extends leftward from there.

        Args:
            text: The text string
            font: PIL ImageFont object
            x_end: Rightmost x position where RTL text ends (self.padding)
            y_offset: Y offset for text baseline
            img_height: Image height for coordinate conversion

        Returns:
            List of tuples: (char, left, bottom, right, top) in Tesseract format
            Coordinates are in Tesseract format (bottom-left origin)
            Spaces are skipped (no box entry)
        """
        boxes = []

        # Create a temporary image and draw context for accurate measurements
        temp_img = Image.new("RGB", (2000, 200), color=(255, 255, 255))
        temp_draw = ImageDraw.Draw(temp_img)

        # For RTL text, the rendering position (x_end) is where text ENDS
        # We need to find where text STARTS (leftmost position)
        full_bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = full_bbox[2] - full_bbox[0]
        x_start = x_end - text_width  # Leftmost position where text starts

        # Process characters from right to left (RTL)
        # Build text progressively from the end, measuring cumulative positions
        suffix = ""
        x_pos = x_end  # Start from rightmost position

        for char in reversed(text):
            if char == " ":
                # For spaces, measure width and create a box entry
                # Spaces don't render a visible glyph but still need box entries
                with_space = " " + suffix
                bbox_with = temp_draw.textbbox((0, 0), with_space, font=font)
                width_with = bbox_with[2] - bbox_with[0]

                bbox_without = (
                    temp_draw.textbbox((0, 0), suffix, font=font)
                    if suffix
                    else (0, 0, 0, 0)
                )
                width_without = bbox_without[2] - bbox_without[0]

                space_width = width_with - width_without
                if space_width <= 0:
                    space_width = max(1, font.size // 4)

                # For spaces, create a box entry (no visible glyph, but still in .box file)
                # Use the same vertical bounds as surrounding text
                # Get baseline and typical character height for spacing
                char_bbox = temp_draw.textbbox(
                    (0, 0), "ا", font=font
                )  # Use a typical character for height
                char_top = char_bbox[1]
                char_bottom = char_bbox[3]

                # Space box: ends at x_pos, starts at x_pos - space_width
                space_right = x_pos
                space_left = x_pos - space_width

                # PIL coordinates (top-left origin)
                pil_top = y_offset + char_top
                pil_bottom = y_offset + char_bottom

                # Convert to Tesseract coordinates (bottom-left origin)
                tesseract_left = space_left
                tesseract_bottom = img_height - pil_bottom
                tesseract_right = space_right
                tesseract_top = img_height - pil_top

                # Ensure coordinates are valid
                tesseract_left = max(0, int(tesseract_left))
                tesseract_bottom = max(0, int(tesseract_bottom))
                tesseract_right = max(tesseract_left + 1, int(tesseract_right))
                tesseract_top = max(tesseract_bottom + 1, int(tesseract_top))

                boxes.append(
                    (
                        " ",  # Space character
                        tesseract_left,
                        tesseract_bottom,
                        tesseract_right,
                        tesseract_top,
                    )
                )

                # Advance position leftward (for RTL)
                x_pos = space_left
                suffix = with_space
            else:
                # Measure this character's position
                char_text = char + suffix
                char_bbox = temp_draw.textbbox((0, 0), char, font=font)
                char_width = char_bbox[2] - char_bbox[0]
                char_top = char_bbox[1]
                char_bottom = char_bbox[3]

                # For RTL, character ends at x_pos, starts at x_pos - char_width
                char_right = x_pos
                char_left = x_pos - char_width

                # PIL coordinates (top-left origin)
                pil_top = y_offset + char_top
                pil_bottom = y_offset + char_bottom

                # Convert to Tesseract coordinates (bottom-left origin)
                tesseract_left = char_left
                tesseract_bottom = img_height - pil_bottom
                tesseract_right = char_right
                tesseract_top = img_height - pil_top

                # Ensure coordinates are valid
                tesseract_left = max(0, int(tesseract_left))
                tesseract_bottom = max(0, int(tesseract_bottom))
                tesseract_right = max(tesseract_left + 1, int(tesseract_right))
                tesseract_top = max(tesseract_bottom + 1, int(tesseract_top))

                boxes.append(
                    (
                        char,
                        tesseract_left,
                        tesseract_bottom,
                        tesseract_right,
                        tesseract_top,
                    )
                )

                # Move position left for next character (RTL)
                x_pos = char_left
                suffix = char_text

        # Reverse to match text order (we processed RTL, but .box should match .gt.txt)
        boxes.reverse()
        return boxes
