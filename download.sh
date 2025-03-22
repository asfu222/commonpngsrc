#!/bin/bash
if [ -d "AssetBundles" ]; then
  echo "AssetBundles directory already exists, skipping download."
else
  echo "AssetBundles directory not found, downloading..."
	for filter in "png_asset" "psd_asset" "tga_asset"
	do
	  for attempt in {1..3}
	  do
		echo "Attempting to download assets with filter: $filter (Attempt $attempt/3)"
		baad download --androidassets --iosassets --output AssetBundles --filter "$filter"
	  done
	done
fi