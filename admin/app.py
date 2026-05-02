"""
Jaya Klampra - Admin CMS
Dashboard sederhana untuk mengelola postingan website
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import html as html_lib
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'jayaklampra-admin-key-2024'

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'posts.json')
EBOOK_FILE = os.path.join(os.path.dirname(__file__), 'data', 'ebook.json')
WP_EXPORT_FILE = r'C:\Users\LENOVO\Downloads\jayaklampra.WordPress.2026-05-01.xml'
IMAGES_DIR = os.path.join(BASE_DIR, 'images')

# Upload config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(IMAGES_DIR, exist_ok=True)

# Load posts from JSON
def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Save posts to JSON
def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# Load ebook data - now returns array of ebooks
def load_ebooks():
    if os.path.exists(EBOOK_FILE):
        with open(EBOOK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Load single ebook by id
def load_ebook_by_id(ebook_id):
    ebooks = load_ebooks()
    return next((e for e in ebooks if e.get('id') == ebook_id), None)

# Save ebooks data (array)
def save_ebooks(ebooks_data):
    with open(EBOOK_FILE, 'w', encoding='utf-8') as f:
        json.dump(ebooks_data, f, ensure_ascii=False, indent=2)

# Generate unique ebook ID
def generate_ebook_id():
    ebooks = load_ebooks()
    if not ebooks:
        return '1'
    max_id = max(int(e.get('id', '0')) for e in ebooks)
    return str(max_id + 1)

# Generate slug from title
def generate_slug(title):
    title_clean = html_lib.unescape(title).lower()
    title_clean = re.sub(r'[^\w\s-]', '', title_clean)
    title_clean = re.sub(r'[\s_]+', '-', title_clean)
    title_clean = title_clean.strip('-')
    title_clean = title_clean.encode('ascii', 'ignore').decode('ascii')
    return title_clean[:100] if title_clean else 'post'

# Format date for display
def format_date_display(date_str):
    try:
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except:
        return date_str

# Format date for storage
def format_date_storage(year, month, day, hour=0, minute=0):
    return f'{["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][datetime(year,month,day).weekday()]}, {day:02d} {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month-1]} {year} {hour:02d}:{minute:02d}:00 +0000'

# Routes
@app.route('/')
def index():
    posts = load_posts()
    ebooks = load_ebooks()
    # Sort by parsed date, not string
    def get_date_sort_key(post):
        pub_date = post.get('pub_date', '')
        try:
            dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            return dt.timestamp()
        except:
            return 0

    posts_sorted = sorted(posts, key=get_date_sort_key, reverse=True)
    return render_template('index.html', posts=posts_sorted, ebooks=ebooks)

@app.route('/new')
def new_post():
    return render_template('edit.html', post=None)

@app.route('/edit/<slug>')
def edit_post(slug):
    posts = load_posts()
    post = next((p for p in posts if p.get('slug') == slug), None)
    if not post:
        flash('Post tidak ditemukan', 'error')
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/save', methods=['POST'])
def save_post():
    posts = load_posts()

    # Get form data
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    excerpt = request.form.get('excerpt', '')
    categories_str = request.form.get('categories', '')
    year = request.form.get('year', '')
    month = request.form.get('month', '')
    day = request.form.get('day', '')
    slug = request.form.get('slug', '')
    original_slug = request.form.get('original_slug', '')

    # Generate slug if empty
    if not slug:
        slug = generate_slug(title)

    # Parse categories
    categories = [c.strip() for c in categories_str.split(',') if c.strip()]

    # Format date - use current date if not provided
    if year and month and day:
        try:
            pub_date = format_date_storage(int(year), int(month), int(day))
        except:
            pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    else:
        # Use current date/time
        now = datetime.now()
        pub_date = now.strftime('%a, %d %b %Y %H:%M:%S +0000')

    # Build post data
    post_data = {
        'title': title,
        'content': content,
        'excerpt': excerpt,
        'pub_date': pub_date,
        'slug': slug,
        'categories': categories,
        'id': datetime.now().strftime('%Y%m%d%H%M%S')
    }

    # Update or add post
    if original_slug and original_slug != slug:
        # Remove old slug if changed
        posts = [p for p in posts if p.get('slug') != original_slug]

    # Check if slug exists
    existing_idx = next((i for i, p in enumerate(posts) if p.get('slug') == slug), None)
    if existing_idx is not None:
        posts[existing_idx] = post_data
    else:
        posts.append(post_data)

    save_posts(posts)
    flash('Post berhasil disimpan!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<slug>')
def delete_post(slug):
    posts = load_posts()
    posts = [p for p in posts if p.get('slug') != slug]
    save_posts(posts)
    flash('Post berhasil dihapus', 'success')
    return redirect(url_for('index'))

@app.route('/preview/<slug>')
def preview_post(slug):
    posts = load_posts()
    post = next((p for p in posts if p.get('slug') == slug), None)
    if not post:
        return 'Post tidak ditemukan', 404
    return render_template('preview.html', post=post)

@app.route('/generate')
def generate():
    """Generate static HTML files from admin data"""
    try:
        from generate import generate_site
        result = generate_site()
        flash(result, 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'})

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'error': 'File too large. Max 5MB'})

    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"

    # Save file
    filepath = os.path.join(IMAGES_DIR, unique_filename)
    file.save(filepath)

    return jsonify({'success': True, 'filename': unique_filename})

@app.route('/import-wp')
def import_wp():
    """Import posts from WordPress export"""
    try:
        if not os.path.exists(WP_EXPORT_FILE):
            flash('File export WordPress tidak ditemukan!', 'error')
            return redirect(url_for('index'))

        tree = ET.parse(WP_EXPORT_FILE)
        root = tree.getroot()

        ns = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
            'wp': 'http://wordpress.org/export/1.2/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        posts = []
        for item in root.findall('.//item'):
            post_type = item.find('wp:post_type', ns)
            status = item.find('wp:status', ns)

            if post_type is None or post_type.text != 'post':
                continue
            if status is None or status.text != 'publish':
                continue

            title_elem = item.find('title')
            title = title_elem.text if title_elem.text else ''

            pub_date_elem = item.find('pubDate')
            pub_date = pub_date_elem.text if pub_date_elem.text else ''

            content_elem = item.find('content:encoded', ns)
            content = content_elem.text if content_elem.text else ''

            excerpt_elem = item.find('excerpt:encoded', ns)
            excerpt = excerpt_elem.text if excerpt_elem.text else ''

            post_name_elem = item.find('wp:post_name', ns)
            slug = post_name_elem.text if post_name_elem is not None and post_name_elem.text else ''

            if not slug or slug.isdigit():
                slug = generate_slug(title)

            categories = []
            for cat in item.findall('category'):
                cat_text = cat.text
                if cat_text and cat_text not in ['Uncategorized', 'Tidak Dikategorikan']:
                    categories.append(cat_text)

            posts.append({
                'title': html_lib.unescape(title),
                'content': content,
                'excerpt': excerpt,
                'pub_date': pub_date,
                'slug': slug,
                'categories': categories,
                'id': ''
            })

        save_posts(posts)
        flash(f'Berhasil import {len(posts)} posts dari WordPress!', 'success')
    except Exception as e:
        flash(f'Error importing: {str(e)}', 'error')

    return redirect(url_for('index'))

# ========== E-BOOKS MANAGEMENT ==========
@app.route('/ebook')
def ebook_list():
    """E-Books list page"""
    ebooks = load_ebooks()
    return render_template('ebooks.html', ebooks=ebooks)

@app.route('/ebook/new')
def ebook_new():
    """Create new e-book page"""
    return render_template('ebook_form.html', ebook=None)

@app.route('/ebook/edit/<id>')
def ebook_edit(id):
    """Edit e-book page"""
    ebook = load_ebook_by_id(id)
    if not ebook:
        flash('E-Book tidak ditemukan', 'error')
        return redirect(url_for('ebook_list'))
    return render_template('ebook_form.html', ebook=ebook)

@app.route('/ebook/save', methods=['POST'])
def ebook_save():
    """Save e-book (create or update)"""
    ebooks = load_ebooks()

    # Get form data
    ebook_id = request.form.get('id', '')
    title = request.form.get('title', '')
    subtitle = request.form.get('subtitle', '')
    description = request.form.get('description', '')
    cover_image = request.form.get('cover_image_filename', '')
    price = request.form.get('price', '')
    price_original = request.form.get('price_original', '')
    bank_name = request.form.get('bank_name', '')
    bank_number = request.form.get('bank_number', '')
    bank_owner = request.form.get('bank_owner', '')
    whatsapp = request.form.get('whatsapp', '')

    # Get features as list
    features_raw = request.form.get('features', '')
    features = [f.strip() for f in features_raw.split('\n') if f.strip()]

    # Build ebook data
    ebook_data = {
        'id': ebook_id if ebook_id else generate_ebook_id(),
        'title': title,
        'subtitle': subtitle,
        'description': description,
        'cover_image': cover_image,
        'price': price,
        'price_original': price_original,
        'features': features,
        'bank_name': bank_name,
        'bank_number': bank_number,
        'bank_owner': bank_owner,
        'whatsapp': whatsapp
    }

    # Update or add ebook
    if ebook_id:
        # Update existing
        existing_idx = next((i for i, e in enumerate(ebooks) if e.get('id') == ebook_id), None)
        if existing_idx is not None:
            ebooks[existing_idx] = ebook_data
    else:
        # Add new
        ebooks.append(ebook_data)

    save_ebooks(ebooks)

    # Also update e-buku.html with new data
    update_ebook_html_all()

    flash('E-Book berhasil disimpan!', 'success')
    return redirect(url_for('ebook_list'))

@app.route('/ebook/delete/<id>')
def ebook_delete(id):
    """Delete e-book"""
    ebooks = load_ebooks()
    ebooks = [e for e in ebooks if e.get('id') != id]
    save_ebooks(ebooks)

    # Also update e-buku.html
    update_ebook_html_all()

    flash('E-Book berhasil dihapus', 'success')
    return redirect(url_for('ebook_list'))

def update_ebook_html_all():
    """Update e-buku.html with all ebooks data - generates dynamic HTML"""
    from pathlib import Path

    ebook_page = os.path.join(BASE_DIR, 'pages', 'e-buku.html')
    ebooks = load_ebooks()

    if not os.path.exists(ebook_page):
        return

    # Read the base template (we need to preserve the structure)
    with open(ebook_page, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate ebook cards HTML
    ebook_cards_html = ''
    for ebook in ebooks:
        price_formatted = f"{int(ebook['price']):,}".replace(',', '.')
        price_original_formatted = f"{int(ebook['price_original']):,}".replace(',', '.')

        features_html = ''
        if ebook.get('features'):
            for feature in ebook['features']:
                features_html += f'<li>{feature}</li>'

        whatsapp_msg = f'Halo,%20saya%20ingin%20membeli%20E-Book%20%22{ebook["title"].replace(" ", "%20")}%22%20seharga%20Rp%20{price_formatted.replace(".", "")}'
        whatsapp_link = f'https://wa.me/{ebook["whatsapp"]}?text={whatsapp_msg}'

        # Cover image or book mockup
        cover_html = ''
        if ebook.get('cover_image'):
            cover_html = f'<img src="images/{ebook["cover_image"]}" alt="{ebook["title"]}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;">'
        else:
            cover_html = '<div class="book-mockup"></div>'

        ebook_cards_html += f'''
                <div class="ebook-card">
                    <div class="ebook-cover">
                        {cover_html}
                    </div>
                    <div class="ebook-info">
                        <span class="ebook-tag">E-Book</span>
                        <h2 class="ebook-title">{ebook["title"]}</h2>
                        <p class="ebook-subtitle">{ebook["subtitle"]}</p>

                        <p class="ebook-description">
                            {ebook["description"]}
                        </p>

                        <ul class="ebook-features">
                            {features_html}
                        </ul>

                        <div class="price-section">
                            <div class="price-row">
                                <div class="price">
                                    <span class="price-label">Harga</span>
                                    <span class="price-value">Rp {price_formatted}</span>
                                    <span class="price-original">Rp {price_original_formatted}</span>
                                </div>
                                <a href="#payment-instructions" class="buy-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                                    </svg>
                                    Beli Sekarang
                                </a>
                            </div>

                            <div class="payment-methods">
                                <p class="payment-label">Metode Pembayaran:</p>
                                <div class="payment-icons">
                                    <span class="payment-icon">{ebook["bank_name"]} Transfer</span>
                                    <span class="payment-icon">WhatsApp</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>'''

    # If no ebooks, add placeholder
    if not ebooks:
        ebook_cards_html = '''
                <div class="ebook-card" style="opacity: 0.6; border-style: dashed;">
                    <div class="ebook-cover" style="background: var(--bg-secondary);">
                        <div style="font-size: 3rem; color: var(--text-secondary);"></div>
                    </div>
                    <div class="ebook-info">
                        <span class="ebook-tag" style="background: var(--bg-secondary); color: var(--text-secondary);">Coming Soon</span>
                        <h2 class="ebook-title">E-Book Lainnya</h2>
                        <p class="ebook-subtitle">Sedang dalam penulisan...</p>
                        <p class="ebook-description">
                            Koleksi e-book lain tentang kesadaran, spiritualitas, dan filsafat kehidupan
                            sedang disusun. Nantikan update terbaru.
                        </p>
                    </div>
                </div>'''

    # Replace ebook-grid content
    pattern = r'(<div class="ebook-grid">)(.*?)(</div>)'
    content = re.sub(pattern, r'\1\n' + ebook_cards_html + '\n                \3', content, flags=re.DOTALL)

    # Update payment instructions with first ebook's info (or last modified)
    if ebooks:
        ebook = ebooks[-1]  # Use the most recently added/edited ebook
        price_formatted = f"{int(ebook['price']):,}".replace(',', '.')

        # Update price in payment section
        content = re.sub(
            r'Transfer Rp ([\d\.]+) ke',
            f'Transfer Rp {price_formatted} ke',
            content
        )

        # Update bank info
        content = re.sub(
            r'<div class="bank-logo">[^<]*</div>',
            f'<div class="bank-logo">{ebook["bank_name"]}</div>',
            content
        )
        content = re.sub(
            r'<p class="bank-number">[^<]*</p>',
            f'<p class="bank-number">{ebook["bank_number"]}</p>',
            content
        )
        content = re.sub(
            r'<p class="bank-name">[^<]*</p>',
            f'<p class="bank-name">a.n. {ebook["bank_owner"]}</p>',
            content
        )

        # Update WhatsApp links
        whatsapp_msg = f'Halo,%20saya%20ingin%20membeli%20E-Book%20%22{ebook["title"].replace(" ", "%20")}%22%20seharga%20Rp%20{price_formatted.replace(".", "")}'
        whatsapp_link = f'href="https://wa.me/{ebook["whatsapp"]}?text={whatsapp_msg}"'

        # Update WhatsApp links in various places
        content = re.sub(
            r'href="https://wa\.me/[^"]*"',
            whatsapp_link,
            content
        )

        # Update format text with current ebook title
        content = re.sub(
            r'untuk E-Book "[^"]*"',
            f'untuk E-Book "{ebook["title"]}"',
            content
        )

        # Update CTA price
        content = re.sub(
            r'Beli Sekarang - Rp [\d\.]+',
            f'Beli Sekarang - Rp {price_formatted}',
            content
        )

    with open(ebook_page, 'w', encoding='utf-8') as f:
        f.write(content)

# Template filters
@app.template_filter('date_display')
def date_display_filter(date_str):
    return format_date_display(date_str)

@app.template_filter('formatPrice')
def format_price_filter(price):
    """Format price with dot separators"""
    try:
        return f"{int(price):,}".replace(',', '.')
    except:
        return str(price)

if __name__ == '__main__':
    # Initial import if data file doesn't exist
    if not os.path.exists(DATA_FILE) and os.path.exists(WP_EXPORT_FILE):
        print('Mengimport posts dari WordPress export...')
        try:
            with app.test_request_context():
                import_wp()
        except:
            pass

    app.run(debug=True, port=5000)
