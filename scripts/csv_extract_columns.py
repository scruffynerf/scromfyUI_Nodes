#!/usr/bin/env python3
"""
CSV Column Extraction Utility
Extracts unique, sorted values from specified CSV columns into separate text files.
Useful for generating wildcard lists for ComfyUI.
"""

import csv
import argparse
import os
import sys

def extract_columns(input_csv, output_dir, no_header=False, columns=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Initialize data storage
    # If no_header is True, we use indices as keys.
    # If False, we use header names.
    extracted_data = {}

    try:
        with open(input_csv, mode='r', encoding='utf-8') as f:
            if no_header:
                reader = csv.reader(f)
                header = None
            else:
                reader = csv.DictReader(f)
                header = reader.fieldnames

            for row in reader:
                if no_header:
                    # row is a list
                    for i, value in enumerate(row):
                        # Filter by columns if specified
                        if columns and str(i) not in columns:
                            continue
                        
                        if i not in extracted_data:
                            extracted_data[i] = set()
                        
                        clean_val = value.strip()
                        if clean_val:
                            extracted_data[i].add(clean_val)
                else:
                    # row is a dict
                    for col_name, value in row.items():
                        # Filter by columns if specified
                        if columns and col_name not in columns:
                            continue
                        
                        if col_name not in extracted_data:
                            extracted_data[col_name] = set()
                        
                        clean_val = value.strip() if value else ""
                        if clean_val:
                            extracted_data[col_name].add(clean_val)

    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Write output files
    for key, values in extracted_data.items():
        # Create filename. Handle indices vs names.
        filename = f"{input_csv}{key}.txt".replace("/", "_").replace("\\", "_")
        filepath = os.path.join(output_dir, filename)
        
        sorted_values = sorted(list(values))
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for val in sorted_values:
                    f.write(f"{val}\n")
            print(f"Extracted {len(sorted_values)} unique values to {filepath}")
        except Exception as e:
            print(f"Error writing to {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract unique, sorted values from CSV columns into text files.")
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("output_dir", help="Directory to save the extracted text files")
    parser.add_argument("--no-header", action="store_true", help="Set this flag if the CSV does not have a header row")
    parser.add_argument("--columns", nargs="+", help="Specific column names or indices to extract (space separated)")

    args = parser.parse_args()

    if not os.path.isfile(args.input_csv):
        print(f"Error: Input file '{args.input_csv}' not found.")
        sys.exit(1)

    extract_columns(args.input_csv, args.output_dir, args.no_header, args.columns)

if __name__ == "__main__":
    main()
