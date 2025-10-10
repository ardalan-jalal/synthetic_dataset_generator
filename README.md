# Synthetic OCR Data Generator

A Python tool for generating synthetic OCR training data for Kurdish text. This generator creates image/text pairs optimized for Tesseract LSTM training.

## Features

✨ **Automatic Font Detection** - Scans the `fonts/` directory and randomly selects fonts for each image  
✨ **Font Index Mapping** - Generates `font_index.json` with traceable font assignments  
✨ **Smart File Naming** - Compact filenames encode line number, chunk, and font index  
✨ **Duplicate Prevention** - Unique filenames prevent accidental overwrites  
✨ **Tesseract Optimized** - Follows LSTM training best practices (32px text height, proper padding)  
✨ **Ground Truth Generation** - Automatically creates `.gt.txt` files for each image  
✨ **Kurdish Text Support** - Full UTF-8 encoding support for Kurdish characters  
✨ **Dynamic Sizing** - Images automatically resize based on text length  
✨ **Line Splitting** - Intelligently splits long text at sentence boundaries  

## Project Structure

```
Synthatic_ocr_data_generator/
├── dataset/              # Generated images and ground truth files (auto-created)
│   ├── t0001c01f03.tif  # Image file (line 1, chunk 1, font 3)
│   ├── t0001c01f03.gt.txt  # Ground truth text
│   └── ...
├── fonts/               # Place your .ttf/.otf font files here
│   ├── rudaw_regular.ttf
│   ├── k24_regular.ttf
│   └── ...
├── input/
│   └── raw_text/
│       ├── text.txt     # Kurdish text samples
│       └── special.txt  # Numbers and special characters (optional)
├── dataset_generator    # Main generator script
├── font_index.json      # Font mapping reference (auto-generated)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your fonts:**
   - Place `.ttf` font files in the `fonts/` directory
   - The generator will automatically detect and use all fonts

4. **Add your text:**
   - Edit `input/raw_text/text.txt` - Kurdish text samples
   - Add `input/raw_text/special.txt` - Numbers/symbols (optional)
   - One line of text per entry
   - Supports Kurdish, Arabic, and Latin characters

## Usage

Run the generator:

```bash
python dataset_generator
```

The script will:
1. Scan all fonts in the `fonts/` directory and create `font_index.json`
2. Read text lines from `input/raw_text/text.txt` (and `special.txt` if present)
3. Split long lines intelligently at sentence boundaries
4. Generate images with randomly selected text and fonts
5. Save files with traceable naming: `t{line}c{chunk}f{font}.tif`
6. Create matching ground truth `.gt.txt` files

## Output

### File Naming Convention

Files use a compact, traceable naming scheme:

**Format:** `t{LINE}c{CHUNK}f{FONT}`

- **t{LINE}** - Original line number (4 digits, e.g., `t0042`)
- **c{CHUNK}** - Chunk number if line was split (2 digits, e.g., `c01`)
- **f{FONT}** - Font index from `font_index.json` (2 digits, e.g., `f03`)

**Examples:**
```
t0042c01f03.tif  → Line 42, Chunk 1, Font 3 (rabar_30_regular.ttf)
t0158c02f07.tif  → Line 158, Chunk 2, Font 7 (uniSalar_F_020_regular.otf)
t1234c01f12.tif  → Line 1234, Chunk 1, Font 12 (unikurd_hejar_regular.ttf)
```

### Font Index Mapping

The generator creates `font_index.json` to map font codes to actual fonts:

```json
{
  "f01": {
    "font_file": "k24_regular.ttf",
    "index": 1
  },
  "f02": {
    "font_file": "nrt_regular.ttf",
    "index": 2
  },
  ...
}
```

### Output Structure

Each text generates a pair of files:

```
dataset/
├── font_index.json       # Font mapping reference
├── t0001c01f01.tif      # Image file
├── t0001c01f01.gt.txt   # Ground truth text
├── t0001c01f02.tif      # Same line, different font
├── t0001c01f02.gt.txt
└── ...
```

**Benefits:**
- ✅ No duplicate combinations (each line+font pair is unique)
- ✅ Full traceability back to source line and font
- ✅ Compact filenames (15 characters)
- ✅ Easy to verify dataset coverage

## Tesseract Training

The generated data is optimized for Tesseract LSTM training:

- Text height: **32 pixels** (optimal range: 30-48px for LSTM)
- Padding: **10 pixels** minimum on all sides
- Format: Single-line images with corresponding `.gt.txt` files
- White background, black text
- TIFF format at 300 DPI
- Smart line splitting at 100 characters (sentence-aware)

To use with Tesseract training tools:
```bash
# Example using tesstrain
lstmtraining --traineddata your_model.traineddata \
             --train_listfile dataset/train.txt \
             --model_output output/model
```

## Configuration

Edit these constants in `dataset_generator` to customize:

```python
NUM_IMAGES = 10              # Total images to generate
MAX_LINE_LENGTH = 100        # Max characters per line before splitting
TARGET_TEXT_HEIGHT = 32      # Text height in pixels (30-48 recommended)
PADDING = 10                 # Padding around text in pixels
```

### Recommended Dataset Sizes

| Images | Quality Level | Use Case |
|--------|---------------|----------|
| 1,000-2,000 | Basic | Testing/prototyping |
| 8,000-10,000 | Good | Small production |
| 25,000-50,000 | Excellent | Professional OCR |
| 100,000+ | Optimal | High-quality production |

**Note:** With 1,622 unique text lines and 16 fonts, you can generate up to 25,952 unique combinations (without splits). More images = better font coverage per text line.

## Requirements

- Python 3.6+
- Pillow (PIL) 10.0.0+

## Troubleshooting

**Q: How do I decode a filename like `t0158c02f07.tif`?**

A: Check `font_index.json`:
- `t0158` = Line 158 from input text file
- `c02` = Second chunk (if the line was split)
- `f07` = Font 7 (look up "f07" in font_index.json)

**Q: How many images should I generate?**

A: For Kurdish OCR training:
- Minimum: 8,000-10,000 images
- Recommended: 25,000-50,000 images
- Professional: 100,000+ images

**Q: Can I add more text files?**

A: Yes! Edit line 93 in `dataset_generator` to include additional files from `input/raw_text/`.

## License

Free to use for OCR training and research purposes.
