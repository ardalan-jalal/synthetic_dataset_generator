"""
Main controller for OCR dataset generation
Orchestrates text and special character image generation
"""
import logging
import sys
from pathlib import Path
from src.config_loader import load_config
from src.image_generator import OCRImageGenerator

import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/generation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main generation workflow"""
    try:
        # Load configuration
        config = load_config("config.yaml")
        config.print_summary()

        # Calculate samples
        total_samples = config.dataset.total_samples
        text_percentage = config.dataset.text_percentage
        text_samples = int(total_samples * text_percentage / 100)
        special_samples = total_samples - text_samples

        print(f"\n📝 Generating {text_samples:,} text images...")
        print(f"🔢 Generating {special_samples:,} special images...\n")

        # Generate text images
        if text_samples > 0:
            print("=" * 70)
            print("GENERATING TEXT IMAGES")
            print("=" * 70)

            text_gen = OCRImageGenerator(config=config, mode="text")
            text_gen.setup()
            text_stats = text_gen.generate(text_samples)

            logger.info(f"Text generation stats: {text_stats}")

        # Generate special images
        if special_samples > 0:
            print("\n" + "=" * 70)
            print("GENERATING SPECIAL CHARACTER IMAGES")
            print("=" * 70)

            special_gen = OCRImageGenerator(config=config, mode="special")
            special_gen.setup()
            special_stats = special_gen.generate(special_samples)

            logger.info(f"Special generation stats: {special_stats}")

        # Final summary
        print("\n" + "=" * 70)
        print("✅ GENERATION COMPLETE!")
        print("=" * 70)
        print(f"Total images created: {total_samples:,}")
        print(f"  ├─ Text images: {text_samples:,}")
        print(f"  └─ Special images: {special_samples:,}")
        print(f"\nOutput directory: {config.dataset.output_dir}/")
        print(f"Configuration used: config/config.yaml")
        print(f"Log file: logs/generation.log")
        print("=" * 70)

    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("See logs/generation.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
