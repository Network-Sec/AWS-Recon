#!/usr/bin/env python3

# Script to sort out key pars from unclean grep results

import sys
import re
import argparse

# Configuration for Trash/Placeholder values to ignore
TRASH_VALUES = {
    "EXAMPLE", "YOUR_SECRET_KEY", "YOUR_ACCESS_KEY",
    "XXXXXXX", "INSERT_KEY_HERE", "AWS_KEY",
    "AKIAIOSFODNN7EXAMPLE", # AWS Documentation Example Key
    "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", # AWS Documentation Example Secret
    "JE7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY"
}

def is_trash(value):
    """
    Checks if the value is trash/placeholder using length,
    blocklists, and regex patterns for sequences/repetition.
    """
    if not value:
        return True

    # 1. Length Check (AWS Access Key IDs are 20 chars, Secrets are 40)
    if len(value) < 16 or len(value) > 64:
        return True

    # 2. Blocklist Check
    if any(t in value for t in TRASH_VALUES):
        return True

    # 3. Regex: Repetitive Characters (e.g., AAAAA, 11111)
    if re.fullmatch(r'(.)\1+', value):
        return True

    # 4. Regex: Sequential Characters (e.g., 12345, ABCDE)
    if re.search(r'(?:01234|12345|23456|34567|45678|56789)', value):
        return True
    if re.search(r'(?:abcde|bcdef|cdefg|defgh|efghi|fghij)', value, re.IGNORECASE):
        return True

    return False

def clean_line(line):
    """Parses a line to extract key/secret type and value."""
    line = line.strip()
    if not line or line.startswith('#') or "=" not in line:
        return None, None

    parts = line.split("=", 1)
    if len(parts) != 2:
        return None, None

    key_part, val_part = parts

    key_part = key_part.upper().strip()

    if "SECRET" in key_part:
        key_type = "SECRET"
    elif "KEY" in key_part or "ID" in key_part:
        key_type = "ID"
    else:
        return None, None

    # Clean values
    val_part = re.sub(r"['\"\s]", "", val_part)

    return key_type, val_part

def process_file(input_file, output_file, linear_mode):
    pairs = []
    orphans = 0
    trash_count = 0

    current_key_id = None
    key_matched = False  # Track if the current key has been paired at least once

    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    print(f"{YELLOW}[*] Processing {input_file}...{RESET}")

    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"{RED}[!] Error: File {input_file} not found.{RESET}")
        return

    for line in lines:
        k_type, value = clean_line(line)

        if not k_type or not value:
            continue

        if is_trash(value):
            trash_count += 1
            continue

        if k_type == "ID":
            # If we hit a new ID, check if the previous one was never used
            if current_key_id and not key_matched:
                orphans += 1

            # Start tracking new Key ID
            current_key_id = value
            key_matched = False # Reset match status for new key

        elif k_type == "SECRET":
            if current_key_id:
                # We have a pair
                pairs.append((current_key_id, value))
                key_matched = True
                # CRITICAL CHANGE: Do NOT reset current_key_id here.
                # It remains active for subsequent secrets until a new ID is found.
            else:
                # Secret without a preceding Key ID
                orphans += 1

    # Handle the very last key in the file if it was never matched
    if current_key_id and not key_matched:
        orphans += 1

    # Remove Duplicates
    unique_pairs = list(set(pairs))
    dups_removed = len(pairs) - len(unique_pairs)

    try:
        with open(output_file, 'w') as f:
            for kid, ksec in unique_pairs:
                if linear_mode:
                    f.write(f"{kid} {ksec}\n")
                else:
                    f.write(f"AWS_ACCESS_KEY_ID={kid}\n")
                    f.write(f"AWS_SECRET_ACCESS_KEY={ksec}\n")
    except IOError as e:
        print(f"{RED}[!] Error writing to file: {e}{RESET}")
        return

    print(f"{GREEN}[+] Done.{RESET}")
    print(f"    Pairs generated:  {len(unique_pairs)}")
    print(f"    Orphans dropped:  {orphans}")
    print(f"    Trash filtered:   {trash_count}")
    print(f"    Duplicates rm'd:  {dups_removed}")
    print(f"    Output saved to:  {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and organize AWS credentials text files.")
    parser.add_argument("input", help="Input text file path")
    parser.add_argument("output", help="Output text file path")
    parser.add_argument("-l", "--linear", action="store_true", help="Output in linear format ('KEY' 'SECRET')")

    args = parser.parse_args()

    process_file(args.input, args.output, args.linear)
