# Synthetic OCR Data Generator

A Python tool for generating synthetic OCR training data for Kurdish text. This generator creates image/text pairs optimized for Tesseract LSTM training.

## Features

✨ **Automatic Font Detection** - Scans the `fonts/` directory and randomly selects fonts for each image  
✨ **Tesseract Optimized** - Follows LSTM training best practices (48px text height, proper padding)  
✨ **Ground Truth Generation** - Automatically creates `.gt.txt` files for each image  
✨ **Kurdish Text Support** - Full UTF-8 encoding support for Kurdish characters  
✨ **Dynamic Sizing** - Images automatically resize based on text length  

## Project Structure

```
Synthatic_ocr_data_generator/
├── dataset/              # Generated images and ground truth files (auto-created)
├── fonts/               # Place your .ttf font files here
│   ├── rudaw_regular.ttf
│   └── Droid_arabic_naskh_regular.ttf
├── input/
│   └── raw_text/
│       └── text.txt     # Input text file (one line per image)
├── dataset_generator    # Main generator script
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
   - Edit `input/raw_text/text.txt`
   - Add one line of text per image you want to generate
   - Supports Kurdish and Arabic text

## Usage

Run the generator:

```bash
python dataset_generator
```

The script will:
1. Scan all fonts in the `fonts/` directory
2. Read text lines from `input/raw_text/text.txt`
3. Generate one image per line with randomly selected fonts
4. Save images as `img_0.tif`, `img_1.tif`, etc.
5. Save ground truth as `img_0.gt.txt`, `img_1.gt.txt`, etc.

## Output

Each text line generates two files:

- **Image file** (`img_N.tif`) - TIFF image with rendered text
- **Ground truth** (`img_N.gt.txt`) - UTF-8 text file containing the exact text

Example output:
```
dataset/
├── img_0.tif
├── img_0.gt.txt
├── img_1.tif
├── img_1.gt.txt
└── ...
```

## Tesseract Training

The generated data is optimized for Tesseract LSTM training:

- Text height: **48 pixels** (optimal range: 30-48px)
- Padding: **10 pixels** minimum on all sides
- Format: Single-line images with corresponding `.gt.txt` files
- White background, black text

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
TARGET_TEXT_HEIGHT = 48  # Text height in pixels (30-48 recommended)
PADDING = 10             # Padding around text in pixels
```

## Requirements

- Python 3.6+
- Pillow (PIL) 10.0.0+

## License

Free to use for OCR training and research purposes.
