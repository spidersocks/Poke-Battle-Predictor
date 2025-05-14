#!/usr/bin/env python3

import requests
import time
import os
import json
import random
from pathlib import Path
from tqdm import tqdm
import argparse
import sys

BASE_URL = "https://replay.pokemonshowdown.com/"
JSON_ENDPOINT = "search.json"

def get_listing_url(format_name):
    return f"{BASE_URL}{JSON_ENDPOINT}?format={format_name}"

def get_page_json(session, listing_url, page_number):
    url = f"{listing_url}&page={page_number}" if page_number > 1 else listing_url
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch page {page_number}: {e}", file=sys.stderr)
        return []

def save_battle_json(session, page_json, download_dir, sleep_min=0, sleep_max=3):
    for battle in tqdm(page_json, desc="Downloading battles", unit="battle"):
        battle_id = battle.get("id")
        if not battle_id:
            print("[WARNING] Skipping battle with no 'id' field.")
            continue
        filename = download_dir / f"{battle_id}.json"
        # Skip if already downloaded
        if filename.exists():
            tqdm.write(f"[INFO] {battle_id}.json already exists, skipping.")
            continue
        url = f"{BASE_URL}{battle_id}.json"
        try:
            r = session.get(url, timeout=10)
            r.raise_for_status()
            battle_json = r.json()
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(battle_json, f)
        except Exception as e:
            tqdm.write(f"[ERROR] Failed to download {battle_id}: {e}")
            continue
        time.sleep(random.uniform(sleep_min, sleep_max))

def main(format_name, output_dir):
    listing_url = get_listing_url(format_name)
    download_dir = Path(output_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    page_number = 1
    total_downloaded = 0

    print(f"Starting extraction for format: {format_name}")
    while True:
        print(f"\n[INFO] Fetching results page {page_number}...")
        page_json = get_page_json(session, listing_url, page_number)
        if not page_json:
            print("[INFO] No data retrieved, finishing.")
            break
        save_battle_json(session, page_json, download_dir)
        total_downloaded += len(page_json)
        if len(page_json) < 51:
            print(f"[INFO] Extraction complete. Total battles processed: {total_downloaded}")
            break
        page_number += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Pokémon Showdown battle replays as JSON.")
    parser.add_argument(
        "--format",
        type=str,
        default="gen9vgc2025regibo3",
        help="Format name (e.g., gen9vgc2025regibo3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="replays",
        help="Directory to save replays"
    )
    args = parser.parse_args()
    main(args.format, args.output)