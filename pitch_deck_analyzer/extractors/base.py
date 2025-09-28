"""
Base extractor interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str, output_dir: Path) -> Dict[str, any]:
        pass