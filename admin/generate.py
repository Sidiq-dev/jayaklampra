"""
Generate static HTML files from admin data
"""

import json
import os
import re
import html as html_lib
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'posts.json')
OUTPUT_DIR = BASE_DIR
POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')

# Ensure posts directory exists
os.makedirs(POSTS_DIR, exist_ok=True)


def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def clean_wp_content(content, for_post_page=False):
    """Clean WordPress content and optionally fix image paths for post pages"""
    if not content:
        return ''

    # Remove WordPress blocks comments
    content = re.sub(r'<!-- wp:.*?-->', '', content)
    content = re.sub(r'<!-- /wp:.*?-->', '', content)

    # Convert WordPress figure galleries to simple images
    # Fixed: capture only the URL, not src=" part
    content = re.sub(r'<figure class="wp-block-image[^"]*".*?<img src="([^"]+)"[^>]*>.*?</figure>', r'<img src="\1" alt="">', content, flags=re.DOTALL)
    content = re.sub(r'<figure[^>]*>(.*?)</figure>', r'\1', content, flags=re.DOTALL)

    # Convert WordPress URLs to local paths if file exists
    def convert_wp_image(match):
        img_url = match.group(1)
        if 'wordpress.com' in img_url or 'files.wordpress.com' in img_url:
            filename = os.path.basename(img_url.split('?')[0])
            images_dir = os.path.join(OUTPUT_DIR, 'images')
            if os.path.exists(os.path.join(images_dir, filename)):
                # Return path with correct prefix
                prefix = '../images/' if for_post_page else 'images/'
                return f'src="{prefix}{filename}"'
        # Return original if no local file
        prefix = '../images/' if for_post_page else 'images/'
        if img_url.startswith('images/'):
            return f'src="{prefix}{img_url.replace("images/", "")}"'
        return f'src="{img_url}"'

    content = re.sub(r'src="([^"]+)"', convert_wp_image, content)

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


def get_featured_image(post):
    """Get featured image from post content"""
    images = re.findall(r'<img[^>]+src="([^"]+)"', post.get('content', ''))

    # First check for local images (images/filename.ext)
    for img_url in images:
        if img_url.startswith('images/'):
            filename = img_url.replace('images/', '')
            images_dir = os.path.join(OUTPUT_DIR, 'images')
            if os.path.exists(os.path.join(images_dir, filename)):
                return img_url  # Return as-is since it's already correct path

    # Then check for WordPress images
    for img_url in images:
        if 'wordpress.com' in img_url or 'files.wordpress.com' in img_url:
            filename = os.path.basename(img_url.split('?')[0])
            images_dir = os.path.join(OUTPUT_DIR, 'images')
            if os.path.exists(os.path.join(images_dir, filename)):
                return f"images/{filename}"
    return None


def generate_site():
    """Generate the static site"""
    posts = load_posts()

    if not posts:
        return "Tidak ada post untuk digenerate!"

    # Sort posts by parsed date (newest first) - same logic as dashboard
    def get_date_sort_key(post):
        pub_date = post.get('pub_date', '')
        try:
            dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            return dt.timestamp()
        except:
            return 0

    posts_sorted = sorted(posts, key=get_date_sort_key, reverse=True)

    # Read existing CSS from index.html
    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        existing_html = f.read()

    # Extract CSS
    css_match = re.search(r'<style>(.*?)</style>', existing_html, re.DOTALL)
    css = css_match.group(1) if css_match else ''

    # Build index.html
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

    for post in posts_sorted:
        title = post.get('title', '')

        # Get excerpt
        excerpt = post.get('excerpt', '')
        if not excerpt or len(excerpt) < 10:
            content_clean = clean_wp_content(post.get('content', ''), for_post_page=False)
            p_match = re.search(r'<p>([^<]+)</p>', content_clean)
            if p_match:
                excerpt = p_match.group(1)[:200] + '...'
            else:
                excerpt = content_clean[:200] + '...' if len(content_clean) > 200 else content_clean

        # Clean excerpt from HTML
        excerpt = re.sub(r'<[^>]+>', '', excerpt)

        date_str = format_date(post.get('pub_date', ''))
        category = post.get('categories', ['Umum'])[0] if post.get('categories') else 'Umum'
        slug = post.get('slug', 'post')

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
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Create individual post pages
    for post in posts:
        content = clean_wp_content(post.get('content', ''), for_post_page=True)
        title = post.get('title', '')
        date_str = format_date(post.get('pub_date', ''))
        slug = post.get('slug', 'post')

        categories_html = ''
        if post.get('categories'):
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

        with open(os.path.join(POSTS_DIR, f"{slug}.html"), 'w', encoding='utf-8') as f:
            f.write(post_html)

    return f"Berhasil generate {len(posts)} posts!"


if __name__ == '__main__':
    result = generate_site()
    print(result)
