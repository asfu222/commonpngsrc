import UnityPy
from PIL import Image, ImageOps
from pathlib import Path
import json
import os
from UnityPy.enums import TextureFormat
from multiprocessing import Pool

types = ['Texture2D']
ANDROID_OUT = Path("commonpng/latest/Android_PatchPack")
IOS_OUT = Path("commonpng/latest/iOS_PatchPack")
ASSETS_IN = Path("commonpngassets")
ANDROID_IN = Path("AssetBundles/AndroidAssetBundles")
IOS_IN = Path("AssetBundles/iOSAssetBundles")
ANDROID_OUT.mkdir(parents=True, exist_ok=True)
IOS_OUT.mkdir(parents=True, exist_ok=True)
modded_assets = {filepath.stem.lower(): filepath for filepath in ASSETS_IN.rglob("*") if filepath.is_file()}

def pad_to_multiple_of_4(img):
    new_width = (img.width + 3) // 4 * 4
    new_height = (img.height + 3) // 4 * 4
    return ImageOps.pad(img, (new_width, new_height), method=Image.Resampling.NEAREST, color=(0, 0, 0, 0))

def process_file(file_info):
    file, input_path, output_path, modded_assets = file_info
    filename = file.name
    fpath = os.path.join(input_path, filename)
    
    try:
        env = UnityPy.load(fpath)
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return

    has_modded = False
    for obj in env.objects:
        if obj.type.name != 'Texture2D':
            continue
        data = obj.read()
        if data.m_Name.lower() in modded_assets:
            modasset_path = modded_assets[data.m_Name.lower()]
            data.set_image(pad_to_multiple_of_4(Image.open(modasset_path)))
            data.save()
            has_modded = True
    
    if has_modded:
        print(f"Modifying {filename}")
        with open(output_path / filename, "wb") as f:
            f.write(env.file.save(packer="original"))

def applyMods_parallel(input_path: Path, output_path: Path) -> None:
    file_list = [file for file in input_path.glob("*.bundle") if any(ext in file.name for ext in ["textures", "mx-addressableasset-uis"])]
    
    tasks = [(file, input_path, output_path, modded_assets) for file in file_list]
    
    with Pool(os.cpu_count()) as p:
        p.map(process_file, tasks)

if __name__ == '__main__':
    applyMods_parallel(ANDROID_IN, ANDROID_OUT)
    applyMods_parallel(IOS_IN, IOS_OUT)
