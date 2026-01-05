#!/usr/bin/env python3
#
# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

# Requirement: `pip install black`
#
# This script releases the approved sections of aigdat/gaia to the open source repo.
#
# At the time of this writing, we are releasing the core functionality while keeping some
# internal tools and configurations private.
#
# NOTE: This repo is the single source of truth (SSOT) for gaia.
# Please do not check code directly into the OSS repo!!! Only check code into this
# private repo, then use this script to sync it to the OSS repo. We don't have any tooling
# for syncing code in the other direction (public -> private).
#
# Usage:
# 1. Make sure you already cloned the Gaia OSS repo on to your hard drive.
#    We'll use C:\work\gaia as an example clone.
# 2. Create a branch in the clone
# 3. NOTE: if aigdat/gaia moved any files already checked into the clone, you need
#    to `git mv` those files in the clone to the expected location before proceeding.
# 4. Run `python release.py -o C:\work\gaia` to sync changes from aigdat/gaia
#    into your Gaia OSS clone.
# 5. Use `git add` to add any new files. NOTE: be mindful when doing this! Make sure that
#    no internal/NDA files slipped through the filters.
# 6. Use `git commit -am MESSAGE` and `git push` to sync your updates to the server.
# 7. Launch a PR for your branch on the OSS repo.
#
# Details of operation:
# - All source files under src/gaia are copied, except those that violate the
#   `exclude` list filter.
#   - NOTE: the `--internal` arg disables the exclude filter! Only use this when
#     syncing to an AMD-internal clone.
# - The script uses Git to identify tracked files in the source repository
# - Files are filtered based on an exclude list to prevent internal/NDA content from being copied
# - The script creates the necessary directory structure in the target repository
# - The script copies all files and then updates all markdown files with correct github links
# - The script prints out which files will be copied, which are excluded, and their destination paths

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import List

from util.docs import update_github_links


def remove_empty_directories(directory):
    """
    Recursively remove empty directories within the given directory.
    Returns count of directories removed.
    """
    removed_count = 0

    # Walk the directory tree bottom-up so we can remove parent dirs after children
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Check if directory is empty (no files and no subdirectories)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"  Removed empty directory: {dir_path}")
                    removed_count += 1
            except OSError:
                # Directory not empty or permission error, skip it
                pass

    return removed_count


def prompt_delete_file(file_path):
    """
    Prompt the user to delete a file and delete it if confirmed.
    Returns True if deleted, False otherwise.
    """
    while True:
        response = input(f"\nDelete {file_path}? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            try:
                os.remove(file_path)
                print(f"  Deleted: {file_path}")
                return True
            except Exception as e:
                print(f"  Error deleting file: {e}")
                return False
        elif response in ["n", "no"]:
            print(f"  Skipped: {file_path}")
            return False
        else:
            print("  Please enter 'y' or 'n'")


def copy_and_update(path, new_path):
    """
    Copy a Gaia file to its target location and update content if needed
    Returns: 'added' if new file, 'modified' if existing file updated
    """
    # Create target directory if it doesn't exist
    new_path_dir = Path(new_path).parent
    os.makedirs(new_path_dir, exist_ok=True)

    # Check if file already exists
    file_exists = os.path.exists(new_path)

    # Copy the file
    shutil.copy2(path, new_path)

    return "modified" if file_exists else "added"


def main():
    parser = argparse.ArgumentParser(
        description="Release script for Gaia to OSS repo. Instructions: "
        "1. Clone the Gaia OSS repo to a LOCATION on your disk, "
        "2. Make a branch in the Gaia clone, "
        "3. `python release.py -o LOCATION`, "
        "4. Add/commit files as needed and make a pull request into the Gaia OSS repo"
    )

    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Location on disk of a Gaia repo clone that will "
        "be used to perform the pull request into Gaia OSS",
    )

    parser.add_argument(
        "--internal",
        help="Include artifacts that are safe to share within AMD",
        action="store_true",
    )

    args = parser.parse_args()

    gaia_location = Path(__file__).parent
    destination_location = Path(args.output)

    # Validate destination directory exists
    if not destination_location.exists():
        print(f"Error: Destination directory does not exist: {destination_location}")
        return 1
    if not destination_location.is_dir():
        print(f"Error: Destination path is not a directory: {destination_location}")
        return 1

    # Fixed exclude paths - using os.path.sep to ensure correct path separators
    # Also, a missing comma was added after "docs\\nimbys.md"
    exclude = [
        f".github{os.path.sep}workflows{os.path.sep}local_hybrid_tests.yml",
        f".github{os.path.sep}workflows{os.path.sep}test_installer_npu.yml",
        f".github{os.path.sep}workflows{os.path.sep}test_chat_sdk.yml",
        f".github{os.path.sep}workflows{os.path.sep}test_gaia_cli_windows.yml",
        f"docs{os.path.sep}nimbys.md",
        f"nda",  # Added the NDA directory itself
        f"notebooks",
        "release.py",
    ]

    # If --internal flag is used, don't filter out any files
    if args.internal:
        exclude = []

    # Get the list of tracked files using Git index
    git_output = subprocess.check_output(
        ["git", "ls-files"], cwd=gaia_location, stderr=subprocess.DEVNULL
    )
    tracked_files = git_output.decode("utf-8").splitlines()

    # Construct absolute paths for tracked files
    file_paths = [
        os.path.abspath(os.path.join(gaia_location, filename))
        for filename in tracked_files
    ]

    # Filter files to exclude NDA content
    filtered_file_paths: List[str] = []
    for path in file_paths:
        # Get the relative path from gaia_location and normalize separators
        rel_path = os.path.relpath(path, gaia_location)
        # Normalize to forward slashes for consistent comparison (git uses forward slashes)
        rel_path_normalized = rel_path.replace(os.path.sep, "/")

        # Check if the path should be excluded
        filter_out = any(
            rel_path_normalized == ex.replace(os.path.sep, "/")
            or rel_path_normalized.startswith(f"{ex.replace(os.path.sep, '/')}/")
            for ex in exclude
        )

        if not filter_out:
            filtered_file_paths.append(path)

    print("The following source files will be copied:\n")
    for path in filtered_file_paths:
        print(path)

    print("\n\nThe following source files were NOT copied due to an exclude rule:\n")
    for path in file_paths:
        if path not in filtered_file_paths:
            print(path)

    # Get list of tracked files in destination (to identify deletions)
    destination_tracked_files = set()
    if os.path.exists(os.path.join(destination_location, ".git")):
        try:
            dest_git_output = subprocess.check_output(
                ["git", "ls-files"], cwd=destination_location, stderr=subprocess.DEVNULL
            )
            destination_tracked_files = set(
                dest_git_output.decode("utf-8").splitlines()
            )
        except subprocess.CalledProcessError:
            # Destination is not a git repo or git command failed
            pass

    # Track file operations
    added_files = []
    modified_files = []
    source_relative_files = set()

    # Copy the files
    print("\n\nThe new paths are:\n")
    for path in filtered_file_paths:
        # Use Path objects for proper path manipulation
        rel_path = os.path.relpath(path, gaia_location)
        new_path = destination_location / rel_path
        print(new_path)
        operation = copy_and_update(path, str(new_path))

        # Track the relative path for deletion detection (normalized to forward slashes)
        rel_path_normalized = rel_path.replace(os.path.sep, "/")
        source_relative_files.add(rel_path_normalized)

        if operation == "added":
            added_files.append(str(new_path))
        else:
            modified_files.append(str(new_path))

    # Identify deleted files (in destination but not in filtered source)
    deleted_files = []
    for dest_file in destination_tracked_files:
        # Normalize destination file path to forward slashes (git always uses forward slashes)
        dest_file_normalized = dest_file.replace("\\", "/")

        # Check if this file should be in our filtered list
        # Only consider it deleted if it's not in the exclude list
        should_be_excluded = any(
            dest_file_normalized == ex.replace(os.path.sep, "/")
            or dest_file_normalized.startswith(f"{ex.replace(os.path.sep, '/')}/")
            for ex in exclude
        )

        # File is considered deleted if it's not excluded and not in our source files
        if not should_be_excluded and dest_file_normalized not in source_relative_files:
            # Convert back to OS-specific path for file operations
            file_path = str(destination_location / dest_file_normalized)
            # Only add to deletion list if file actually exists on filesystem
            if os.path.exists(file_path):
                deleted_files.append(file_path)

    # Then update GitHub links for all .md files
    update_github_links(str(destination_location))

    # Handle deleted files - prompt user to delete each one
    actually_deleted = []
    if deleted_files:
        print("\n" + "=" * 70)
        print("OBSOLETE FILES DETECTED")
        print("=" * 70)
        print(
            f"\nFound {len(deleted_files)} file(s) in destination that no longer exist in source:"
        )
        for deleted_file in deleted_files:
            print(f"  - {deleted_file}")

        print("\n" + "=" * 70)
        print("DELETION PROMPT")
        print("=" * 70)
        print("\nYou will be prompted to delete each obsolete file.\n")

        for deleted_file in deleted_files:
            if prompt_delete_file(deleted_file):
                actually_deleted.append(deleted_file)

    # Remove empty directories after file deletion
    empty_dirs_removed = 0
    if actually_deleted:
        print("\n" + "=" * 70)
        print("CLEANING UP EMPTY DIRECTORIES")
        print("=" * 70)
        print("\nRemoving empty directories left behind after file deletion...\n")
        empty_dirs_removed = remove_empty_directories(str(destination_location))

        if empty_dirs_removed > 0:
            print(
                f"\nRemoved {empty_dirs_removed} empty director{'y' if empty_dirs_removed == 1 else 'ies'}"
            )
        else:
            print("No empty directories found.")

    # Print summary statistics
    print("\n" + "=" * 70)
    print("RELEASE SUMMARY")
    print("=" * 70)
    print(f"Files added:       {len(added_files)}")
    print(f"Files modified:    {len(modified_files)}")
    print(f"Files deleted:     {len(actually_deleted)}")
    print(f"Files skipped:     {len(deleted_files) - len(actually_deleted)}")
    print(f"Files excluded:    {len(file_paths) - len(filtered_file_paths)}")
    print(f"Dirs removed:      {empty_dirs_removed}")
    print("=" * 70)

    print("\ndone!")


if __name__ == "__main__":
    main()
