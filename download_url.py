import requests
import json
import os
import re
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse
import time

json_file = "sources.json"

with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

output_folder = "downloads"
os.makedirs(output_folder, exist_ok=True)

USER_AGENTS = [
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_headers(user_agent_index=0):
    """Get headers with rotating user agents"""
    return {
        "User-Agent": USER_AGENTS[user_agent_index % len(USER_AGENTS)],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

def sanitize_filename(filename):
    """Sanitize filename for cross-platform compatibility"""
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filename = re.sub(r'_+', "_", filename)
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip("_")

def is_pdf(filepath):
    """Check if file is a valid PDF by examining magic bytes and structure"""
    try:
        if not os.path.exists(filepath):
            return False
            
        with open(filepath, "rb") as f:
            header = f.read(8)
            if not header.startswith(b"%PDF-"):
                return False
            
            f.seek(0, 2)  
            file_size = f.tell()
            
            if file_size < 100:  
                return False
                
            f.seek(max(0, file_size - 1024))  
            trailer_content = f.read()
            if b"%%EOF" not in trailer_content and file_size > 1000:
                return False
                
        return True
    except Exception as e:
        print(f"Error checking PDF validity: {e}")
        return False

def extract_pdf_links_from_html(html_content, base_url):
    """Extract PDF links from HTML content"""
    pdf_links = []
    
    pdf_patterns = [
        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
        r'href=["\']([^"\']*)["\'](?=[^>]*>.*?pdf)',  
        r'src=["\']([^"\']*\.pdf[^"\']*)["\']', 
        r'data-url=["\']([^"\']*\.pdf[^"\']*)["\']',  
        r'window\.open\(["\']([^"\']*\.pdf[^"\']*)["\']',  
        r'location\.href\s*=\s*["\']([^"\']*\.pdf[^"\']*)["\']',  
        r'href=["\']([^"\']*Download\.aspx[^"\']*)["\']',
        r'href=["\']([^"\']*DocumentID[^"\']*)["\']',
        r'action=["\']([^"\']*Download\.aspx[^"\']*)["\']'
    ]
    
    for pattern in pdf_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            full_url = urljoin(base_url, match)
            if full_url not in pdf_links:
                pdf_links.append(full_url)
    
    return pdf_links

def try_alternative_download(url, filename, title):
    """Alternative download method for stubborn sites with resume capability"""
    try:
        print("Trying urllib method with resume capability...")
        
        resume_pos = 0
        if os.path.exists(filename):
            resume_pos = os.path.getsize(filename)
            print(f"Found partial file, resuming from {resume_pos:,} bytes")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', USER_AGENTS[2])  
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Accept-Encoding', 'gzip, deflate')
        req.add_header('Connection', 'keep-alive')
        
        if resume_pos > 0:
            req.add_header('Range', f'bytes={resume_pos}-')
        
        try:
            with urllib.request.urlopen(req, timeout=300) as response: 
                file_mode = 'ab' if resume_pos > 0 else 'wb'
                
                with open(filename, file_mode) as f:
                    downloaded = resume_pos
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if downloaded % (1024*1024) == 0: 
                            print(f"Downloaded: {downloaded:,} bytes")
            
            if is_pdf(filename):
                print(f"✓ Downloaded via urllib: {title}")
                return True
            else:
                os.remove(filename)
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 416:  
                print("Server doesn't support resume, trying fresh download...")
                if os.path.exists(filename):
                    os.remove(filename)
                req = urllib.request.Request(url)
                req.add_header('User-Agent', USER_AGENTS[2])
                
                with urllib.request.urlopen(req, timeout=300) as response:
                    with open(filename, 'wb') as f:
                        downloaded = 0
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if downloaded % (1024*1024) == 0:
                                print(f"Downloaded: {downloaded:,} bytes")
                
                if is_pdf(filename):
                    print(f"✓ Downloaded via urllib (fresh): {title}")
                    return True
                else:
                    os.remove(filename)
                    return False
            else:
                raise
                
    except Exception as e:
        print(f"Alternative method also failed: {e}")
        return False

def download_file(url, filepath, max_retries=5):
    """Download file with retry logic, resume capability, and robust error handling"""
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            current_headers = get_headers(attempt)
            
            resume_pos = 0
            if os.path.exists(filepath) and attempt > 0:
                resume_pos = os.path.getsize(filepath)
                current_headers['Range'] = f'bytes={resume_pos}-'
                print(f"Resuming download from byte {resume_pos}")
            
            if attempt == 0 and any(domain in url for domain in ['osha.gov', 'gov', 'edu']):
                try:
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    session.get(base_url, headers=current_headers, timeout=30)
                    time.sleep(2) 
                except:
                    pass 
            
            timeout = min(120 + (attempt * 30), 300)  
            print(f"Attempt {attempt + 1}/{max_retries} - Timeout: {timeout}s")
            
            response = session.get(
                url, 
                headers=current_headers, 
                allow_redirects=True, 
                timeout=timeout,
                stream=True
            )
            response.raise_for_status()
            
            content_length = response.headers.get('Content-Length')
            expected_size = int(content_length) if content_length else None
            
            if expected_size:
                print(f"Expected file size: {expected_size:,} bytes ({expected_size/1024/1024:.1f} MB)")
            
            file_mode = 'ab' if resume_pos > 0 else 'wb'
            
            with open(filepath, file_mode) as f:
                downloaded = resume_pos
                chunk_size = 8192
                last_progress = 0
                stall_count = 0
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if expected_size and downloaded - last_progress > 1024*1024:
                            progress = (downloaded / expected_size) * 100
                            print(f"Progress: {progress:.1f}% ({downloaded:,}/{expected_size:,} bytes)")
                            last_progress = downloaded
                            stall_count = 0
                        elif not expected_size and downloaded - last_progress > 1024*1024:
                            print(f"Downloaded: {downloaded:,} bytes")
                            last_progress = downloaded
                            stall_count = 0
                        
                        stall_count += 1
                        
                        if stall_count > 10000:
                            print("Download appears stalled, will retry...")
                            break
            
            actual_size = os.path.getsize(filepath)
            
            if expected_size and actual_size < expected_size:
                print(f"Incomplete download: {actual_size:,}/{expected_size:,} bytes")
                if attempt < max_retries - 1:
                    print("Will retry with resume...")
                    time.sleep(3 + attempt * 2)
                    continue
            
            print(f"Download completed: {actual_size:,} bytes")
            return True, response.headers.get("Content-Type", "")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"403 Forbidden on attempt {attempt + 1}/{max_retries} - trying different approach...")
                if attempt < max_retries - 1:
                    time.sleep(5 + attempt * 2) 
                    continue
            elif e.response.status_code == 416: 
                print("Server doesn't support resume, starting fresh...")
                if os.path.exists(filepath):
                    os.remove(filepath)
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
            else:
                print(f"HTTP error {e.response.status_code} on attempt {attempt + 1}/{max_retries}")
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError, 
                requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
            print(f"Connection/timeout error on attempt {attempt + 1}/{max_retries}: {type(e).__name__}")
            if attempt < max_retries - 1:
                wait_time = min(10 + (attempt * 5), 60) 
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 + attempt * 2)
                continue
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            break
    
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        if file_size == 0 or not is_pdf(filepath):
            os.remove(filepath)
            print("Removed incomplete/invalid file")
    
    return False, ""

def try_aspx_alternatives(url, filename, title):
    """Try alternative methods for ASPX pages that might serve PDFs"""
    print("Trying ASPX-specific approaches...")
    
    try:
        session = requests.Session()
        headers = get_headers(1)  
        
        headers['Referer'] = url
        
        alternative_urls = [
            url,
            url + "&ForceDownload=true",
            url + "&download=1",
            url + "&format=pdf",
            url.replace('Download.aspx', 'DownloadDirect.aspx') if 'Download.aspx' in url else url
        ]
        
        for alt_url in alternative_urls:
            try:
                print(f"Trying alternative URL: {alt_url}")
                response = session.get(alt_url, headers=headers, allow_redirects=True, timeout=60, stream=True)
                
                final_url = response.url
                if final_url.lower().endswith('.pdf') or 'pdf' in response.headers.get('Content-Type', '').lower():
                    with open(filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    if is_pdf(filename):
                        print(f"✓ Downloaded via ASPX alternative: {title}")
                        return True
                    else:
                        os.remove(filename)
                
                content_disp = response.headers.get('Content-Disposition', '')
                if 'pdf' in content_disp.lower() or '.pdf' in content_disp:
                    with open(filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    if is_pdf(filename):
                        print(f"✓ Downloaded via Content-Disposition: {title}")
                        return True
                    else:
                        os.remove(filename)
                        
            except Exception as e:
                print(f"Alternative URL failed: {e}")
                continue
        
        try:
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                pdf_links = extract_pdf_links_from_html(response.text, url)
                
                js_pdf_patterns = [
                    r"window\.open\(['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                    r"location\.href\s*=\s*['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                    r"src=['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                    r"data-url=['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                    r"href=['\"]([^'\"]*DocumentID[^'\"]*)['\"]"
                ]
                
                for pattern in js_pdf_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    for match in matches:
                        full_url = urljoin(url, match)
                        if full_url not in pdf_links:
                            pdf_links.append(full_url)
                
                if pdf_links:
                    print(f"Found {len(pdf_links)} potential PDF links in ASPX page")
                    for pdf_url in pdf_links[:5]:  
                        print(f"Trying: {pdf_url}")
                        success, _ = download_file(pdf_url, filename)
                        
                        if success and is_pdf(filename):
                            print(f"✓ Downloaded from ASPX embedded link: {title}")
                            return True
                        elif os.path.exists(filename):
                            os.remove(filename)
        
        except Exception as e:
            print(f"ASPX page parsing failed: {e}")
        
        print(f"All ASPX alternatives failed for: {title}")
        return False
        
    except Exception as e:
        print(f"ASPX alternative method error: {e}")
        return False

def process_url(title, url):
    """Process a single URL and attempt to download PDF"""
    print(f"\nProcessing: {title}")
    print(f"URL: {url}")
    
    filename = os.path.join(output_folder, f"{sanitize_filename(title)}.pdf")
    
    if os.path.exists(filename) and is_pdf(filename):
        print(f"Already exists (valid PDF): {title}")
        return True
    
    try:
        session = requests.Session()
        initial_headers = get_headers(0)
        
        try:
            head_response = session.head(url, headers=initial_headers, allow_redirects=True, timeout=30)
            content_type = head_response.headers.get("Content-Type", "").lower()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("HEAD request forbidden, trying GET request instead...")
                try:
                    get_response = session.get(url, headers=initial_headers, allow_redirects=True, timeout=30, stream=True)
                    content_type = get_response.headers.get("Content-Type", "").lower()
                    if "pdf" in content_type:
                        with open(filename, "wb") as f:
                            for chunk in get_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        if is_pdf(filename):
                            print(f"✓ Downloaded (via initial GET): {title}")
                            return True
                        else:
                            os.remove(filename)
                except:
                    content_type = "unknown"
            else:
                content_type = "unknown"
        
        print(f"Content-Type: {content_type}")
        
        if "pdf" in content_type or url.lower().endswith(".pdf"):
            print("Attempting direct PDF download...")
            success, actual_content_type = download_file(url, filename)
            
            if success and is_pdf(filename):
                print(f"✓ Downloaded: {title}")
                return True
            else:
                print(f"✗ Invalid PDF downloaded: {title}")
                if os.path.exists(filename):
                    os.remove(filename)
                
                if any(domain in url for domain in ['osha.gov', 'gov']):
                    print("Trying alternative download method...")
                    alt_success = try_alternative_download(url, filename, title)
                    if alt_success:
                        return True
                
                return False
        
        elif url.lower().endswith(('.aspx', '.asp', '.jsp', '.php')) or 'download' in url.lower():
            print("Dynamic page detected (ASPX/ASP/JSP/PHP), attempting PDF download...")
            success, actual_content_type = download_file(url, filename)
            
            if success and is_pdf(filename):
                print(f"✓ Downloaded from dynamic page: {title}")
                return True
            elif success:
                try:
                    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)
                        if '<html' in content.lower() or '<!doctype html' in content.lower():
                            print("Got HTML response, searching for PDF links...")
                            pdf_links = extract_pdf_links_from_html(content, url)
                            
                            if pdf_links:
                                print(f"Found {len(pdf_links)} potential PDF link(s) in dynamic page response")
                                
                                for i, pdf_url in enumerate(pdf_links[:3]):
                                    print(f"Trying PDF link {i+1}: {pdf_url}")
                                    
                                    success2, _ = download_file(pdf_url, filename)
                                    
                                    if success2 and is_pdf(filename):
                                        print(f"✓ Downloaded PDF from dynamic page link: {title}")
                                        return True
                                    elif os.path.exists(filename):
                                        pass
                            
                            print("No valid PDF links found in dynamic page response")
                except:
                    pass
                    
                print(f"✗ Dynamic page didn't return PDF: {title}")
                if os.path.exists(filename):
                    os.remove(filename)
                
                if url.lower().endswith('.aspx'):
                    return try_aspx_alternatives(url, filename, title)
                
                return False
            else:
                print(f"✗ Failed to download from dynamic page: {title}")
                return False
        
        elif "text/html" in content_type:
            print("HTML page detected, searching for PDF links...")
            
            try:
                html_response = session.get(url, headers=initial_headers, timeout=30)
                html_response.raise_for_status()
                
                pdf_links = extract_pdf_links_from_html(html_response.text, url)
                
                if pdf_links:
                    print(f"Found {len(pdf_links)} potential PDF link(s)")
                    
                    for i, pdf_url in enumerate(pdf_links[:3]):
                        print(f"Trying PDF link {i+1}: {pdf_url}")
                        
                        success, _ = download_file(pdf_url, filename)
                        
                        if success and is_pdf(filename):
                            print(f"✓ Downloaded from embedded link: {title}")
                            return True
                        elif os.path.exists(filename):
                            os.remove(filename)
                
                print(f"✗ No valid PDF found in HTML: {title}")
                return False
                
            except Exception as e:
                print(f"Error processing HTML: {e}")
                return False
        
        else:
            print("Unknown content type, attempting download anyway...")
            success, actual_content_type = download_file(url, filename)
            
            if success and is_pdf(filename):
                print(f"✓ Downloaded (content-type was wrong): {title}")
                return True
            else:
                print(f"✗ Not a PDF file: {title}")
                if os.path.exists(filename):
                    os.remove(filename)
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {title} | Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {title} | Error: {e}")
        return False

successful_downloads = 0
failed_downloads = 0

print(f"Starting download of {len(data)} items...")
print(f"Output folder: {output_folder}")
print("=" * 50)

for i, item in enumerate(data, 1):
    title = item.get("title", f"untitled_{i}")
    url = item.get("url")
    
    if not url:
        print(f"✗ Skipped (no URL): {title}")
        failed_downloads += 1
        continue
    
    print(f"\n[{i}/{len(data)}] ", end="")
    
    success = process_url(title, url)
    if success:
        successful_downloads += 1
    else:
        failed_downloads += 1
    
    if any(domain in url for domain in ['osha.gov', 'gov', 'edu']):
        time.sleep(5)
    elif not success:
        time.sleep(3)
    else:
        time.sleep(2)

print("\n" + "=" * 50)
print(f"Download Summary:")
print(f"✓ Successful: {successful_downloads}")
print(f"✗ Failed: {failed_downloads}")
print(f"📁 Files saved to: {output_folder}")

if failed_downloads > 0:
    print(f"\nNote: {failed_downloads} downloads failed. This could be due to:")
    print("- URLs pointing to HTML pages without PDF links")
    print("- Access restrictions or authentication required")
    print("- Network timeouts or server errors")
    print("- Invalid or broken URLs")