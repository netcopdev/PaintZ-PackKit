from __future__ import annotations

from functools import lru_cache
from io import BytesIO

from PIL import Image

try:
    from PIL import ImageCms
except ImportError:  # pragma: no cover
    ImageCms = None


@lru_cache(maxsize=1)
def srgb_icc_profile() -> bytes | None:
    if ImageCms is None:
        return None
    try:
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
        return profile.tobytes()
    except Exception:
        return None


def tag_srgb(image: Image.Image) -> Image.Image:
    profile = srgb_icc_profile()
    if profile is not None:
        image.info["icc_profile"] = profile
    else:
        image.info.pop("icc_profile", None)
    return image


def normalize_to_srgb(image: Image.Image, mode: str = "RGBA") -> Image.Image:
    embedded = image.info.get("icc_profile")
    if embedded and ImageCms is not None:
        try:
            source_profile = ImageCms.ImageCmsProfile(BytesIO(embedded))
            target_profile = ImageCms.createProfile("sRGB")
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            rgb = image.convert("RGB")
            converted = ImageCms.profileToProfile(
                rgb, source_profile, target_profile, outputMode="RGB"
            )
            if mode == "RGBA":
                converted = converted.convert("RGBA")
                if alpha is not None:
                    converted.putalpha(alpha)
            else:
                converted = converted.convert(mode)
            return tag_srgb(converted)
        except Exception:
            pass
    return tag_srgb(image.convert(mode))
