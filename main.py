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
import multiprocessing

types = ['Texture2D']
ANDROID_IN = ANDROID_OUT = Path("commonpng/latest/Android")
IOS_IN = IOS_OUT = Path("commonpng/latest/iOS")
ASSETS_IN = Path("commonpngassets")

ANDROID_OUT.mkdir(exist_ok=True, parents=True)
IOS_OUT.mkdir(exist_ok=True, parents=True)
IMAGE_TYPES = [".png", ".jpg"]
# Preload modded assets into memory and map filepaths
modded_assets = {}
for filepath in ASSETS_IN.rglob("*"):
    if filepath.is_file() and filepath.suffix.lower() in IMAGE_TYPES:
        key = filepath.stem.lower()
        try:
            with Image.open(filepath) as img:
                img = img.convert("RGBA")
                modded_assets[key] = {
                    'bytes': img.tobytes(),
                    'size': img.size,
                    'path': filepath
                }
        except Exception as e:
            print(f"Error loading {filepath}: {e}")

# Pre-initialize ASTC contexts for each block size
astc_contexts = {
    (4,4): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 4,4)),
    (5,5): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 5,5)),
    (6,6): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 6,6)),
    (8,8): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 8,8)),
    (10,10): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 10,10)),
    (12,12): ASTCContext(ASTCConfig(ASTCProfile.LDR_SRGB, 12,12)),
}

def pad_to_multiple_of_4(img):
    new_width = (img.width + 3) // 4 * 4
    new_height = (img.height + 3) // 4 * 4
    return ImageOps.pad(img, (new_width, new_height), method=Image.Resampling.NEAREST, color=(0, 0, 0, 0))

def set_astc_data(texture, img, block_width, block_height, texture_format):
    img = ImageOps.flip(img)
    context = astc_contexts[(block_width, block_height)]
    image = ASTCImage(ASTCType.U8, img.width, img.height, data=img.tobytes())
    swizzle = ASTCSwizzle.from_str("RGBA")
    comp = context.compress(image, swizzle)
    texture.image_data = comp
    texture.m_CompleteImageSize = len(comp)
    texture.m_TextureFormat = texture_format
    texture.save()

def set_image(texture, img):
    fmt = texture.m_TextureFormat
    if fmt == TextureFormat.ASTC_RGB_4x4:
        set_astc_data(texture, img, 4, 4, fmt)
    elif fmt == TextureFormat.ASTC_RGB_5x5:
        set_astc_data(texture, img, 5, 5, fmt)
    elif fmt == TextureFormat.ASTC_RGB_6x6:
        set_astc_data(texture, img, 6, 6, fmt)
    elif fmt == TextureFormat.ASTC_RGB_8x8:
        set_astc_data(texture, img, 8, 8, fmt)
    elif fmt == TextureFormat.ASTC_RGB_10x10:
        set_astc_data(texture, img, 10, 10, fmt)
    elif fmt == TextureFormat.ASTC_RGB_12x12:
        set_astc_data(texture, img, 12, 12, fmt)
    else:
        texture.set_image(pad_to_multiple_of_4(img))

def process_single_file(args):
    input_dir, output_dir, filename = args
    used = []
    input_path = os.path.join(input_dir, filename)
    try:
        env = UnityPy.load(input_path)
    except Exception as e:
        print(f"Error loading {input_path}: {e}")
        return used
    has_modded = False
    for obj in env.objects:
        if obj.type.name != 'Texture2D':
            continue
        data = obj.read()
        key = data.m_Name.lower()
        if key in modded_assets:
            asset = modded_assets[key]
            img = Image.frombytes("RGBA", asset['size'], asset['bytes'])
            set_image(data, img)
            used.append(asset['path'])
            has_modded = True
    if has_modded:
        print(f"modding {filename}")
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "wb") as f:
            f.write(env.file.save(packer="original"))
    return used

def process_platform(input_dir, output_dir):
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    args = [(input_dir, output_dir, f) for f in files]
    with multiprocessing.Pool() as pool:
        results = pool.map(process_single_file, args)
    used_paths = []
    for res in results:
        used_paths.extend(res)
    return used_paths

def main():
    android_used = process_platform(ANDROID_IN, ANDROID_OUT)
    ios_used = process_platform(IOS_IN, IOS_OUT)
    all_used = android_used + ios_used

    all_modded_paths = [asset['path'] for asset in modded_assets.values()]
    unused_paths = [str(fpath).replace("\\", "/") for fpath in list(set(all_modded_paths) - set(all_used))]
    
    if unused_paths:
        print(f"Warning: {len(unused_paths)} unused modded assets.")
        with open("balocalizationmod.log", "w", encoding="utf-8") as f:
            f.write("UNUSED ASSETS:\n")
            json.dump(unused_paths, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
