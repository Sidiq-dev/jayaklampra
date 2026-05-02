import json
import re
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = BASE_DIR

def get_featured_image(post):
    images = re.findall(r'<img[^>]+src="([^"]+)"', post.get('content', ''))
    for img_url in images:
        if 'wordpress.com' in img_url or 'files.wordpress.com' in img_url:
            filename = os.path.basename(img_url.split('?')[0])
            images_dir = os.path.join(OUTPUT_DIR, 'images')
            if os.path.exists(os.path.join(images_dir, filename)):
                return f"images/{filename}"
    return None

# Load posts
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'posts.json')
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    posts = json.load(f)

# Check posts with WordPress images
print("=== Checking featured images ===")
count = 0
for p in posts[:15]:
    result = get_featured_image(p)
    title = p.get('title', '')[:40]
    if result:
        count += 1
        print(f"OK {title}")
        print(f"   {result}")
    else:
        # Check if post has any images at all
        images = re.findall(r'<img[^>]+src="([^"]+)"', p.get('content', ''))
        if images:
            print(f"NO {title}")
            print(f"   Has images but no match")
        else:
            print(f"-- {title}")
            print(f"   No images")

print(f"\nTotal with featured images: {count}")
print(f"Total posts checked: {min(15, len(posts))}")
