import os
import shutil
from pathlib import Path

# Create output directory
output_dir = 'dist'
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

# Copy all HTML files from templates
templates_dir = Path('templates')
for html_file in templates_dir.glob('*.html'):
    shutil.copy(html_file, output_dir)

# Copy static folder
if os.path.exists('static'):
    shutil.copytree('static', os.path.join(output_dir, 'static'))

print(f"✓ Built {len(list(Path(output_dir).glob('*.html')))} HTML files to {output_dir}/")