"""
Configuration loader for OCR dataset generation
Loads and validates YAML configuration file
"""

import yaml
import os
from pathlib import Path


class Config:
    """Configuration manager for dataset generation"""

    def __init__(self, config_path="config.yaml"):
        """Load configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create config.yaml in the project root."
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        self._validate()

    def _validate(self):
        """Validate configuration values"""
        # Validate percentages
        if not 0 <= self.dataset.text_percentage <= 100:
            raise ValueError("text_percentage must be between 0 and 100")

        if not 0 <= self.augmentation.percentage <= 100:
            raise ValueError("augmentation.percentage must be between 0 and 100")

        if not 0 <= self.background.percentage <= 100:
            raise ValueError("background.percentage must be between 0 and 100")

        # Validate intensity
        if self.background.intensity not in ["light", "medium", "heavy"]:
            raise ValueError(
                "background.intensity must be 'light', 'medium', or 'heavy'"
            )

        # Validate directories exist
        if not os.path.exists(self.fonts.directory):
            raise FileNotFoundError(f"Font directory not found: {self.fonts.directory}")

        # Validate positive values
        if self.dataset.total_samples <= 0:
            raise ValueError("total_samples must be greater than 0")

        if self.fonts.target_text_height <= 0:
            raise ValueError("target_text_height must be greater than 0")

    def __getattr__(self, name):
        """Allow dot notation access to config"""
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        return ConfigSection(self._config.get(name, {}))

    def get(self, key, default=None):
        """Get config value with default"""
        return self._config.get(key, default)

    def print_summary(self):
        """Print configuration summary"""
        text_samples = int(
            self.dataset.total_samples * self.dataset.text_percentage / 100
        )
        special_samples = self.dataset.total_samples - text_samples

        print("=" * 70)
        print("📋 CONFIGURATION SUMMARY")
        print("=" * 70)
        print(f"Total samples: {self.dataset.total_samples:,}")
        print(f"  ├─ Text samples: {text_samples:,} ({self.dataset.text_percentage}%)")
        print(
            f"  └─ Special samples: {special_samples:,} ({100-self.dataset.text_percentage}%)"
        )
        print(f"\nAugmentation:")
        print(
            f"  ├─ General: {self.augmentation.percentage}% of images "
            f"({'enabled' if self.augmentation.enabled else 'disabled'})"
        )
        print(
            f"  └─ Background: {self.background.percentage}% "
            f"(intensity: {self.background.intensity})"
        )
        print(
            f"\nOutput: {self.dataset.output_dir}/ "
            f"({self.output.format.upper()} @ {self.output.dpi} DPI)"
        )
        print(
            f"Font settings: {self.fonts.target_text_height}px height, {self.fonts.padding}px padding"
        )
        print("=" * 70 + "\n")


class ConfigSection:
    """Wrapper for nested configuration sections"""

    def __init__(self, section):
        self._section = section if section is not None else {}

    def __getattr__(self, name):
        value = self._section.get(name)
        if isinstance(value, dict):
            return ConfigSection(value)
        return value

    def get(self, key, default=None):
        return self._section.get(key, default)


# Singleton instance
_config = None


def load_config(config_path="config/config.yaml"):
    """Load configuration (singleton pattern)"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def get_config():
    """Get current configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path="config/config.yaml"):
    """Force reload configuration"""
    global _config
    _config = Config(config_path)
    return _config
