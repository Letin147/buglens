"""Vision utilities: the executable verification oracle primitives (EXP-07)."""

from buglens.vision.layout import covered_elements_in_region, layout_defects_in_region
from buglens.vision.pixels import region_change_ratio

__all__ = ["covered_elements_in_region", "layout_defects_in_region", "region_change_ratio"]
