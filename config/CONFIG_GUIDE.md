# Configuration Guide

## Overview

The OCR Data Generator now uses YAML configuration files for all settings. This makes it easy to:
- Switch between different configurations
- Version control your settings
- Share configurations with your team
- Avoid editing Python code

## Quick Start

### 1. Edit Configuration

Open `config.yaml` and adjust settings:

```yaml
dataset:
  total_samples: 5000        # Change this number
  text_percentage: 85

augmentation:
  percentage: 40             # 0-100

background:
  percentage: 70             # 0-100
  intensity: "medium"        # light, medium, heavy
```

### 2. Run Generation

```bash
python main.py
```

## Example Configurations

### Testing (Quick Validation)
```yaml
dataset:
  total_samples: 100
augmentation:
  percentage: 30
background:
  percentage: 50
  intensity: "light"
advanced:
  random_seed: 42  # Reproducible results
```

### Production (Balanced, Real-World)
```yaml
dataset:
  total_samples: 10000
augmentation:
  percentage: 40
background:
  percentage: 70
  intensity: "medium"
```

### Clean (Digital Text Only)
```yaml
dataset:
  total_samples: 5000
augmentation:
  percentage: 0
background:
  percentage: 0
```

### Heavy (Maximum Robustness)
```yaml
dataset:
  total_samples: 10000
augmentation:
  percentage: 60
background:
  percentage: 90
  intensity: "heavy"
```

## Configuration Structure

### Main Sections

```yaml
dataset:              # Dataset size and composition
text_processing:      # Text splitting settings
fonts:                # Font and sizing settings
augmentation:         # General augmentation (rotation, blur, etc.)
background:           # Background augmentation (paper effects)
output:               # Output format and progress
advanced:             # Advanced options
```

## Key Settings Explained

### Dataset Settings

```yaml
dataset:
  total_samples: 5000        # Total images to generate
  text_percentage: 85        # % for text.txt (rest = special.txt)
  output_dir: "dataset"      # Where to save images
```

**Recommendations:**
- **Testing:** 100-500 samples
- **Development:** 1,000-3,000 samples
- **Production:** 5,000-20,000 samples
- **Text percentage:** 80-85% (OCR best practice)

### Augmentation Settings

```yaml
augmentation:
  enabled: true              # Master switch
  percentage: 40             # % of images to augment
```

**Percentage Guidelines:**
- **0%:** Clean only (digital text)
- **30-40%:** Balanced (recommended)
- **50-60%:** Heavy variance
- **100%:** All augmented (not recommended)

### Background Settings

```yaml
background:
  enabled: true
  percentage: 70             # % to get realistic backgrounds
  intensity: "medium"        # light/medium/heavy
```

**Intensity Levels:**
- **light:** Modern documents, subtle texture
- **medium:** General purpose (recommended)
- **heavy:** Historical documents, strong aging

**Percentage Guidelines:**
- **0%:** White backgrounds only
- **50-70%:** Balanced (recommended for real-world)
- **100%:** All realistic (maximum accuracy)

### Individual Augmentations

Each augmentation can be fine-tuned:

```yaml
augmentation:
  rotation:
    enabled: true
    probability: 0.7         # 70% chance when augmenting
    angle_range: [-2, 2]     # Rotation range in degrees
  
  noise:
    enabled: true
    probability: 0.5
    level: 0.01              # Intensity (0.01 = subtle)
  
  # ... blur, brightness, contrast ...
```

## Customizing Your Configuration

### Example: High-Quality Scans Only

```yaml
dataset:
  total_samples: 3000
  
augmentation:
  percentage: 20             # Light augmentation
  
background:
  percentage: 40             # Some realistic backgrounds
  intensity: "light"         # Subtle effects
```

### Example: Maximum Robustness

```yaml
dataset:
  total_samples: 15000       # Large dataset
  
augmentation:
  percentage: 70             # Heavy augmentation
  
background:
  percentage: 95             # Almost all realistic
  intensity: "heavy"         # Strong effects
```

### Example: Quick Testing

```yaml
dataset:
  total_samples: 50          # Very small
  
output:
  progress_interval: 10      # Frequent updates
  
advanced:
  random_seed: 123           # Reproducible
```

## Validation

The system automatically validates your configuration:

- Percentages must be 0-100
- Intensity must be 'light', 'medium', or 'heavy'
- Font directory must exist
- All values must be positive

If there's an error, you'll see a clear message.

## Tips & Best Practices

### 1. Start Small
Always test with small sample size first:
```yaml
# In config.yaml, set:
dataset:
  total_samples: 100
```

### 2. Version Control
Backup your working config:
```bash
cp config.yaml config_backup_$(date +%Y%m%d).yaml
```

### 3. Document Changes
Add comments to your config:
```yaml
augmentation:
  percentage: 45  # Increased from 40 to improve robustness on 2024-10-10
```

### 4. Test Before Large Runs
Always test with 100-500 samples first to verify settings

### 5. Experiment
Try different combinations:
- Low aug + high background
- High aug + low background
- All combinations with different intensities

## Common Issues

### "Configuration file not found"
```bash
# Make sure config.yaml exists in project root
ls -la config.yaml
```

### "Font directory not found"
Check `fonts.directory` in your config matches your actual folder.

### Slow Generation
Reduce these values:
- `dataset.total_samples`
- `augmentation.percentage`
- `background.percentage`

### Not Enough Variation
Increase these values:
- `augmentation.percentage`
- `background.percentage`
- Change `background.intensity` to "medium" or "heavy"

## Reference: Full Config Template

See `config.yaml` for a fully documented template with all options.

## Need Help?

1. Check the example configs for inspiration
2. Read the comments in `config.yaml`
3. Start with defaults and adjust incrementally
4. Test with small samples before large runs

---

**Pro Tip:** Keep your `config.yaml` in git to track what settings produced which results!

