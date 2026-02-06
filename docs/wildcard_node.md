# Scromfy Wildcard Processor

The `WildcardProcessor` node provides a flexible way to add dynamic, randomized content to your prompts using local text files. It supports recursive resolution and reproducible randomness.

## Core Features

- **Recursive Resolution**: If a selected replacement contains another wildcard tag (e.g., `{color}`), the node will automatically resolve that tag as well (up to a depth of 10).
- **Seeded Randomness**: Use the `seed` field to ensure that your random selections are reproducible.
- **Support for Multiple Syntax**: Recognizes both `[wildcard]` and `{wildcard}` patterns.
- **Easy Management**: Manage your collections by simply adding `.txt` files to the `wildcards/` directory.

## Inputs

*   **text**: The input string containing patterns to be replaced. Example: `A [color] {subject} standing in a [location]`.
*   **seed**: The seed value for the random number generator. The same seed will always produce the same replacements for a given set of wildcard files.

## Outputs

*   **STRING**: The processed text with all successfully identified wildcards replaced.

## Wildcard Directory Structure

All wildcard files should be placed in the `wildcards/` directory at the root of the custom node folder.

### File Format
Create `.txt` files with one entry per line. Lines starting with `#` or empty lines are ignored.

**Example: `wildcards/color.txt`**
```text
red
blue
# Exotic colors
golden {metal}
```

**Example: `wildcards/metal.txt`**
```text
gold
silver
copper
```

## How it Works

1.  The node scans the input text for patterns inside `[]` or `{}`.
2.  It looks for a matching `.txt` file in the `wildcards/` folder (case-insensitive).
3.  A random line is chosen from the file using the provided `seed`.
4.  If the chosen line contains more wildcards, the process repeats.
5.  If a wildcard file is not found, the original tag is left in the text.
