from pathlib import Path
import shutil
import argparse
import random

def split_by_size(input_dir: Path, chunks: int):
    """
    Splits files in input_dir into 'chunks' subfolders so total size per chunk is roughly balanced.
    """
    input_dir = Path(input_dir)
    files = [f for f in input_dir.glob("*") if f.is_file()]

    random.shuffle(files)
    
    # Initialize chunk folders
    chunk_paths = [input_dir / str(i) for i in range(chunks)]
    for p in chunk_paths:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True)

    # Track total size per chunk
    chunk_sizes = [0] * chunks

    # Assign each file to the chunk with currently smallest total size
    for f in files:
        size = f.stat().st_size
        min_idx = chunk_sizes.index(min(chunk_sizes))
        shutil.move(str(f), chunk_paths[min_idx] / f.name)
        chunk_sizes[min_idx] += size

    print("Chunks created with sizes (bytes):", chunk_sizes)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--android_in", type=str, default="Android/AssetBundles")
    parser.add_argument("--ios_in", type=str, default="iOS/AssetBundles")
    parser.add_argument("--chunks", type=int, default=4)
    args = parser.parse_args()

    # Split Android
    split_by_size(Path(args.android_in), args.chunks)
    # Split iOS
    split_by_size(Path(args.ios_in), args.chunks)
