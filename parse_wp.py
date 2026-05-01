import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime
import os

# Parse WordPress export
tree = ET.parse(r'C:\Users\LENOVO\Downloads\jayaklampra.WordPress.2026-05-01.xml')
root = tree.getroot()

# Define namespaces
ns = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

posts = []
pages = []
attachments = []

# Find all items
for item in root.findall('.//item'):
    post_type = item.find('wp:post_type', ns)
    status = item.find('wp:status', ns)

    if post_type is None:
        continue

    post_type = post_type.text

    # Get status, default to 'publish' if missing
    if status is None:
        status = 'publish'
    else:
        status = status.text

    # Skip non-published posts (but keep all pages)
    if post_type == 'post' and status != 'publish':
        continue

    # Skip attachments
    if post_type == 'attachment':
        continue

    title_elem = item.find('title')
    title = title_elem.text if title_elem.text else ''

    link_elem = item.find('link')
    link = link_elem.text if link_elem.text else ''

    pub_date_elem = item.find('pubDate')
    pub_date = pub_date_elem.text if pub_date_elem.text else ''

    content_elem = item.find('content:encoded', ns)
    content = content_elem.text if content_elem.text else ''

    excerpt_elem = item.find('excerpt:encoded', ns)
    excerpt = excerpt_elem.text if excerpt_elem.text else ''

    post_id_elem = item.find('wp:post_id', ns)
    post_id = post_id_elem.text if post_id_elem is not None else ''

    post_name_elem = item.find('wp:post_name', ns)
    slug = post_name_elem.text if post_name_elem is not None and post_name_elem.text else f'{post_type}-{post_id}'

    # Get categories
    categories = []
    for cat in item.findall('category'):
        cat_text = cat.text
        if cat_text and cat_text not in ['Uncategorized', 'Tidak Dikategorikan']:
            categories.append(cat_text)

    data = {
        'title': html.unescape(title),
        'link': link,
        'content': content,
        'excerpt': excerpt,
        'pub_date': pub_date,
        'id': post_id,
        'slug': slug,
        'categories': categories,
        'status': status
    }

    if post_type == 'post':
        posts.append(data)
    elif post_type == 'page':
        pages.append(data)

# Sort posts by date (newest first)
posts.sort(key=lambda x: x['pub_date'], reverse=True)

print(f"Found {len(posts)} posts")
print(f"Found {len(pages)} pages")

# Debug: print some post dates
print("\n=== Sample post dates ===")
for p in posts[:10]:
    print(f"{p['pub_date']}: {p['title']}")

print("\n=== All pages ===")
for p in pages:
    print(f"{p['slug']}: {p['title']}")

# Create output directory
output_dir = r'C:\Users\LENOVO\jayaklampra-site'
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, 'posts'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'pages'), exist_ok=True)

# Clean WordPress content
def clean_wp_content(content):
    if not content:
        return ''

    # Remove WordPress blocks comments
    content = re.sub(r'<!-- wp:.*?-->', '', content)
    content = re.sub(r'<!-- /wp:.*?-->', '', content)

    # Convert WordPress figure galleries to simple images
    content = re.sub(r'<figure class="wp-block-image[^"]*".*?<img (src="[^"]+")[^>]*>.*?</figure>', r'<img \1 alt="">', content, flags=re.DOTALL)
    content = re.sub(r'<figure[^>]*>(.*?)</figure>', r'\1', content, flags=re.DOTALL)

    # Convert wp:file to proper download links
    content = re.sub(r'<div class="wp-block-file[^"]*">.*?<a href="([^"]+)">([^<]+)</a>.*?</div>',
                     r'<p><a href="\1" class="download-link" download>\2</a></p>', content, flags=re.DOTALL)

    # Clean up extra whitespace
    content = re.sub(r'\s+', ' ', content)

    # Convert remaining HTML to simpler format
    content = content.replace('<p>', '<p>')
    content = content.replace('</p>', '</p>')

    return content

def format_date(date_str):
    """Format date to Indonesian format"""
    try:
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        months = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except:
        return date_str

# Create CSS
css = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --bg-primary: #0a0a0c;
    --bg-secondary: #111113;
    --text-primary: #e8e6e3;
    --text-secondary: #9b9a97;
    --accent: #c9a87c;
    --accent-glow: rgba(201, 168, 124, 0.1);
    --border: rgba(255, 255, 255, 0.06);
}

body {
    font-family: 'Georgia', serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.8;
    min-height: 100vh;
}

.container {
    max-width: 720px;
    margin: 0 auto;
    padding: 0 24px;
}

/* Header */
header {
    padding: 80px 0 60px;
    text-align: center;
    border-bottom: 1px solid var(--border);
}

.site-title {
    font-size: 2rem;
    font-weight: normal;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    color: var(--text-primary);
}

.site-tagline {
    font-size: 0.95rem;
    color: var(--text-secondary);
    font-style: italic;
}

/* Navigation */
nav {
    padding: 32px 0;
    border-bottom: 1px solid var(--border);
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 40px;
    flex-wrap: wrap;
}

nav a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    transition: color 0.3s;
}

nav a:hover {
    color: var(--accent);
}

/* Main Content */
main {
    padding: 60px 0 100px;
}

/* Post List */
.post-list {
    display: flex;
    flex-direction: column;
    gap: 60px;
}

.post-item {
    padding-bottom: 40px;
    border-bottom: 1px solid var(--border);
}

.post-item:last-child {
    border-bottom: none;
}

.post-title {
    font-size: 1.5rem;
    font-weight: normal;
    margin-bottom: 16px;
}

.post-title a {
    color: var(--text-primary);
    text-decoration: none;
    transition: color 0.3s;
}

.post-title a:hover {
    color: var(--accent);
}

.post-excerpt {
    color: var(--text-secondary);
    font-size: 1rem;
    margin-bottom: 16px;
    line-height: 1.7;
}

.post-date {
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-style: italic;
}

.post-categories {
    margin-top: 12px;
}

.post-categories a {
    color: var(--accent);
    text-decoration: none;
    font-size: 0.8rem;
    margin-right: 12px;
}

/* Single Post */
.post-content {
    font-size: 1.1rem;
    line-height: 1.9;
}

.post-content h2 {
    font-size: 1.6rem;
    font-weight: normal;
    margin: 48px 0 24px;
    color: var(--accent);
}

.post-content h3 {
    font-size: 1.3rem;
    font-weight: normal;
    margin: 36px 0 20px;
}

.post-content p {
    margin-bottom: 24px;
}

.post-content img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin: 32px 0;
}

.post-content blockquote {
    border-left: 2px solid var(--accent);
    padding-left: 24px;
    margin: 32px 0;
    font-style: italic;
    color: var(--text-secondary);
}

.post-content ul, .post-content ol {
    margin-left: 24px;
    margin-bottom: 24px;
}

.post-content li {
    margin-bottom: 12px;
}

.download-link {
    display: inline-block;
    padding: 12px 24px;
    background: var(--accent);
    color: var(--bg-primary);
    text-decoration: none;
    border-radius: 4px;
    margin: 24px 0;
}

.download-link:hover {
    opacity: 0.9;
}

.post-meta {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
}

.back-link {
    display: inline-block;
    margin-top: 60px;
    color: var(--accent);
    text-decoration: none;
    font-size: 0.9rem;
}

.back-link:hover {
    text-decoration: underline;
}

/* Footer */
footer {
    padding: 40px 0;
    text-align: center;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.85rem;
}

/* Page Styles */
.page-content {
    font-size: 1.1rem;
    line-height: 1.9;
}

.page-content h1 {
    font-size: 2rem;
    font-weight: normal;
    margin-bottom: 32px;
    color: var(--accent);
}

.page-content h2 {
    font-size: 1.5rem;
    font-weight: normal;
    margin: 40px 0 20px;
}

.page-content p {
    margin-bottom: 24px;
}

/* Responsive */
@media (max-width: 768px) {
    header {
        padding: 60px 0 40px;
    }

    .site-title {
        font-size: 1.6rem;
    }

    nav ul {
        gap: 24px;
    }

    nav a {
        font-size: 0.8rem;
    }

    main {
        padding: 40px 0 60px;
    }

    .post-content {
        font-size: 1rem;
    }
}
'''

# Create index.html with all posts
index_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jaya Klampra</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="site-title">Jaya Klampra</h1>
            <p class="site-tagline">Every soul will taste of death</p>
        </header>

        <nav>
            <ul>
                <li><a href="index.html">Home</a></li>
                <li><a href="pages/e-buku.html">E-Book</a></li>
                <li><a href="pages/about-me.html">About</a></li>
            </ul>
        </nav>

        <main>
            <div class="post-list">
'''

# Add posts to index
for post in posts:
    title = post['title']

    # Get excerpt from content or excerpt field
    excerpt = post['excerpt']
    if not excerpt or len(excerpt) < 10:
        content_clean = clean_wp_content(post['content'])
        # Remove HTML tags for excerpt
        p_match = re.search(r'<p>([^<]+)</p>', content_clean)
        if p_match:
            excerpt = p_match.group(1)[:300] + '...'
        else:
            excerpt = content_clean[:300] + '...' if len(content_clean) > 300 else content_clean

    date_str = format_date(post['pub_date'])
    categories_html = ''
    if post['categories']:
        categories_html = '<div class="post-categories">' + ''.join([f'<a href="#">{cat}</a>' for cat in post['categories']]) + '</div>'

    index_html += f'''
                <article class="post-item">
                    <h2 class="post-title">
                        <a href="posts/{post['slug']}.html">{title}</a>
                    </h2>
                    <p class="post-excerpt">{excerpt}</p>
                    {categories_html}
                    <time class="post-date">{date_str}</time>
                </article>
    '''

index_html += f'''
            </div>
        </main>

        <footer>
            <p>&copy; 2025 Jaya Klampra. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
'''

# Write index.html
with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)

print(f"Created index.html")

# Create individual post pages
for post in posts:
    content = clean_wp_content(post['content'])
    title = post['title']
    date_str = format_date(post['pub_date'])

    categories_html = ''
    if post['categories']:
        categories_html = '<div class="post-categories">' + ' '.join([f'<span>#{cat}</span>' for cat in post['categories']]) + '</div>'

    post_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Jaya Klampra</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="site-title">Jaya Klampra</h1>
            <p class="site-tagline">Every soul will taste of death</p>
        </header>

        <nav>
            <ul>
                <li><a href="../index.html">Home</a></li>
                <li><a href="../pages/e-buku.html">E-Book</a></li>
            </ul>
        </nav>

        <main>
            <article>
                <div class="post-meta">
                    <time>{date_str}</time>
                    {categories_html}
                </div>

                <h1 class="page-content">{title}</h1>

                <div class="post-content">
                    {content}
                </div>

                <a href="../index.html" class="back-link">&larr; Back to Articles</a>
            </article>
        </main>

        <footer>
            <p>&copy; 2025 Jaya Klampra. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
    '''

    with open(os.path.join(output_dir, 'posts', f"{post['slug']}.html"), 'w', encoding='utf-8') as f:
        f.write(post_html)

print(f"Created {len(posts)} post pages")

# Create pages
for page in pages:
    content = clean_wp_content(page['content'])
    title = page['title']
    slug = page['slug']

    page_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Jaya Klampra</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="site-title">Jaya Klampra</h1>
            <p class="site-tagline">Every soul will taste of death</p>
        </header>

        <nav>
            <ul>
                <li><a href="../index.html">Home</a></li>
                <li><a href="e-buku.html">E-Book</a></li>
                <li><a href="about-me.html">About</a></li>
            </ul>
        </nav>

        <main>
            <article>
                <h1 class="page-content">{title}</h1>

                <div class="page-content">
                    {content}
                </div>
            </article>
        </main>

        <footer>
            <p>&copy; 2025 Jaya Klampra. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
    '''

    with open(os.path.join(output_dir, 'pages', f"{slug}.html"), 'w', encoding='utf-8') as f:
        f.write(page_html)

print(f"Created {len(pages)} page pages")
print("Done! Site created at: C:\\Users\\LENOVO\\jayaklampra-site")
