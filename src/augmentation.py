"""
Image augmentation functions for realistic document simulation
"""

from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import random


def add_noise(image, noise_level=0.01):
    """Add Gaussian noise to simulate scan artifacts"""
    img_array = np.array(image)
    noise = np.random.normal(0, noise_level * 255, img_array.shape)
    noisy = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


def rotate_image(image, angle_range=(-2, 2)):
    """Apply slight rotation to simulate scan skew"""
    angle = random.uniform(*angle_range)
    return image.rotate(angle, fillcolor=(255, 255, 255), expand=True)


def adjust_brightness(image, factor_range=(0.88, 1.12)):
    """Adjust brightness to simulate lighting variations"""
    factor = random.uniform(*factor_range)
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image, factor_range=(0.9, 1.1)):
    """Adjust contrast to simulate scan quality variations"""
    factor = random.uniform(*factor_range)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def add_blur(image, radius_range=(0.5, 0.8)):
    """Add slight blur to simulate scan quality"""
    radius = random.uniform(*radius_range)
    return image.filter(ImageFilter.GaussianBlur(radius))


def augment_image(image):
    """
    Apply moderate augmentation for scanned paper simulation
    Randomly applies 2-4 different augmentations
    """
    augmented = image.copy()
    augmentations_applied = 0

    # Rotation (70% chance) - typical scan skew
    if random.random() < 0.7:
        augmented = rotate_image(augmented)
        augmentations_applied += 1

    # Noise (50% chance) - scan artifacts
    if random.random() < 0.5:
        augmented = add_noise(augmented, noise_level=0.01)
        augmentations_applied += 1

    # Blur (50% chance) - scan quality
    if random.random() < 0.5:
        augmented = add_blur(augmented)
        augmentations_applied += 1

    # Brightness (60% chance) - lighting differences
    if random.random() < 0.6:
        augmented = adjust_brightness(augmented)
        augmentations_applied += 1

    # Contrast (40% chance) - scan quality variations
    if random.random() < 0.4:
        augmented = adjust_contrast(augmented)
        augmentations_applied += 1

    return augmented
