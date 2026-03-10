import json
import os
import requests
import urllib.parse
from urllib.parse import unquote

def sanitize_filename(name):
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()

def download_pdfs():
    with open('vestibulares.json', 'r', encoding='utf-8') as f:
        editions = json.load(f)

    base_dir = "pdfs"
    os.makedirs(base_dir, exist_ok=True)

    total_downloaded = 0
    total_skipped = 0

    for ed in editions:
        ed_name = sanitize_filename(ed['name'].replace('/', '-'))
        ed_dir = os.path.join(base_dir, ed_name)
        os.makedirs(ed_dir, exist_ok=True)

        for link in ed['approved_links']:
            url = link['url']

            # Check if it's a file
            if '.pdf' in url.lower() or '@@download' in url.lower() or '@@display-file' in url.lower():
                try:
                    # Guess filename from URL or title
                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.split('/')

                    filename = None
                    # Try to find something ending in .pdf
                    for part in reversed(path_parts):
                        if part.lower().endswith('.pdf'):
                            filename = unquote(part)
                            break

                    if not filename:
                        # Fallback to title
                        filename = sanitize_filename(link['title']) + '.pdf'

                    filepath = os.path.join(ed_dir, filename)

                    if os.path.exists(filepath):
                        print(f"Skipping {filename} (already exists)")
                        total_skipped += 1
                        continue

                    print(f"Downloading {filename}...")
                    res = requests.get(url, stream=True)
                    if res.status_code == 200:
                        with open(filepath, 'wb') as pdf_file:
                            for chunk in res.iter_content(chunk_size=8192):
                                pdf_file.write(chunk)
                        total_downloaded += 1
                    else:
                        print(f"Failed to download {url} - Status code: {res.status_code}")
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
            else:
                # It's an HTML page or campus page (like vestibular current editions), skip downloading
                pass

    print(f"Finished! Downloaded {total_downloaded} files, skipped {total_skipped}.")

if __name__ == "__main__":
    download_pdfs()
