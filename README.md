# Synthetic OCR Data Generator for Kurdish

A Python tool for generating synthetic OCR training data optimized for Kurdish text and Tesseract LSTM training. Creates high-quality image/text pairs with intelligent duplicate prevention and balanced dataset composition.

## ✨ Key Features

### Core Features
- 🎯 **Zero Duplicate Guarantee** - Prevents generating the same text+font combination twice
- 🔀 **True Random Distribution** - Shuffled selection ensures coverage across all text entries
- 📊 **Balanced Dataset Generation** - Configurable text/special character ratio based on OCR best practices
- 🎨 **Multi-Font Support** - Automatically detects all fonts and creates diverse variations
- 📝 **Dual Content Types** - Separate generators for regular text and special characters/numbers

### Technical Features
- ⚡ **Tesseract LSTM Optimized** - 32px text height, proper padding, sentence-aware splitting
- 🗂️ **Smart File Management** - Sequential naming with font tracking
- 🌐 **Kurdish/Arabic Support** - Full UTF-8 encoding with Arabic-Indic numerals
- 📈 **Progress Tracking** - Real-time generation status updates
- 🔍 **Font Index Mapping** - Traceable font assignments in JSON format

## 📁 Project Structure

```
Synthatic_ocr_data_generator/
├── dataset/                    # Generated images (auto-created)
│   ├── t0000c01f03.tif        # Text image (sequential, font 3)
│   ├── t0000c01f03.gt.txt     # Ground truth text
│   ├── s0000c01f05.tif        # Special char image (sequential, font 5)
│   ├── s0000c01f05.gt.txt     # Ground truth
│   └── ...
├── fonts/                      # Place your font files here
│   ├── k24_regular.ttf
│   ├── nrt_regular.ttf
│   ├── rudaw_regular.ttf
│   ├── unikurd_hejar_regular.ttf
│   └── ...
├── input/
│   └── raw_text/
│       ├── text.txt           # Kurdish text samples (714 lines)
│       └── special.txt        # Numbers and symbols (366 lines)
├── main.py                    # Main controller (run this!)
├── text_generator.py          # Text-only generator
├── special_generator.py       # Special chars generator
├── font_index.json            # Auto-generated font mapping
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd Synthatic_ocr_data_generator

# Install dependencies
pip install -r requirements.txt
```

**Requirements:**
- Python 3.6+
- Pillow (PIL) 10.0.0+

### 2. Add Your Fonts

Place `.ttf`, `.TTF`, or `.otf` font files in the `fonts/` directory:

```bash
fonts/
├── font1.ttf
├── font2.ttf
└── font3.otf
```

The generator automatically detects all fonts. **Recommended: 3-14 fonts** for optimal variety.

### 3. Configure Generation

Edit `main.py` (only 2 settings!):

```python
# ============================================================================
# SIMPLE CONFIGURATION
# ============================================================================
TOTAL_SAMPLES = 500        # Total number of images to generate
TEXT_PERCENTAGE = 80       # Percentage for text.txt (rest → special.txt)
# ============================================================================
```

**Examples:**
- `TOTAL_SAMPLES = 500, TEXT_PERCENTAGE = 80` → 400 text + 100 special images
- `TOTAL_SAMPLES = 3000, TEXT_PERCENTAGE = 85` → 2550 text + 450 special images

### 4. Generate Dataset

```bash
# Run the main controller (generates both text and special)
python main.py
```

**Or run generators individually:**
```bash
python text_generator.py      # Only text images
python special_generator.py   # Only special char images
```

## 📊 Dataset Composition

### Recommended Ratios (Based on OCR Best Practices)

Following document OCR research and Tesseract LSTM training guidelines:

| Type | Percentage | Use Case | Example (1000 samples) |
|------|-----------|----------|------------------------|
| Text | 80-85% | Regular Kurdish text | 800-850 images |
| Special | 15-20% | Numbers, symbols, dates | 150-200 images |

**Your current `special.txt` includes:**
- ✓ Numbers (Arabic-Indic: ١٢٣ and Latin: 123)
- ✓ Dates & times (١٥/٣/٢٠٢٤, 14:30)
- ✓ Phone numbers (٠٧٥٠١٢٣٤٥٦٧)
- ✓ Currency ($١٠٠, €٥٠, 1000 IQD)
- ✓ Percentages (٢٥٪, 50%)
- ✓ Common punctuation and symbols
- ✓ Document patterns (file names, references)

**Removed uncommon symbols:** Advanced math (∂, ∇, ∫), scientific units, IP addresses, coordinates.

### Recommended Sample Sizes

| Total Samples | Per Font | Quality | Use Case |
|--------------|----------|---------|----------|
| 500-1,000 | ~35-70 | Basic | Testing/prototyping |
| 2,000-3,000 | ~140-215 | Good | Small production |
| 5,000-10,000 | ~355-715 | Excellent | Professional OCR |
| 20,000+ | ~1,400+ | Optimal | High-quality training |

*Based on 14 fonts. More samples per font = better model accuracy.*

## 🎯 How It Works

### Duplicate Prevention System

The generator **guarantees zero duplicates** by tracking all (text + font) combinations:

```python
# Allowed ✓
Text #5 + Font A → t0000c01f01.tif  ✓ Generated
Text #5 + Font B → t0001c01f02.tif  ✓ Generated (same text, different font)
Text #8 + Font A → t0002c01f01.tif  ✓ Generated (different text, same font)

# Prevented ❌
Text #5 + Font A → ❌ SKIPPED (duplicate combination)
```

**Benefits:**
- No wasted generation (every image is unique)
- No file overwrites
- Maximum dataset diversity
- Efficient training (no redundant samples)

### Random Distribution

1. **Shuffles all text indices** at start
2. **Cycles through shuffled list** for even distribution
3. **Randomly selects fonts** for each image
4. **Checks for duplicates** before generating
5. **Retries automatically** if duplicate found

This ensures:
- Coverage across entire text file (no clustering)
- Different random results each run
- Balanced representation of all texts

### File Naming Convention

**Format:** `{prefix}{counter}c01f{font}`

- **Prefix:** `t` for text, `s` for special
- **Counter:** Sequential 4-digit number (0000, 0001, 0002...)
- **c01:** Chunk identifier (always 01 for single-line images)
- **f{font}:** Font index (01-99)

**Examples:**
```
t0000c01f03.tif  → Text image #0, Font 3
t0001c01f07.tif  → Text image #1, Font 7
s0000c01f02.tif  → Special image #0, Font 2
s0001c01f05.tif  → Special image #1, Font 5
```

**Font mapping** in `font_index.json`:
```json
{
  "f01": {
    "font_file": "k24_regular.ttf",
    "index": 1
  },
  "f03": {
    "font_file": "rudaw_regular.ttf",
    "index": 3
  }
}
```

## ⚙️ Advanced Configuration

### Individual Generators

Each generator (`text_generator.py` and `special_generator.py`) can be customized:

```python
# Number of images to generate
NUM_IMAGES = 100

# Maximum characters per line (before splitting)
MAX_LINE_LENGTH = 100

# Tesseract LSTM best practices
TARGET_TEXT_HEIGHT = 32  # Optimal: 30-48px
PADDING = 10             # Minimum: 5-10px
```

### Text Processing

**Smart line splitting** for long text:
- Splits at sentence boundaries (., !, ?, ،, ؛)
- Respects Kurdish/Arabic punctuation
- Falls back to word boundaries if needed
- Hard splits as last resort

**Example:**
```
Long line (150 chars) → Split into:
  - Chunk 1 (95 chars) at sentence boundary
  - Chunk 2 (55 chars) remaining text
```

### Output Format

**Image specifications:**
- Format: TIFF (`.tif`)
- Resolution: 300 DPI
- Color: RGB (white background, black text)
- Height: ~52px (32px text + 20px padding)
- Width: Dynamic based on text length

**Ground truth files:**
- Format: Plain text UTF-8 (`.gt.txt`)
- Content: Exact text as rendered in image
- One file per image

## 📈 Best Practices

### 1. Font Selection
- **Use 3-5 fonts** for focused training
- **Use 10-14 fonts** for maximum variety
- Include both regular and bold weights
- Test fonts render Kurdish characters correctly

### 2. Dataset Size
- **Minimum:** 400-800 samples per font
- **Recommended:** 1,000-3,000 samples per font
- **Professional:** 5,000+ samples per font

### 3. Text/Special Ratio
- **80% text, 20% special** (recommended)
- **85% text, 15% special** (text-heavy documents)
- **70% text, 30% special** (forms, data-heavy docs)

### 4. Text Content
- Use real Kurdish text from documents
- Include diverse vocabulary
- Mix formal and informal text
- Add domain-specific terminology

### 5. Generation Strategy
```python
# For 3 fonts × 1000 samples per font:
TOTAL_SAMPLES = 3000
TEXT_PERCENTAGE = 80

# For 14 fonts × 500 samples per font:
TOTAL_SAMPLES = 7000
TEXT_PERCENTAGE = 85
```

## 🔧 Troubleshooting

### Issue: "Not generating enough samples"

**Check:**
1. Total possible combinations = (number of texts) × (number of fonts)
2. If `TOTAL_SAMPLES` exceeds this, generation will stop early

**Solution:**
- Reduce `TOTAL_SAMPLES`, or
- Add more text lines, or
- Add more fonts

### Issue: "Text clustering at beginning of file"

**Solution:** Already fixed! The generators now:
- Shuffle text indices for random distribution
- Use proper random seeding
- Cover entire text file evenly

### Issue: "Duplicate images appearing"

**Solution:** Already fixed! The generators now:
- Track all (text + font) combinations
- Skip duplicate attempts automatically
- Guarantee 100% unique images

### Issue: "Generation is slow"

**Normal behavior** when:
- Requesting many samples (3000+)
- Using many fonts (10+)
- Near maximum possible combinations

**Speed estimates:**
- ~10-20 images/second typical
- 500 samples: ~30-60 seconds
- 3000 samples: ~3-5 minutes

## 📚 Usage Examples

### Example 1: Quick Test Dataset
```python
# main.py
TOTAL_SAMPLES = 200
TEXT_PERCENTAGE = 80
```
Output: 160 text + 40 special images (~10 seconds)

### Example 2: Production Dataset
```python
# main.py
TOTAL_SAMPLES = 5000
TEXT_PERCENTAGE = 85
```
Output: 4250 text + 750 special images (~4-6 minutes)

### Example 3: Text-Only Generation
```bash
# Edit text_generator.py
NUM_IMAGES = 1000

# Run
python text_generator.py
```
Output: 1000 text images only

### Example 4: Special Characters Focus
```bash
# Edit special_generator.py
NUM_IMAGES = 500

# Run
python special_generator.py
```
Output: 500 special character images only

## 🔬 For Tesseract Training

The generated dataset is optimized for Tesseract LSTM:

```bash
# Example training command
lstmtraining \
  --traineddata ckb.traineddata \
  --net_spec '[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c1]' \
  --model_output output/ckb \
  --train_listfile dataset/train.txt \
  --eval_listfile dataset/eval.txt \
  --max_iterations 10000
```

**Create list files:**
```bash
# Generate train.txt
ls dataset/t*.tif | sed 's/.tif//' > dataset/train.txt
ls dataset/s*.tif | sed 's/.tif//' >> dataset/train.txt
```

## 📊 Dataset Statistics

After generation, analyze your dataset:

```python
# Count unique combinations
import os
files = os.listdir('dataset')
tif_files = [f for f in files if f.endswith('.tif')]
print(f"Total images: {len(tif_files)}")
print(f"Text images: {len([f for f in tif_files if f.startswith('t')])}")
print(f"Special images: {len([f for f in tif_files if f.startswith('s')])}")
```

## 🤝 Contributing

Suggestions for improvement:
- Additional Kurdish text sources
- More commonly used symbols/patterns
- Font recommendations
- OCR training tips

## 📄 License

Free to use for OCR training and research purposes.

## 🙏 Acknowledgments

- Optimized for Kurdish language OCR
- Follows Tesseract LSTM training best practices
- Special character set curated for document OCR
- Duplicate prevention algorithm ensures training efficiency
