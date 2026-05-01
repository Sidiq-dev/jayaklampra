import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime
import os
import urllib.request
import urllib.parse
from pathlib import Path

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
all_images = []  # Store all image URLs

# Create directories
output_dir = r'C:\Users\LENOVO\jayaklampra-site'
images_dir = os.path.join(output_dir, 'images')
posts_dir = os.path.join(output_dir, 'posts')
pages_dir = os.path.join(output_dir, 'pages')

os.makedirs(images_dir, exist_ok=True)
os.makedirs(posts_dir, exist_ok=True)
os.makedirs(pages_dir, exist_ok=True)

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
        # Get attachment URL for downloading
        attachment_url = item.find('wp:attachment_url', ns)
        if attachment_url is not None and attachment_url.text:
            all_images.append(attachment_url.text)
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

    # Get featured image
    featured_image = None
    for meta in item.findall('wp:postmeta', ns):
        meta_key = meta.find('wp:meta_key', ns)
        if meta_key is not None and meta_key.text == '_thumbnail_id':
            meta_value = meta.find('wp:meta_value', ns)
            if meta_value is not None:
                featured_image_id = meta_value.text

    # Extract images from content
    content_images = re.findall(r'<img[^>]+src="([^"]+)"', content)
    for img_url in content_images:
        if img_url not in all_images:
            all_images.append(img_url)

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
        'status': status,
        'featured_image': featured_image,
        'content_images': content_images
    }

    if post_type == 'post':
        posts.append(data)
    elif post_type == 'page':
        pages.append(data)

# Sort posts by date (newest first)
posts.sort(key=lambda x: x['pub_date'], reverse=True)

print(f"Found {len(posts)} posts")
print(f"Found {len(pages)} pages")
print(f"Found {len(all_images)} unique images")

# Download images
def download_image(url, dest_path):
    """Download image from URL to local path"""
    try:
        # Handle WordPress.com URLs
        if 'wordpress.com' in url or 'files.wordpress.com' in url:
            # Remove query parameters
            url = url.split('?')[0]

        # Create filename from URL
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)

        # If filename is empty or just extension, generate one
        if not filename or '.' not in filename:
            filename = f"image_{hash(url)}.jpg"

        dest_file = os.path.join(dest_path, filename)

        # Skip if already exists
        if os.path.exists(dest_file):
            return f"images/{filename}"

        # Download
        urllib.request.urlretrieve(url, dest_file)
        print(f"Downloaded: {filename}")
        return f"images/{filename}"

    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return url  # Return original URL if download fails

# Download all images (limit to first 50 for speed)
print("\n=== Downloading images ===")
downloaded_images = {}
for i, img_url in enumerate(all_images[:50]):  # Limit to 50 for now
    if img_url not in downloaded_images:
        local_path = download_image(img_url, images_dir)
        downloaded_images[img_url] = local_path

print(f"Downloaded {len(downloaded_images)} images")

# Clean WordPress content
def clean_wp_content(content, post_images=None):
    if not content:
        return ''

    # Remove WordPress blocks comments
    content = re.sub(r'<!-- wp:.*?-->', '', content)
    content = re.sub(r'<!-- /wp:.*?-->', '', content)

    # Convert WordPress figure galleries to simple images with captions
    content = re.sub(
        r'<figure class="wp-block-image[^"]*".*?<img (src="[^"]+)"[^>]*>.*?<figcaption[^>]*>([^<]*)</figcaption>.*?</figure>',
        r'<div class="image-caption"><img src="\1" alt=""><figcaption>\2</figcaption></div>',
        content,
        flags=re.DOTALL
    )

    # Simple figures without captions
    content = re.sub(
        r'<figure class="wp-block-image[^"]*".*?<img (src="[^"]+)"[^>]*>.*?</figure>',
        r'<img src="\1" alt="" class="content-image">',
        content,
        flags=re.DOTALL
    )

    # Generic figures
    content = re.sub(r'<figure[^>]*>(.*?)</figure>', r'\1', content, flags=re.DOTALL)

    # Convert wp:file to proper download links
    content = re.sub(
        r'<div class="wp-block-file[^"]*">.*?<a href="([^"]+)">([^<]+)</a>.*?</div>',
        r'<div class="download-box"><a href="\1" class="download-link" download target="_blank">\2</a></div>',
        content,
        flags=re.DOTALL
    )

    # Clean up extra whitespace but preserve paragraph structure
    content = re.sub(r'<p>\s*</p>', '', content)
    content = re.sub(r'\s+', ' ', content)

    # Fix unclosed p tags
    content = re.sub(r'<p>([^<]+)$', r'<p>\1</p>', content, flags=re.MULTILINE)

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

# Create CSS with improved layout
css = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --bg-primary: #0a0a0c;
    --bg-secondary: #111113;
    --bg-card: #161618;
    --text-primary: #e8e6e3;
    --text-secondary: #9b9a97;
    --accent: #c9a87c;
    --accent-glow: rgba(201, 168, 124, 0.1);
    --border: rgba(255, 255, 255, 0.08);
}

body {
    font-family: 'Georgia', serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.8;
    min-height: 100vh;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 24px;
}

/* Header */
header {
    padding: 80px 0 40px;
    text-align: center;
    border-bottom: 1px solid var(--border);
}

.site-title {
    font-size: 2.2rem;
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
    padding: 24px 0;
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
    font-size: 0.85rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    transition: color 0.3s;
    position: relative;
}

nav a:hover {
    color: var(--accent);
}

nav a::after {
    content: "";
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 0;
    height: 1px;
    background: var(--accent);
    transition: width 0.3s;
}

nav a:hover::after {
    width: 100%;
}

/* Main Content */
main {
    padding: 60px 0 100px;
}

/* Hero Section */
.hero {
    text-align: center;
    padding: 60px 0 80px;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: normal;
    margin-bottom: 24px;
    color: var(--accent);
}

.hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto;
}

/* Post Grid */
.post-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 32px;
}

/* Post Card */
.post-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s;
    display: flex;
    flex-direction: column;
}

.post-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.post-card-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    background: var(--bg-secondary);
}

.post-card-no-image {
    width: 100%;
    height: 200px;
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    color: var(--border);
}

.post-card-content {
    padding: 24px;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.post-card-title {
    font-size: 1.2rem;
    font-weight: normal;
    margin-bottom: 12px;
    line-height: 1.4;
}

.post-card-title a {
    color: var(--text-primary);
    text-decoration: none;
    transition: color 0.3s;
}

.post-card-title a:hover {
    color: var(--accent);
}

.post-card-excerpt {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 16px;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex: 1;
}

.post-card-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: auto;
}

.post-card-date {
    font-style: italic;
}

.post-card-category {
    color: var(--accent);
}

/* Single Post */
.post-header {
    text-align: center;
    padding: 40px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
}

.post-title-large {
    font-size: 2.5rem;
    font-weight: normal;
    margin-bottom: 24px;
    line-height: 1.3;
}

.post-meta-info {
    display: flex;
    justify-content: center;
    gap: 24px;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.post-meta-info span {
    display: flex;
    align-items: center;
    gap: 8px;
}

.post-content {
    font-size: 1.15rem;
    line-height: 1.9;
}

.post-content h2 {
    font-size: 1.8rem;
    font-weight: normal;
    margin: 56px 0 24px;
    color: var(--accent);
}

.post-content h3 {
    font-size: 1.4rem;
    font-weight: normal;
    margin: 40px 0 20px;
    color: var(--text-primary);
}

.post-content p {
    margin-bottom: 28px;
}

.post-content img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 40px auto;
    display: block;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.content-image {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 40px 0;
}

.image-caption {
    margin: 40px 0;
}

.image-caption img {
    margin-bottom: 12px;
}

.image-caption figcaption {
    text-align: center;
    font-size: 0.9rem;
    color: var(--text-secondary);
    font-style: italic;
}

.post-content blockquote {
    border-left: 3px solid var(--accent);
    padding-left: 28px;
    margin: 40px 0;
    font-style: italic;
    color: var(--text-secondary);
    font-size: 1.2rem;
}

.post-content ul, .post-content ol {
    margin-left: 28px;
    margin-bottom: 32px;
}

.post-content li {
    margin-bottom: 16px;
}

.download-box {
    text-align: center;
    margin: 40px 0;
    padding: 40px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
}

.download-link {
    display: inline-block;
    padding: 16px 32px;
    background: var(--accent);
    color: var(--bg-primary);
    text-decoration: none;
    border-radius: 8px;
    font-weight: 500;
    transition: transform 0.3s, box-shadow 0.3s;
}

.download-link:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(201, 168, 124, 0.3);
}

.back-link {
    display: inline-flex;
    align-items: center;
    margin-top: 80px;
    padding: 12px 24px;
    background: var(--bg-card);
    color: var(--accent);
    text-decoration: none;
    border-radius: 8px;
    border: 1px solid var(--border);
    transition: all 0.3s;
}

.back-link:hover {
    background: var(--accent);
    color: var(--bg-primary);
}

/* Footer */
footer {
    padding: 60px 0 40px;
    text-align: center;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.85rem;
}

/* Page Styles */
.page-content {
    font-size: 1.15rem;
    line-height: 1.9;
}

.page-content h1 {
    font-size: 2.5rem;
    font-weight: normal;
    margin-bottom: 40px;
    color: var(--accent);
    text-align: center;
}

.page-content h2 {
    font-size: 1.8rem;
    font-weight: normal;
    margin: 48px 0 24px;
}

.page-content p {
    margin-bottom: 28px;
}

/* E-Book Section */
.ebook-grid {
    display: grid;
    gap: 32px;
    margin-top: 40px;
}

.ebook-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 40px;
    text-align: center;
}

.ebook-card h3 {
    font-size: 1.5rem;
    font-weight: normal;
    margin-bottom: 16px;
    color: var(--accent);
}

.ebook-card p {
    color: var(--text-secondary);
    margin-bottom: 24px;
}

/* Responsive */
@media (max-width: 768px) {
    header {
        padding: 60px 0 32px;
    }

    .site-title {
        font-size: 1.8rem;
    }

    .hero-title {
        font-size: 2rem;
    }

    .post-grid {
        grid-template-columns: 1fr;
    }

    .post-title-large {
        font-size: 1.8rem;
    }

    .post-meta-info {
        flex-direction: column;
        gap: 12px;
    }

    main {
        padding: 40px 0 60px;
    }

    .post-content {
        font-size: 1rem;
    }
}
'''

# Get a featured image for each post
def get_featured_image(post):
    """Get the featured image for a post from content"""
    images = re.findall(r'<img[^>]+src="([^"]+)"', post['content'])
    if images:
        img_url = images[0].split('?')[0]  # Remove query params
        return downloaded_images.get(img_url, img_url)
    return None

# Create index.html with card grid layout
index_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jaya Klampra - Every soul will taste of death</title>
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
                <li><a href="pages/about.html">About</a></li>
            </ul>
        </nav>

        <main>
            <section class="hero">
                <h2 class="hero-title">Tulisan Filsafat & Spiritualitas</h2>
                <p class="hero-subtitle">Merenungkan kehidupan, kesadaran, dan makna eksistensi melalui kata-kata</p>
            </section>

            <section class="post-grid">
'''

# Add posts as cards to index
for post in posts:
    title = post['title']
    slug = post['slug']

    # Get excerpt
    excerpt = post['excerpt']
    if not excerpt or len(excerpt) < 10:
        content_clean = clean_wp_content(post['content'])
        p_match = re.search(r'<p>([^<]+)</p>', content_clean)
        if p_match:
            excerpt = p_match.group(1)[:200] + '...'
        else:
            excerpt = content_clean[:200] + '...' if len(content_clean) > 200 else content_clean

    # Clean excerpt from HTML
    excerpt = re.sub(r'<[^>]+>', '', excerpt)

    date_str = format_date(post['pub_date'])
    category = post['categories'][0] if post['categories'] else 'Umum'

    # Get featured image
    featured_img = get_featured_image(post)

    image_html = ''
    if featured_img:
        image_html = f'<img src="{featured_img}" alt="{title}" class="post-card-image">'
    else:
        # Use first letter of title as placeholder
        first_letter = title[0].upper() if title else '?'
        image_html = f'<div class="post-card-no-image">{first_letter}</div>'

    index_html += f'''
                <article class="post-card">
                    {image_html}
                    <div class="post-card-content">
                        <h3 class="post-card-title">
                            <a href="posts/{slug}.html">{title}</a>
                        </h3>
                        <p class="post-card-excerpt">{excerpt}</p>
                        <div class="post-card-meta">
                            <time class="post-card-date">{date_str}</time>
                            <span class="post-card-category">{category}</span>
                        </div>
                    </div>
                </article>
    '''

index_html += f'''
            </section>
        </main>

        <footer>
            <p>&copy; 2025 Jaya Klampra. Seluruh hak cipta dilindungi.</p>
        </footer>
    </div>
</body>
</html>
'''

# Write index.html
with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)

print(f"Created index.html with card grid layout")

# Create individual post pages
for post in posts:
    content = clean_wp_content(post['content'])
    title = post['title']
    date_str = format_date(post['pub_date'])
    slug = post['slug']

    categories_html = ''
    if post['categories']:
        categories_html = ' | '.join([f'<span style="color: var(--accent)">#{cat}</span>' for cat in post['categories']])

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
                <div class="post-header">
                    <h1 class="post-title-large">{title}</h1>
                    <div class="post-meta-info">
                        <span>📅 {date_str}</span>
                        <span>🏷️ {categories_html if categories_html else 'Umum'}</span>
                    </div>
                </div>

                <div class="post-content">
                    {content}
                </div>

                <div style="text-align: center">
                    <a href="../index.html" class="back-link">&larr; Kembali ke Artikel</a>
                </div>
            </article>
        </main>

        <footer>
            <p>&copy; 2025 Jaya Klampra. Seluruh hak cipta dilindungi.</p>
        </footer>
    </div>
</body>
</html>
    '''

    with open(os.path.join(posts_dir, f"{slug}.html"), 'w', encoding='utf-8') as f:
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
                <li><a href="about.html">About</a></li>
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
            <p>&copy; 2025 Jaya Klampra. Seluruh hak cipta dilindungi.</p>
        </footer>
    </div>
</body>
</html>
    '''

    with open(os.path.join(pages_dir, f"{slug}.html"), 'w', encoding='utf-8') as f:
        f.write(page_html)

print(f"Created {len(pages)} page pages")
print("\n✅ Done! Site created at: C:\\Users\\LENOVO\\jayaklampra-site")
print("✨ New features:")
print("   - Card grid layout with images")
print("   - Downloaded images from WordPress")
print("   - Hero section on homepage")
print("   - Improved typography and spacing")
print("   - Hover effects on cards")
