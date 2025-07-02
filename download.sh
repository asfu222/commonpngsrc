#!/bin/bash

if [ -f "ba.env" ]; then
  source ba.env
else
  echo "ba.env file not found!"
  exit 1
fi

if [ -z "$ADDRESSABLE_CATALOG_URL" ]; then
  echo "ADDRESSABLE_CATALOG_URL not set in ba.env"
  exit 1
fi

# Download logic
if [ -d "AssetBundles" ]; then
  echo "AssetBundles directory already exists, skipping download."
else
  echo "AssetBundles directory not found, downloading..."
  pip install git+https://github.com/asfu222/BA-AD

  for filter in "png_asset" "psd_asset" "tga_asset"
  do
    for attempt in {1..3}
    do
      echo "Attempting to download assets with filter: $filter (Attempt $attempt/3)"
      baad download --androidassets --iosassets --output AssetBundles --filter "$filter" --catalog "$ADDRESSABLE_CATALOG_URL"
    done
  done
fi
