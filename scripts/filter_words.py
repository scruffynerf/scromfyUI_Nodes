#!/usr/bin/env python3
"""
Word Filtering Utility
Removes words (lines) found in a master word list from target text files.
"""

import os
import sys
import argparse
import re

def natural_sort_key(s):
    """Key for natural sorting (e.g., file0.txt < file1.txt < file10.txt)."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def normalize_word(word):
    """
    Normalizes a word for comparison:
    - Lowercase
    - Replace all non-alphanumeric characters (punctuation, underscores, etc.) with spaces
    - Collapse multiple spaces
    """
    if not word:
        return ""
    # Lowercase
    w = word.lower()
    # Replace anything not a letter or number with a space
    w = re.sub(r'[^a-z0-9]', ' ', w)
    # Collapse multiple spaces and strip
    return " ".join(w.split())

def get_txt_files(directory):
    """Returns a naturally sorted list of all .txt files in the directory and its subdirectories."""
    files = []
    if not os.path.isdir(directory):
        return []
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".txt"):
                files.append(os.path.join(root, f))
    files.sort(key=natural_sort_key)
    return files

def load_master_words(master_dir):
    """Reads all .txt files in master_dir and returns a set of normalized unique words."""
    master_words = set()
    txt_files = get_txt_files(master_dir)
    if not txt_files:
        print(f"No .txt files found in {master_dir}.")
        return master_words
        
    print(f"Loading master words from {len(txt_files)} files in {master_dir}...")
    
    for filepath in txt_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        norm = normalize_word(word)
                        if norm:
                            master_words.add(norm)
        except Exception as e:
            print(f"Error reading master file {filepath}: {e}")
            
    print(f"Total unique master words loaded (normalized): {len(master_words)}")
    return master_words

def filter_target_files(target_dir, master_words, add_kept=False):
    """Removes words in master_words from all .txt files in target_dir using normalized comparison."""
    txt_files = get_txt_files(target_dir)
    if not txt_files:
        print(f"No .txt files found in {target_dir}.")
        return

    print(f"Filtering {len(txt_files)} files in {target_dir}...")
    if add_kept:
        print("Cumulative mode ENABLED: Kept words will be added to the filter for subsequent files.")
    
    for filepath in txt_files:
        try:
            # Read and filter
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            filtered_lines = []
            removed_count = 0
            for line in lines:
                word = line.strip()
                if not word:
                    filtered_lines.append(line)
                    continue
                    
                norm = normalize_word(word)
                if norm in master_words:
                    removed_count += 1
                else:
                    filtered_lines.append(line)
                    # If add_kept is enabled, add this normalized word to master_words
                    if add_kept and norm:
                        master_words.add(norm)
            
            # Write back
            if removed_count > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)
                print(f"Updated {os.path.basename(filepath)}: Removed {removed_count} words.")
            else:
                print(f"Skipped {os.path.basename(filepath)}: No matching words found.")
                
        except Exception as e:
            print(f"Error processing target file {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Filter words from target text files based on a master word list.")
    parser.add_argument("master_dir", help="Directory containing master word list .txt files")
    parser.add_argument("target_dir", help="Directory containing target .txt files to filter")
    parser.add_argument("--add-kept", action="store_true", help="Add kept words to the master list as files are processed")

    args = parser.parse_args()

    if not os.path.isdir(args.master_dir):
        print(f"Error: Master directory '{args.master_dir}' not found.")
        sys.exit(1)
    
    if not os.path.isdir(args.target_dir):
        print(f"Error: Target directory '{args.target_dir}' not found.")
        sys.exit(1)

    # Initial master list load
    master_words = load_master_words(args.master_dir)
    
    # Even if master is empty, we might use --add-kept to deduplicate within target_dir
    if not master_words and not args.add_kept:
        print("No master words found and --add-kept is not set. Exiting.")
        return

    filter_target_files(args.target_dir, master_words, args.add_kept)
    print("Filtering complete.")

if __name__ == "__main__":
    main()
