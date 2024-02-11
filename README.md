# worddiff
A diff tool that will highlight individual words that are different instead of highlighting entire lines that contain a difference. 

This Python script provides a detailed, side-by-side comparison of two text files, highlighting differences with options for color coding, underlining, and custom column widths.

## Features

- **Dynamic Column Width:** Automatically adjusts based on terminal size or can be manually set.
- **Color Highlighting:** Differences can be highlighted in color. Colors for insertion, deletion, and replacement are customizable.
- **Underline Differences:** Option to underline the differences for added visibility.
- **Custom Headers:** Ability to set custom headers for each column in the comparison.

## Usage

Basic command structure:
python cdiff.py <file1> <file2> [options]


Options include:
- `-o, --output`: Specify an output file.
- `--fixed_width`: Set a fixed width for each column.
- `--color/--no-color`: Enable or disable colorized output.
- `--underline`: Enable underline for differences.
- Additional options for setting colors and headers.

For detailed usage and all options, run `python cdiff.py --help`.

## Configuration

Customize default settings via `config.ini`, allowing preset values for column width, coloring, and more.

## Requirements

- Python 3.x
- termcolor (for colored output)

