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
#ANDROID_IN = Path("AssetBundles/AndroidAssetBundles")
# IOS_IN = Path("AssetBundles/iOSAssetBundles")
ANDROID_IN = ANDROID_OUT = Path("commonpng/latest/Android")
IOS_IN = IOS_OUT = Path("commonpng/latest/iOS")
ASSETS_IN = Path("commonpngassets")

ANDROID_OUT.mkdir(exist_ok=True)
IOS_OUT.mkdir(exist_ok=True)
modded_assets = {filepath.stem.lower():filepath for filepath in ASSETS_IN.rglob("*") if filepath.is_file()}
def pad_to_multiple_of_4(img):
    new_width = (img.width + 3) // 4 * 4
    new_height = (img.height + 3) // 4 * 4
    return ImageOps.pad(img, (new_width, new_height), method=Image.Resampling.NEAREST, color=(0, 0, 0, 0))
def set_astc_data(texture, imagebytes, block_width, block_height, texture_format):
    config = ASTCConfig(ASTCProfile.LDR_SRGB, block_width, block_height)
    context = ASTCContext(config)
    img = imagebytes.convert("RGBA")
    image = ASTCImage(ASTCType.U8, *img.size, data=img.tobytes())
    swizzle = ASTCSwizzle.from_str("RGBA")
    comp = context.compress(image, swizzle)
    
    texture.image_data = comp
    texture.m_CompleteImageSize = len(comp)
    texture.m_TextureFormat = texture_format
    texture.save()

def set_image(texture, imagebytes):
    print("Texture format: " + TextureFormat(texture.m_TextureFormat).name)
    
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_4x4:
        set_astc_data(texture, imagebytes, 4, 4, TextureFormat.ASTC_RGB_4x4)
        return
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_5x5:
        set_astc_data(texture, imagebytes, 5, 5, TextureFormat.ASTC_RGB_5x5)
        return
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_6x6:
        set_astc_data(texture, imagebytes, 6, 6, TextureFormat.ASTC_RGB_6x6)
        return
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_8x8:
        set_astc_data(texture, imagebytes, 8, 8, TextureFormat.ASTC_RGB_8x8)
        return
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_10x10:
        set_astc_data(texture, imagebytes, 10, 10, TextureFormat.ASTC_RGB_10x10)
        return
    if texture.m_TextureFormat == TextureFormat.ASTC_RGB_12x12:
        set_astc_data(texture, imagebytes, 12, 12, TextureFormat.ASTC_RGB_12x12)
        return
    
    print("not ASTC, continue")
    texture.set_image(pad_to_multiple_of_4(imagebytes))
def get_prefix(name):
    last_index = name.rfind('_')
    return name[:last_index] if last_index != -1 else name
with open("filter-config.json", "r", encoding="utf8") as f_cfg:
    filter_config = json.loads(f_cfg.read())
filtered_prefixes = set(filter_config["filter_prefixes"])
found_prefixes = []
filtered_types = filter_config["filtered_types"]
def applyMod(input_path: Path, output_path: Path) -> None:
    used_paths = []
    filtered_names = names = os.listdir(input_path)
    #names = [name for name in names if any(typename in name for typename in filtered_types)]
    #filtered_names = [name for name in names if get_prefix(name) in filtered_prefixes] if filter_config["enabled"] else names
    for filename in filtered_names:
        fpath = os.path.join(input_path, filename)
        env = UnityPy.load(fpath)
        has_modded = False
        for obj in env.objects:
            if obj.type.name != 'Texture2D':
                continue
            data = obj.read()
            if data.m_Name.lower() in modded_assets:
                modasset_path = modded_assets[data.m_Name.lower()]
                set_image(data, Image.open(modasset_path))
                data.save()
                used_paths.append(modasset_path)
                has_modded = True
        if has_modded:
            print(f"Modifying {filename}")
            with open(output_path / filename, "wb") as f:
                f.write(env.file.save(packer = "original"))
            found_prefixes.append(get_prefix(filename))
            
    unused_paths = [str(upath) for upath in set(modded_assets.values()) - set(used_paths)]
    if len(unused_paths) > 0:
        print(f"Warning: {len(unused_paths)} unused. Writing unused paths to logs.")
        with open("balocalizationmod.log", "a", encoding="utf-8") as f:
            f.write(f"UNUSED ASSETS WARNING:\n{json.dumps(unused_paths, indent=4)}\n")
applyMod(ANDROID_IN, ANDROID_OUT)
applyMod(IOS_IN, IOS_OUT)
'''
if not filter_config["enabled"]:
    filter_config["filter_prefixes"] = list(set(found_prefixes))
    filter_config["enabled"] = True
    with open("filter-config.json", "wb") as f_cfg:
        f_cfg.write(json.dumps(filtered_prefixes, indent=4, ensure_ascii=False))
'''