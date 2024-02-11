import argparse
import configparser
import difflib
import re
import shutil
from termcolor import colored
from itertools import zip_longest
import textwrap

# Default configuration values
DEFAULT_CONFIG = {
    'fixed_width': None,  # Calculated dynamically if not set
    'color': True,
    'underline': False,
    'replace_color': 'green,blue',
    'insert_color': 'yellow',
    'delete_color': 'red',
    'header_titles': None,
}

# Load configuration from file
config = configparser.ConfigParser()
config_found = config.read('config.ini')

config = config['DEFAULT'] if 'DEFAULT' in config else {}

def get_config_value(key, command_line_arg, default):
    if command_line_arg is not None:
        return command_line_arg
    if key in config:
        if key in ['color', 'underline']:  # Handle boolean values
            return config.getboolean(key)
        elif key == 'fixed_width':  # Special handling for 'fixed_width' to allow 'None'
            value = config.get(key, default)
            if value.lower() == 'none':
                return None
            try:
                return int(value)
            except ValueError:
                return default
        else:  # For all other string values
            return config.get(key)
    return default


def strip_ansi_codes(text):
    """Strips ANSI escape sequences from a string."""
    return re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', text)

def calculate_fixed_width(fixed_width):
    if fixed_width is None:
        # Dynamically calculate the fixed width based on terminal size
        terminal_width = shutil.get_terminal_size().columns
        return (terminal_width // 2) - 4
    return fixed_width


def underline_text(text, underline):
    return '\033[4m' + text + '\033[0m' if underline else text

def parse(color_str):
    colors = color_str.split(',')
    return colors if len(colors) > 1 else colors * 2

def pad_text(text, width):
    visible_length = len(strip_ansi_codes(text))
    padding_needed = width - visible_length
    return text + ' ' * padding_needed if padding_needed > 0 else text

def title(text, width):
    centered_text = text.center(width)
    return '\033[4m' + centered_text + '\033[0m'

def preprocess_line(line):
    return ' '.join(line.split())

def preprocess_file(filename):
    with open(filename, 'r') as file:
        return [preprocess_line(line) for line in file]

def colorize_difference(orig_word, modified_word, color):
    if orig_word != modified_word:
        return colored(modified_word, color)
    return modified_word

def word_diff(orig_line, modified_line, colors, color=True, underline=False):
    orig_words, mod_words = orig_line.split(), modified_line.split()
    s = difflib.SequenceMatcher(None, orig_words, mod_words)
    orig_output, mod_output = [], []

    def apply_styles(word, word_color, underline):
        if color:
            word = colored(word, word_color)
        if underline:
            word = '\033[4m' + word + '\033[0m'
        return word

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            orig_output.extend(orig_words[i1:i2])
            mod_output.extend(mod_words[j1:j2])
        elif tag == 'replace':
            orig_output.extend([apply_styles(word, colors['replace_color_left'], underline) for word in orig_words[i1:i2]])
            mod_output.extend([apply_styles(word, colors['replace_color_right'], underline) for word in mod_words[j1:j2]])
        elif tag == 'delete':
            orig_output.extend([apply_styles(word, colors['delete_color'], underline) for word in orig_words[i1:i2]])
        elif tag == 'insert':
            mod_output.extend([apply_styles(word, colors['insert_color'], underline) for word in mod_words[j1:j2]])

    return ' '.join(orig_output), ' '.join(mod_output)

def main():
    parser = argparse.ArgumentParser(description="Compare two files and display a side-by-side diff.")
    parser.add_argument('file1', help="First file to compare")
    parser.add_argument('file2', help="Second file to compare")
    parser.add_argument('-o', '--output', help="Output file to write the diff to")
    parser.add_argument('--fixed_width', type=int, help="Fixed width for each column")
    parser.add_argument('--color', action='store_true', default=None, help="Enable colorized output")
    parser.add_argument('--no-color', action='store_false', dest='color', help="Disable colorized output")
    parser.add_argument('--underline', action='store_true', default=None, help="Enable underline for differences")

    parser.add_argument('--replace_color', help="Colors for replacements, specified as 'left,right'")
    parser.add_argument('--insert_color', help="Color for insertions")
    parser.add_argument('--delete_color', help="Color for deletions")
    parser.add_argument('--header_titles', help="Column titles, specified as 'left,right'")
    args = parser.parse_args()

    # Apply configuration and defaults
    fixed_width = int(calculate_fixed_width(get_config_value('fixed_width', args.fixed_width, DEFAULT_CONFIG['fixed_width'])))
    color = get_config_value('color', args.color, DEFAULT_CONFIG['color'])
    underline = get_config_value('underline', args.underline, DEFAULT_CONFIG['underline'])
    replace_colors = parse(get_config_value('replace_color', args.replace_color, DEFAULT_CONFIG['replace_color']))
    insert_color = get_config_value('insert_color', args.insert_color, DEFAULT_CONFIG['insert_color'])
    delete_color = get_config_value('delete_color', args.delete_color, DEFAULT_CONFIG['delete_color'])
    header_titles = get_config_value('header_titles', args.header_titles, DEFAULT_CONFIG['header_titles'])
    header_titles = parse(get_config_value('header_titles', args.header_titles, DEFAULT_CONFIG['header_titles']))
    
    try:
        orig_lines = preprocess_file(args.file1)
        modified_lines = preprocess_file(args.file2)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return

    colors = {'replace_color_left': replace_colors[0], 'replace_color_right':replace_colors[1], 'insert_color': insert_color, 'delete_color': delete_color}

    column_separator = " | "
    diff_output = []

    if header_titles is not None:
        original = title(header_titles[0], fixed_width)
        student = title(header_titles[1], fixed_width)
        header = f"{original:<{fixed_width}}{column_separator}{student}"
        diff_output.append(header)

    s = difflib.SequenceMatcher(None, orig_lines, modified_lines)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            continue  # Skip equal lines to focus on differences
        else:
            for orig, modified in zip_longest(orig_lines[i1:i2], modified_lines[j1:j2], fillvalue=''):
                if orig.strip() == '' and modified.strip() == '':
                    continue  # Skip this pair of lines
                orig_diff, mod_diff = word_diff(orig, modified, colors, color, underline)
                wrapped_orig_diff = textwrap.fill(orig_diff, fixed_width)
                wrapped_mod_diff = textwrap.fill(mod_diff, fixed_width)
                orig_diff_lines = wrapped_orig_diff.split('\n')
                mod_diff_lines = wrapped_mod_diff.split('\n')
                max_lines = max(len(orig_diff_lines), len(mod_diff_lines))
                orig_diff_lines += [''] * (max_lines - len(orig_diff_lines))
                mod_diff_lines += [''] * (max_lines - len(mod_diff_lines))
                for orig_line, mod_line in zip(orig_diff_lines, mod_diff_lines):
                    diff_output.append(f"{pad_text(orig_line, fixed_width)}{column_separator}{pad_text(mod_line, fixed_width)}")

    final_output = '\n'.join(diff_output)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(final_output)
    else:
        print(final_output)
    

if __name__ == "__main__":
    main()
