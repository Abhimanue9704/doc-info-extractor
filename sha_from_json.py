import os
import json
import hashlib
import string

sources_file = "sources.json"
pdf_folder = "downloads"
output_file = "sha_sources.json"

def normalize_title(s: str) -> str:
    """
    Normalize a title or filename to allow matching between PDF filenames
    and sources.json titles.
    """
    if s is None:
        return ""
    s = str(s).lower().strip()
    for ch in ["/", "_", ":", "?", "–", "-", "’", "'", "“", "”"]:
        s = s.replace(ch, "")
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = " ".join(s.split())
    return s

with open(sources_file, "r", encoding="utf-8") as f:
    sources = json.load(f)

title_url_map = {}
for item in sources:
    norm_title = normalize_title(item.get("title", ""))
    title_url_map[norm_title] = item.get("url", "")

sha_dict = {}

for filename in os.listdir(pdf_folder):
    if not filename.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(pdf_folder, filename)
    pdf_title = os.path.splitext(filename)[0]
    pdf_title_norm = normalize_title(pdf_title)

    url = title_url_map.get(pdf_title_norm, "")

    matched_title = ""
    for item in sources:
        if normalize_title(item.get("title", "")) == pdf_title_norm:
            matched_title = item.get("title", "")
            break
    print(f"[COMPARE] PDF: {pdf_title}  |  Source Title: {matched_title}")

    try:
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

      
        sha = hashlib.sha256(file_bytes).hexdigest()

       
        sha_dict[sha] = {"title": pdf_title, "url": url}

        if url:
            print(f"Processed: {pdf_title} | SHA: {sha[:10]}... | matched URL")
        else:
            print(f"Processed: {pdf_title} | SHA: {sha[:10]}... | NO URL match (normalized: '{pdf_title_norm}')")

    except Exception as e:
        print(f"Failed to process {filename} | Error: {e}")


with open(output_file, "w", encoding="utf-8") as f:
    json.dump(sha_dict, f, indent=2, ensure_ascii=False)

print(f"Done! SHA mapping saved to {output_file}")
