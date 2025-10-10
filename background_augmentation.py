"""
Background augmentation module for realistic scanned document simulation
Provides various paper textures, aging effects, and scanner artifacts
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
import random


def create_paper_texture(width, height, base_color=(240, 235, 230)):
    """
    Create realistic paper texture with subtle grain

    Args:
        width: Image width
        height: Image height
        base_color: RGB tuple for base paper color (slightly off-white by default)

    Returns:
        PIL Image with paper texture
    """
    # Create base with slight color variation
    img_array = np.ones((height, width, 3), dtype=np.uint8)
    img_array[:, :] = base_color

    # Add fine paper grain (subtle noise)
    grain = np.random.normal(0, 3, (height, width, 3))
    img_array = np.clip(img_array + grain, 0, 255).astype(np.uint8)

    # Add slightly larger grain for texture
    scale_factor = 4
    coarse_h = (height + scale_factor - 1) // scale_factor  # Ceiling division
    coarse_w = (width + scale_factor - 1) // scale_factor
    coarse_grain = np.random.normal(0, 5, (coarse_h, coarse_w, 3))
    coarse_grain = np.repeat(
        np.repeat(coarse_grain, scale_factor, axis=0), scale_factor, axis=1
    )
    # Trim to exact size
    coarse_grain = coarse_grain[:height, :width, :]
    img_array = np.clip(img_array + coarse_grain, 0, 255).astype(np.uint8)

    return Image.fromarray(img_array)


def add_paper_aging(image, intensity=0.3):
    """
    Add aging effects to simulate old paper (yellowing, spots)

    Args:
        image: PIL Image
        intensity: Aging intensity (0.0-1.0)

    Returns:
        PIL Image with aging effects
    """
    img_array = np.array(image, dtype=np.float32)
    height, width = img_array.shape[:2]

    # Create yellow tint (more red and green, less blue)
    yellow_factor = 1.0 - (intensity * 0.3)
    img_array[:, :, 2] *= yellow_factor  # Reduce blue channel

    # Add random age spots
    num_spots = int(intensity * 10)
    for _ in range(num_spots):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        spot_size = random.randint(2, 8)
        spot_intensity = random.uniform(10, 30)

        # Create circular spot
        for dy in range(-spot_size, spot_size + 1):
            for dx in range(-spot_size, spot_size + 1):
                if dx * dx + dy * dy <= spot_size * spot_size:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        img_array[ny, nx] = np.clip(
                            img_array[ny, nx] - spot_intensity, 0, 255
                        )

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def add_scanner_lines(image, num_lines=None, intensity=15):
    """
    Add horizontal scanner artifact lines

    Args:
        image: PIL Image
        num_lines: Number of scan lines (None for random 1-3)
        intensity: Line intensity (higher = more visible)

    Returns:
        PIL Image with scanner lines
    """
    img_array = np.array(image, dtype=np.float32)
    height = img_array.shape[0]

    if num_lines is None:
        num_lines = random.randint(1, 3)

    for _ in range(num_lines):
        y = random.randint(0, height - 1)
        # Add subtle horizontal line
        img_array[y] = np.clip(img_array[y] - intensity, 0, 255)

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def add_gradient_lighting(image, intensity=0.2):
    """
    Add gradient to simulate uneven lighting from scanner

    Args:
        image: PIL Image
        intensity: Gradient intensity (0.0-1.0)

    Returns:
        PIL Image with gradient lighting
    """
    img_array = np.array(image, dtype=np.float32)
    height, width = img_array.shape[:2]

    # Random gradient direction
    direction = random.choice(["horizontal", "vertical", "diagonal"])

    if direction == "horizontal":
        gradient = np.linspace(1.0 - intensity, 1.0 + intensity, width)
        gradient = np.tile(gradient, (height, 1))
    elif direction == "vertical":
        gradient = np.linspace(1.0 - intensity, 1.0 + intensity, height)
        gradient = np.tile(gradient.reshape(-1, 1), (1, width))
    else:  # diagonal
        x_grad = np.linspace(1.0 - intensity, 1.0 + intensity, width)
        y_grad = np.linspace(1.0 - intensity, 1.0 + intensity, height)
        gradient = np.outer(y_grad, x_grad) / 2 + 0.5

    # Apply gradient to all channels
    for c in range(3):
        img_array[:, :, c] *= gradient

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def add_stains(image, num_stains=None, stain_size_range=(5, 20)):
    """
    Add random stains/marks to simulate real document wear

    Args:
        image: PIL Image
        num_stains: Number of stains (None for random 0-3)
        stain_size_range: Tuple of (min, max) stain radius

    Returns:
        PIL Image with stains
    """
    if num_stains is None:
        num_stains = random.randint(0, 3)

    if num_stains == 0:
        return image

    img_array = np.array(image, dtype=np.float32)
    height, width = img_array.shape[:2]

    for _ in range(num_stains):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        radius = random.randint(*stain_size_range)
        stain_color = random.randint(180, 220)  # Light brownish stain

        # Create irregular stain shape
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                # Add irregularity
                dist = np.sqrt(dx * dx + dy * dy) + random.uniform(-2, 2)
                if dist <= radius:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        alpha = 1.0 - (dist / radius) * 0.7  # Fade out at edges
                        img_array[ny, nx] = (
                            img_array[ny, nx] * (1 - alpha * 0.3)
                            + stain_color * alpha * 0.3
                        )

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def add_shadow(image, shadow_intensity=0.15):
    """
    Add subtle shadow effect to simulate paper not lying completely flat

    Args:
        image: PIL Image
        shadow_intensity: Shadow darkness (0.0-1.0)

    Returns:
        PIL Image with shadow
    """
    img_array = np.array(image, dtype=np.float32)
    height, width = img_array.shape[:2]

    # Create shadow in random corner
    corner = random.choice(["top-left", "top-right", "bottom-left", "bottom-right"])

    # Create gradient mask for shadow
    if corner == "top-left":
        y_grad = np.linspace(shadow_intensity, 0, height // 2)
        x_grad = np.linspace(shadow_intensity, 0, width // 2)
        y_grad = np.concatenate([y_grad, np.zeros(height - len(y_grad))])
        x_grad = np.concatenate([x_grad, np.zeros(width - len(x_grad))])
    elif corner == "top-right":
        y_grad = np.linspace(shadow_intensity, 0, height // 2)
        x_grad = np.linspace(0, shadow_intensity, width // 2)
        y_grad = np.concatenate([y_grad, np.zeros(height - len(y_grad))])
        x_grad = np.concatenate([np.zeros(width - len(x_grad)), x_grad])
    elif corner == "bottom-left":
        y_grad = np.linspace(0, shadow_intensity, height // 2)
        x_grad = np.linspace(shadow_intensity, 0, width // 2)
        y_grad = np.concatenate([np.zeros(height - len(y_grad)), y_grad])
        x_grad = np.concatenate([x_grad, np.zeros(width - len(x_grad))])
    else:  # bottom-right
        y_grad = np.linspace(0, shadow_intensity, height // 2)
        x_grad = np.linspace(0, shadow_intensity, width // 2)
        y_grad = np.concatenate([np.zeros(height - len(y_grad)), y_grad])
        x_grad = np.concatenate([np.zeros(width - len(x_grad)), x_grad])

    shadow_mask = np.outer(y_grad, x_grad)
    shadow_mask = np.clip(shadow_mask, 0, shadow_intensity)

    # Apply shadow (darken)
    for c in range(3):
        img_array[:, :, c] *= 1.0 - shadow_mask

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))


def apply_realistic_background(image, intensity="medium"):
    """
    Apply comprehensive background augmentation to simulate real scanned documents

    Args:
        image: PIL Image with text on white background
        intensity: 'light', 'medium', or 'heavy' augmentation

    Returns:
        PIL Image with realistic scanned document background
    """
    width, height = image.size

    # Extract text mask (black text on white background)
    img_array = np.array(image)
    text_mask = img_array < 250  # Pixels that are not pure white (i.e., text)

    # Set intensity parameters
    if intensity == "light":
        paper_color_range = [(245, 243, 240), (250, 248, 245)]
        aging_prob = 0.1
        aging_intensity = (0.1, 0.2)
        scanner_lines_prob = 0.2
        gradient_prob = 0.3
        gradient_intensity = (0.05, 0.1)
        stains_prob = 0.1
        shadow_prob = 0.2
        shadow_intensity = (0.05, 0.1)
    elif intensity == "medium":
        paper_color_range = [(235, 230, 220), (245, 242, 235)]
        aging_prob = 0.3
        aging_intensity = (0.2, 0.4)
        scanner_lines_prob = 0.4
        gradient_prob = 0.5
        gradient_intensity = (0.1, 0.2)
        stains_prob = 0.3
        shadow_prob = 0.3
        shadow_intensity = (0.1, 0.15)
    else:  # heavy
        paper_color_range = [(220, 215, 200), (240, 235, 220)]
        aging_prob = 0.5
        aging_intensity = (0.3, 0.6)
        scanner_lines_prob = 0.6
        gradient_prob = 0.7
        gradient_intensity = (0.15, 0.3)
        stains_prob = 0.5
        shadow_prob = 0.5
        shadow_intensity = (0.15, 0.25)

    # Create realistic paper background
    base_color = random.choice(paper_color_range)
    background = create_paper_texture(width, height, base_color)

    # Apply aging effects
    if random.random() < aging_prob:
        intensity_val = random.uniform(*aging_intensity)
        background = add_paper_aging(background, intensity_val)

    # Apply gradient lighting
    if random.random() < gradient_prob:
        intensity_val = random.uniform(*gradient_intensity)
        background = add_gradient_lighting(background, intensity_val)

    # Apply scanner lines
    if random.random() < scanner_lines_prob:
        background = add_scanner_lines(background)

    # Apply stains
    if random.random() < stains_prob:
        background = add_stains(background)

    # Apply shadow
    if random.random() < shadow_prob:
        intensity_val = random.uniform(*shadow_intensity)
        background = add_shadow(background, intensity_val)

    # Composite text onto realistic background
    background_array = np.array(background)
    result_array = background_array.copy()
    result_array[text_mask] = img_array[text_mask]

    result = Image.fromarray(result_array)

    return result
