import os
from icoextract import IconExtractor, IconExtractorError
from PIL import Image
from io import BytesIO

def extract_icon_from_exe(exe_path: str, output_path: str, icon_index: int = 0) -> str | None:
    """
    Extracts an icon from an EXE file and saves it as .ico or .png.

    Args:
        exe_path (str): Path to the .exe file.
        output_path (str): Path to save the extracted icon (.ico or .png).
        icon_index (int): Index of the icon to extract (default is 0).

    Returns:
        str | None: Path to saved icon, or None if failed.
    """
    try:
        extractor = IconExtractor(exe_path)

        if output_path.lower().endswith(".ico"):
            extractor.export_icon(output_path, num=icon_index)
            return output_path

        icon_data = extractor.get_icon(num=icon_index)
        image = Image.open(icon_data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, format="PNG")
        return output_path

    except IconExtractorError as e:
        print(f"Icon extraction failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
