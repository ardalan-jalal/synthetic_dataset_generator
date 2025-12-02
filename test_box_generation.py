"""
Test script to generate 1-2 sample images with .tif, .gt.txt, and .box files.
Demonstrates the character-level bounding box generation for Tesseract training.
"""

import sys
from pathlib import Path
from src.config_loader import load_config
from src.image_generator import OCRImageGenerator

def main():
    """Generate test samples with box files"""
    print("=" * 70)
    print("TEST: Character-Level Box File Generation")
    print("=" * 70)
    
    try:
        # Load configuration
        config = load_config("config.yaml")
        
        # Create a test output directory
        test_output_dir = Path("test_output")
        test_output_dir.mkdir(exist_ok=True)
        
        # Generate 2 text images
        print("\nGenerating 2 test samples...")
        text_gen = OCRImageGenerator(config=config, mode="text")
        # Override output directory after initialization
        text_gen.output_dir = test_output_dir
        text_gen.setup()
        stats = text_gen.generate(2)
        
        print(f"\n✅ Generated {stats['successful']} samples")
        print(f"\nOutput files in: {test_output_dir}/")
        
        # List generated files
        tif_files = list(test_output_dir.glob("*.tif"))
        gt_files = list(test_output_dir.glob("*.gt.txt"))
        box_files = list(test_output_dir.glob("*.box"))
        
        print(f"\nGenerated files:")
        print(f"  - {len(tif_files)} .tif files")
        print(f"  - {len(gt_files)} .gt.txt files")
        print(f"  - {len(box_files)} .box files")
        
        # Show example files
        if tif_files:
            base_name = tif_files[0].stem
            print(f"\nExample files (basename: {base_name}):")
            print(f"  - {base_name}.tif")
            print(f"  - {base_name}.gt.txt")
            print(f"  - {base_name}.box")
            
            # Show contents of .gt.txt and .box
            gt_file = test_output_dir / f"{base_name}.gt.txt"
            box_file = test_output_dir / f"{base_name}.box"
            
            if gt_file.exists():
                with open(gt_file, "r", encoding="utf-8") as f:
                    gt_text = f.read().strip()
                print(f"\n  Ground truth text: {repr(gt_text)}")
            
            if box_file.exists():
                with open(box_file, "r", encoding="utf-8") as f:
                    box_lines = f.readlines()
                print(f"\n  Box file entries: {len(box_lines)} characters")
                print(f"  First 5 box entries:")
                for i, line in enumerate(box_lines[:5]):
                    print(f"    {line.strip()}")
                if len(box_lines) > 5:
                    print(f"    ... ({len(box_lines) - 5} more entries)")
        
        print("\n" + "=" * 70)
        print("✅ Test complete! Check test_output/ directory for generated files.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

