import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime
import os
import shutil

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

# Find all items
for item in root.findall('.//item'):
    post_type = item.find('wp:post_type', ns)
    status = item.find('wp:status', ns)

    if post_type is None:
        continue

    post_type = post_type.text

    # Get status
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

    pub_date_elem = item.find('pubDate')
    pub_date = pub_date_elem.text if pub_date_elem.text else ''

    content_elem = item.find('content:encoded', ns)
    content = content_elem.text if content_elem.text else ''

    excerpt_elem = item.find('excerpt:encoded', ns)
    excerpt = excerpt_elem.text if excerpt_elem.text else ''

    post_id_elem = item.find('wp:post_id', ns)
    post_id = post_id_elem.text if post_id_elem is not None else ''

    post_name_elem = item.find('wp:post_name', ns)
    slug = post_name_elem.text if post_name_elem is not None and post_name_elem.text else ''

    # If slug is empty or just a number, generate from title
    if not slug or slug.isdigit():
        # Generate slug from title
        title_clean = html.unescape(title).lower()
        # Remove special characters and replace with hyphens
        title_clean = re.sub(r'[^\w\s-]', '', title_clean)
        title_clean = re.sub(r'[\s_]+', '-', title_clean)
        title_clean = title_clean.strip('-')
        # Limit length
        slug = title_clean[:100] if title_clean else f'{post_type}-{post_id}'
        # Remove any non-ASCII characters
        slug = slug.encode('ascii', 'ignore').decode('ascii')

    # Get categories
    categories = []
    for cat in item.findall('category'):
        cat_text = cat.text
        if cat_text and cat_text not in ['Uncategorized', 'Tidak Dikategorikan']:
            categories.append(cat_text)

    data = {
        'title': html.unescape(title),
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

print(f"Total posts found: {len(posts)}")
print(f"Total pages found: {len(pages)}")

# Print all posts with dates to debug
print("\n=== ALL POSTS WITH DATES ===")
for p in posts:
    date_str = p['pub_date'][:16] if len(p['pub_date']) > 16 else p['pub_date']
    print(f"{date_str} | {p['title']} (slug: {p['slug']})")

# Import the CSS and HTML generation functions from the previous script
output_dir = r'C:\Users\LENOVO\jayaklampra-site'

# Clean WordPress content
def clean_wp_content(content):
    if not content:
        return ''

    # Remove WordPress blocks comments
    content = re.sub(r'<!-- wp:.*?-->', '', content)
    content = re.sub(r'<!-- /wp:.*?-->', '', content)

    # Convert WordPress figure galleries to simple images
    content = re.sub(r'<figure class="wp-block-image[^"]*".*?<img (src="[^"]+)"[^>]*>.*?</figure>', r'<img src="\1" alt="">', content, flags=re.DOTALL)
    content = re.sub(r'<figure[^>]*>(.*?)</figure>', r'\1', content, flags=re.DOTALL)

    # Convert wp:file to proper download links
    content = re.sub(r'<div class="wp-block-file[^"]*">.*?<a href="([^"]+)">([^<]+)</a>.*?</div>', r'<p><a href="\1" class="download-link" download>\2</a></p>', content, flags=re.DOTALL)

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

# Read the existing CSS from index.html
with open(os.path.join(output_dir, 'index.html'), 'r', encoding='utf-8') as f:
    existing_html = f.read()

# Extract CSS from existing HTML
css_match = re.search(r'<style>(.*?)</style>', existing_html, re.DOTALL)
if css_match:
    css = css_match.group(1)
else:
    css = ''  # Fallback if CSS not found

# Create index.html
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
            <div class="site-logo">
                <img src="images/cropped-huhuhuhuhuhuhuh.jpeg" alt="Jaya Klampra Logo">
            </div>
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

# Add posts to index - get featured image from content
def get_featured_image(post):
    images = re.findall(r'<img[^>]+src="([^"]+)"', post['content'])
    for img_url in images:
        # Check if image is from the site (local)
        if 'wordpress.com' in img_url or 'files.wordpress.com' in img_url:
            # Get filename
            filename = os.path.basename(img_url.split('?')[0])
            # Check if file exists in images folder
            if os.path.exists(os.path.join(output_dir, 'images', filename)):
                return f"images/{filename}"
    return None

for post in posts:
    title = post['title']

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
        first_letter = title[0].upper() if title else '?'
        image_html = f'<div class="post-card-no-image">{first_letter}</div>'

    index_html += f'''
                <article class="post-card">
                    {image_html}
                    <div class="post-card-content">
                        <h3 class="post-card-title">
                            <a href="posts/{post['slug']}.html">{title}</a>
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

print(f"\nCreated updated index.html")

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
            <div class="site-logo">
                <img src="../images/cropped-huhuhuhuhuhuhuh.jpeg" alt="Jaya Klampra Logo">
            </div>
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

    with open(os.path.join(output_dir, 'posts', f"{slug}.html"), 'w', encoding='utf-8') as f:
        f.write(post_html)

print(f"Created {len(posts)} post pages")

print("\n=== DONE! ===")
print(f"Total posts: {len(posts)}")
print("Please check the posts above to confirm all 2024-2026 posts are included!")
