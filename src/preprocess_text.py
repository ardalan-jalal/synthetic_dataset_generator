"""
Text preprocessing module for OCR dataset generation
Controlled via config.yaml preprocessing section

Run standalone: python -m src.preprocess_text
Or call from code: from src.preprocess_text import preprocess_if_needed
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from src.config_loader import load_config
from src.text_processing import split_long_lines

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocesses raw text files into chunked format with metadata"""

    def __init__(self, config):
        """
        Initialize preprocessor

        Args:
            config: Configuration object
        """
        self.config = config
        self.raw_text_dir = Path(config.input.raw_text_dir)
        self.processed_dir = Path(config.input.processed_dir)
        self.max_chars_text = config.text_processing.max_line_length_text
        self.max_chars_special = config.text_processing.max_line_length_special

        # Preprocessing settings
        if hasattr(config, "preprocessing"):
            self.save_stats = config.preprocessing.save_stats
            self.overwrite = config.preprocessing.overwrite_existing
        else:
            self.save_stats = True
            self.overwrite = False

    def preprocess_text_files(self) -> Dict:
        """
        Process all text files from raw_text directory

        Returns:
            dict: Statistics about preprocessing
        """
        logger.info("Starting text preprocessing...")

        # Check if already processed
        if not self.overwrite and (self.processed_dir / "text.txt").exists():
            logger.info(
                "Preprocessed files already exist. Set overwrite_existing: true to regenerate."
            )
            return {"status": "skipped", "reason": "already_exists"}

        # Create output directory
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Find all text files in raw_text directory
        text_files = list(self.raw_text_dir.glob("*.txt"))

        if not text_files:
            raise FileNotFoundError(
                f"No .txt files found in {self.raw_text_dir}. "
                f"Please add text files to preprocess."
            )

        logger.info(f"Found {len(text_files)} text file(s) to process")

        # Process each file
        all_chunks = []
        all_metadata = []
        stats = {
            "total_files": len(text_files),
            "total_raw_lines": 0,
            "total_chunks": 0,
            "chunk_distribution": {},
        }

        for text_file in text_files:
            chunks, metadata, file_stats = self._process_single_file(
                text_file, len(all_chunks)
            )
            all_chunks.extend(chunks)
            all_metadata.extend(metadata)

            stats["total_raw_lines"] += file_stats["raw_lines"]

            # Update chunk distribution
            for num_chunks, count in file_stats["chunk_counts"].items():
                stats["chunk_distribution"][num_chunks] = (
                    stats["chunk_distribution"].get(num_chunks, 0) + count
                )

        stats["total_chunks"] = len(all_chunks)

        # Save processed text and metadata
        self._save_processed_data(all_chunks, all_metadata, stats)

        logger.info(f"Preprocessing complete: {stats}")
        return stats

    def _process_single_file(
        self, text_file: Path, chunk_offset: int
    ) -> Tuple[List[str], List[Dict], Dict]:
        """
        Process a single text file

        Args:
            text_file: Path to text file
            chunk_offset: Starting chunk index

        Returns:
            Tuple of (chunks, metadata, stats)
        """
        logger.info(f"Processing {text_file.name}...")

        with open(text_file, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        # Filter empty lines
        raw_lines = [line.strip() for line in raw_lines if line.strip()]

        chunks = []
        metadata = []
        chunk_counts = {}

        for line_idx, raw_line in enumerate(raw_lines):
            # Split line into chunks
            line_chunks = split_long_lines(raw_line, self.max_chars_text)

            # Track chunk distribution
            num_chunks = len(line_chunks)
            chunk_counts[num_chunks] = chunk_counts.get(num_chunks, 0) + 1

            # Add chunks and metadata
            for chunk_num, chunk in enumerate(line_chunks, start=1):
                chunk_id = len(chunks) + chunk_offset
                chunks.append(chunk)

                metadata.append(
                    {
                        "chunk_id": chunk_id,
                        "original_file": text_file.name,
                        "original_line_num": line_idx + 1,
                        "chunk_num": chunk_num,
                        "total_chunks": num_chunks,
                        "char_count": len(chunk),
                        "original_text": (
                            raw_line if num_chunks > 1 else None
                        ),  # Only store if split
                    }
                )

        stats = {
            "raw_lines": len(raw_lines),
            "chunks": len(chunks),
            "chunk_counts": chunk_counts,
        }

        logger.info(
            f"  {text_file.name}: {stats['raw_lines']} lines → {stats['chunks']} chunks"
        )

        return chunks, metadata, stats

    def _save_processed_data(
        self, chunks: List[str], metadata: List[Dict], stats: Dict
    ):
        """Save processed chunks, metadata, and statistics"""

        # Save chunked text
        text_output = self.processed_dir / "text.txt"
        with open(text_output, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(chunk + "\n")

        logger.info(f"Saved {len(chunks)} chunks to {text_output}")

        # Save metadata
        metadata_output = self.processed_dir / "metadata.json"
        with open(metadata_output, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved metadata to {metadata_output}")

        # Save statistics (if enabled)
        if not self.save_stats:
            return

        # Save statistics report
        stats_output = self.processed_dir / "preprocessing_stats.txt"
        with open(stats_output, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("TEXT PREPROCESSING STATISTICS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Max characters per chunk: {self.max_chars_text}\n\n")

            f.write(f"Total files processed: {stats['total_files']}\n")
            f.write(f"Total raw lines: {stats['total_raw_lines']}\n")
            f.write(f"Total chunks created: {stats['total_chunks']}\n")
            f.write(
                f"Expansion factor: {stats['total_chunks'] / stats['total_raw_lines']:.2f}x\n\n"
            )

            f.write("Chunk Distribution:\n")
            f.write("-" * 70 + "\n")
            for num_chunks in sorted(stats["chunk_distribution"].keys()):
                count = stats["chunk_distribution"][num_chunks]
                percentage = (count / stats["total_raw_lines"]) * 100
                f.write(
                    f"  {num_chunks} chunk(s): {count:5} lines ({percentage:5.2f}%)\n"
                )

            f.write("\n" + "=" * 70 + "\n")

        logger.info(f"Saved statistics to {stats_output}")

        # Also save a JSON version for programmatic access
        stats_json = self.processed_dir / "preprocessing_stats.json"
        stats_data = {
            "generated_at": datetime.now().isoformat(),
            "max_chars": self.max_chars_text,
            "stats": stats,
        }
        with open(stats_json, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

    def print_summary(self, stats: Dict):
        """Print preprocessing summary to console"""
        print("\n" + "=" * 70)
        print("📊 PREPROCESSING SUMMARY")
        print("=" * 70)
        print(f"Files processed: {stats['total_files']}")
        print(f"Raw lines: {stats['total_raw_lines']:,}")
        print(f"Chunks created: {stats['total_chunks']:,}")
        print(f"Expansion: {stats['total_chunks'] / stats['total_raw_lines']:.2f}x\n")

        print("Chunk Distribution:")
        print("-" * 70)
        for num_chunks in sorted(stats["chunk_distribution"].keys()):
            count = stats["chunk_distribution"][num_chunks]
            percentage = (count / stats["total_raw_lines"]) * 100
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"  {num_chunks} chunk(s): {bar} {count:5} ({percentage:5.2f}%)")

        print("\n" + "=" * 70)
        print(f"✅ Output saved to: {self.processed_dir}/")
        print("=" * 70 + "\n")


def preprocess_if_needed(config, force: bool = False) -> Optional[Dict]:
    """
    Run preprocessing if enabled in config or if processed files don't exist

    Args:
        config: Configuration object
        force: Force preprocessing even if files exist

    Returns:
        Statistics dict if preprocessing ran, None if skipped
    """
    # Check if preprocessing is enabled
    preprocessing_enabled = False
    auto_run = False

    if hasattr(config, "preprocessing"):
        preprocessing_enabled = config.preprocessing.enabled
        auto_run = config.preprocessing.auto_run

    # Check if processed files exist
    processed_dir = Path(config.input.processed_dir)
    processed_exists = (processed_dir / "text.txt").exists()

    # Determine if we should run
    should_run = force or preprocessing_enabled or (auto_run and not processed_exists)

    if not should_run:
        return None

    logger.info("Running text preprocessing...")
    preprocessor = TextPreprocessor(config)
    stats = preprocessor.preprocess_text_files()

    return stats


def main():
    """Main preprocessing workflow - for standalone execution"""
    # Setup logging for standalone mode
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    print("\n" + "=" * 70)
    print("🔄 TEXT PREPROCESSING TOOL")
    print("=" * 70)
    print("Controlled by config.yaml preprocessing section\n")

    try:
        # Load configuration
        config = load_config("config.yaml")

        # Check if raw text directory exists
        raw_text_dir = Path(config.input.raw_text_dir)
        if not raw_text_dir.exists():
            print(f"\n❌ Error: Raw text directory not found: {raw_text_dir}")
            print(f"Please create the directory and add .txt files to process.")
            sys.exit(1)

        # Check if files exist
        text_files = list(raw_text_dir.glob("*.txt"))
        if not text_files:
            print(f"\n❌ Error: No .txt files found in {raw_text_dir}")
            print(f"Please add text files to preprocess.")
            sys.exit(1)

        print(f"📁 Raw text directory: {raw_text_dir}")
        print(f"📝 Found {len(text_files)} file(s) to process:")
        for f in text_files:
            print(f"   - {f.name}")

        print(
            f"\n⚙️  Max characters per chunk: {config.text_processing.max_line_length_text}"
        )
        print(f"📂 Output directory: {config.input.processed_dir}")

        # Show config settings
        if hasattr(config, "preprocessing"):
            print(f"⚙️  Config - enabled: {config.preprocessing.enabled}")
            print(f"⚙️  Config - overwrite: {config.preprocessing.overwrite_existing}")

        print()

        # Run preprocessing (force mode for standalone)
        preprocessor = TextPreprocessor(config)
        stats = preprocessor.preprocess_text_files()

        if stats.get("status") == "skipped":
            print("\n⏭️  Preprocessing skipped: Files already exist")
            print("   Set overwrite_existing: true in config.yaml to regenerate")
            return

        # Print summary
        preprocessor.print_summary(stats)

        print("✅ Preprocessing complete!")
        print("\nNext steps:")
        print("  1. Set use_preprocessed: true in config.yaml")
        print("  2. Run: python main.py")
        print()

    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
