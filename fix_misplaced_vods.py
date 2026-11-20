#!/usr/bin/env python3
"""
Fix VOD folders that were placed into the wrong channel directory due to the
multi-channel output_dir bug.  Scans the download root, reads vod.json for
each VOD, queries the Twitch API for the real channel owner, and moves the
folder into the correct channel subdirectory.

Usage:
    python fix_misplaced_vods.py /data/twitch/unsorted
    python fix_misplaced_vods.py /data/twitch/unsorted --dry-run
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import requests

HELIX_CLIENT_ID = "gh70y1spw727ohtgzbhc0hppvq9br2"
HELIX_VIDEO_URL = "https://api.twitch.tv/helix/videos"


def get_channel_name_for_vod(vod_id: int) -> str | None:
    """Query Twitch Helix API for the channel login name of a given VOD ID."""
    try:
        r = requests.get(
            HELIX_VIDEO_URL,
            params={"id": vod_id},
            headers={"Client-ID": HELIX_CLIENT_ID},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if data:
            # user_login is the lowercase channel name used for directories
            return data[0].get("user_login")
    except requests.RequestException as exc:
        print(f"  API error for VOD {vod_id}: {exc}")
    return None


def fix_directory(root_dir: Path, dry_run: bool = False) -> int:
    """
    Scan *root_dir* for VOD folders, look up the real channel, and move them.

    Returns the number of folders moved.
    """
    moved = 0
    skipped = 0
    errors = 0

    vod_json_files = list(root_dir.rglob("vod.json"))
    total = len(vod_json_files)
    print(f"Found {total} vod.json file(s) under {root_dir}")

    for idx, vod_json in enumerate(vod_json_files, 1):
        vod_folder = vod_json.parent
        rel_path = vod_folder.relative_to(root_dir)

        print(f"\n[{idx}/{total}] {rel_path}")

        # Read vod.json
        try:
            with open(vod_json, encoding="utf8") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  Skipping: could not read vod.json ({exc})")
            skipped += 1
            continue

        vod_id = metadata.get("vod_id")
        if not vod_id:
            print("  Skipping: no vod_id in metadata")
            skipped += 1
            continue

        # Look up correct channel
        correct_channel = get_channel_name_for_vod(int(vod_id))
        if not correct_channel:
            print(f"  Skipping: could not resolve channel for VOD {vod_id}")
            skipped += 1
            continue

        # Determine current channel directory (first component of relative path)
        current_channel = rel_path.parts[0] if rel_path.parts else ""

        if current_channel.lower() == correct_channel.lower():
            print(f"  OK — already in correct folder ({correct_channel})")
            continue

        target_dir = root_dir / correct_channel / vod_folder.name
        print(f"  Move: {rel_path} -> {target_dir.relative_to(root_dir)}")

        if dry_run:
            moved += 1
            continue

        # Ensure target channel directory exists
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # If target already exists, append a counter
        final_target = target_dir
        counter = 1
        while final_target.exists():
            final_target = target_dir.with_name(f"{target_dir.name}_{counter}")
            counter += 1

        try:
            shutil.move(str(vod_folder), str(final_target))
            moved += 1
        except OSError as exc:
            print(f"  ERROR moving folder: {exc}")
            errors += 1

        # Small sleep to be nice to the API
        time.sleep(0.25)

    print(f"\n{'=' * 50}")
    print(f"Total VODs scanned : {total}")
    print(f"Moved             : {moved}")
    print(f"Skipped           : {skipped}")
    print(f"Errors            : {errors}")
    if dry_run:
        print("(DRY RUN — no files were actually moved)")

    return moved


def main():
    parser = argparse.ArgumentParser(description="Fix VOD folders misplaced by the multi-channel output_dir bug.")
    parser.add_argument("root_dir", type=Path, help="Root download directory (e.g. /data/twitch/unsorted)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be moved without doing it")
    args = parser.parse_args()

    if not args.root_dir.is_dir():
        print(f"Error: {args.root_dir} is not a directory")
        sys.exit(1)

    fix_directory(args.root_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
