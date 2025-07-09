# features.py

import re

class PartFeatures:
    @staticmethod
    def parse_volume(size_str):
        """
        Parses a size string like "100x50x5" or "100x50x5 mm" and returns volume in mm³.
        Returns None if not valid.
        """
        if not size_str:
            return None
        size_str = size_str.replace("mm", "").strip().lower()
        # Accept "100x50x5", "100X50X5", "100*50*5"
        nums = [float(s) for s in re.split(r'[xX*]', size_str) if s.strip()]
        if len(nums) == 3:
            return nums[0] * nums[1] * nums[2]
        return None

    @staticmethod
    def size_label(volume_mm3):
        """
        Returns Small/Medium/Large for given volume.
        """
        if volume_mm3 is None:
            return "Unknown"
        elif volume_mm3 < 1000:
            return "Small"
        elif volume_mm3 < 100000:
            return "Medium"
        else:
            return "Large"

    @staticmethod
    def feature_dict(row):
        """
        Given a pandas Series or dict (row), returns a dict of engineered features.
        """
        # Works for DataFrame row or user dict
        material = (row.get('Material') or '').strip().capitalize()
        size = (row.get('Size') or '').strip()
        operations = (row.get('Operations') or '').strip()
        finish = (row.get('Finish') or '').strip()
        price = row.get('Target Price (CHF)', None)
        
        volume = PartFeatures.parse_volume(size)
        op_count = len([op for op in operations.split(',') if op.strip()])

        return {
            "Material": material,
            "Size": size,
            "Volume_mm3": volume,
            "Size_Label": PartFeatures.size_label(volume),
            "Operations": operations,
            "Operations_Count": op_count,
            "Finish": finish,
            "Target Price (CHF)": price,
        }
