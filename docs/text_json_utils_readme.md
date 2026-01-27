# Text & JSON Utility Nodes 🔧📦

Standardized utilities for manipulating strings and JSON objects in the "Scromfy Way."

## Text Nodes

### Flexible String List
Combines up to 10 strings with customizable delimiters or line breaks.
- **Toggleable**: Each string input can be enabled or disabled individually.

### First String Wins (Selector)
Takes multiple string inputs and returns the first one that isn't empty or whitespace.
- **Prefix/Suffix**: Optional decorators for the winning string.
- **Fallback**: Returns the fallback string if all inputs are empty.

### Text Lines to List
Splits a block of text into individual lines and returns them as a LIST output.

## JSON Nodes

### Any to JSON
Injects any ComfyUI type (string, image, int) into a JSON object with a specified key.

### Merge JSON Objects
Combines up to 5 existing JSON objects into a single master object.

### Load JSON from File
Reads a JSON object from a specified file path. Returns both the structured JSON data and its raw STRING representation.

### Save JSON to File
Writes a JSON object to disk. Useful for passing metadata to external scripts or creating study logs.
