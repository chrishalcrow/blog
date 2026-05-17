import os
import subprocess
import glob

# Configuration
POSTS_DIR = 'posts'
OUTPUT_DIR = 'output'

def extract_markdown_title(file_path):
    """
    Reads a markdown file and extracts the H1 title.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    return lines[0]


def build_blog():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    md_files = glob.glob(os.path.join(POSTS_DIR, '*.md'))
    
    # 2. Parse files to generate navigation links dynamically
    nav_links = []
    pages_to_build = []

    for file_path in md_files:
        filename = os.path.basename(file_path)
        basename, _ = os.path.splitext(filename)
        
        title = extract_markdown_title(file_path)     
        html_filename = f"{basename}.html"

        # Separate other pages from blog post navigation list
        if basename == 'index':
            pages_to_build.append({'path': file_path, 'output': 'index.html', 'title': 'Home'})
        else:
            nav_links.append(f'<li><a href="{html_filename}">{title}</a></li>')
            pages_to_build.append({'path': file_path, 'output': html_filename, 'title': title})

    nav_html_block = "\n".join(nav_links)

    # 3. HTML Base Layout
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="blog-layout">
        <aside class="sidebar">
            <div class="sidebar-brand">
                <a href="index.html">Chris Halcrow's Data Blog</a>
            </div>
            <nav>
                <ul>
                    {navigation}
                </ul>
            </nav>
        </aside>
        <main>
            <article>
                {content}
            </article>
        </main>
    </div>
</body>
</html>
"""

    # 4. Compile Markdown files via Pandoc & build pages
    for page in pages_to_build:
        print(f"Processing: {page['path']} -> {page['output']}")
        
        # Run pandoc command: pandoc input.md -t html
        result = subprocess.run(
	    ['pandoc', page['path'], '-t', 'html'],
	    capture_output=True,
	    text=True,
	    check=True
        )
        markdown_html = result.stdout

        # Inject content into our base layout
        final_html = html_template.format(
            title=page['title'],
            navigation=nav_html_block,
            content=markdown_html
        )

        # Save finished HTML file to output folder
        with open(os.path.join(OUTPUT_DIR, page['output']), 'w', encoding='utf-8') as f:
            f.write(final_html)

    print(f"Blog built successfully inside the '{OUTPUT_DIR}' directory.")

if __name__ == '__main__':
    build_blog()
