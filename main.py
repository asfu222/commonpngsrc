import UnityPy
from PIL import Image, ImageOps
from pathlib import Path
import json
import os
from astc_encoder import (
 ASTCConfig,
 ASTCContext,
 ASTCImage,
 ASTCProfile,
 ASTCSwizzle,
 ASTCType,
)
from UnityPy.enums import TextureFormat
types = ['Texture2D']
ANDROID_OUT = Path("commonpng/latest/Android_PatchPack")
IOS_OUT = Path("commonpng/latest/iOS_PatchPack")
ASSETS_IN = Path("commonpngassets")
ANDROID_IN = Path("AssetBundles/AndroidAssetBundles")
IOS_IN = Path("AssetBundles/iOSAssetBundles")
ANDROID_OUT.mkdir(parents=True,exist_ok=True)
IOS_OUT.mkdir(parents=True,exist_ok=True)
modded_assets = {filepath.stem.lower():filepath for filepath in ASSETS_IN.rglob("*") if filepath.is_file()}
def pad_to_multiple_of_4(img):
    new_width = (img.width + 3) // 4 * 4
    new_height = (img.height + 3) // 4 * 4
    return ImageOps.pad(img, (new_width, new_height), method=Image.Resampling.NEAREST, color=(0, 0, 0, 0))
def applyMod(input_path: Path, output_path: Path) -> None:
    used_paths = []
    for filename in os.listdir(input_path):
        if not any(ext in filename for ext in ["png_asset", "psd_asset", "tga_asset"]):
         continue
        print(f"Reading file {filename}")
        fpath = os.path.join(input_path, filename)
        env = UnityPy.load(fpath)
        has_modded = False
        for obj in env.objects:
            if obj.type.name != 'Texture2D':
                continue
            data = obj.read()
            if data.m_Name.lower() in modded_assets:
                modasset_path = modded_assets[data.m_Name.lower()]
                data.set_image(pad_to_multiple_of_4(Image.open(modasset_path)))
                data.save()
                used_paths.append(modasset_path)
                has_modded = True
        if has_modded:
            print(f"Modifying {filename}")
            with open(output_path / filename, "wb") as f:
                f.write(env.file.save(packer = "original"))
            
    unused_paths = [str(upath) for upath in set(modded_assets.values()) - set(used_paths)]
    if len(unused_paths) > 0:
        print(f"Warning: {len(unused_paths)} unused. Writing unused paths to logs.")
        with open("balocalizationmod.log", "a", encoding="utf-8") as f:
            f.write(f"UNUSED ASSETS WARNING:\n{json.dumps(unused_paths, indent=4)}\n")
applyMod(ANDROID_IN, ANDROID_OUT)
applyMod(IOS_IN, IOS_OUT)
