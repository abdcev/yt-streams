#!/usr/bin/env python3
"""
YouTube Stream Updater - Final Full Version
Fetches YouTube stream URLs, handles concurrency/delays, and saves to category folders.
Zero skipped lines. Ready to run.
"""

import json
import os
import sys
import argparse
import time
import re
import random
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs
import concurrent.futures

# --- IMPORT: Cloudscraper and Curl_cffi checks ---
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests

# --- CONFIGURATION ---
ENDPOINT = os.environ.get('ENDPOINT', 'https://your-endpoint.com')
FOLDER_NAME = os.environ.get('FOLDER_NAME', 'streams')
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
VERBOSE = False
MAX_CONCURRENCY = 10  # Eş zamanlı işlem limiti

# --- SESSION CREATION ---
def create_session():
    """Create the best available HTTP session"""
    if CLOUDSCRAPER_AVAILABLE:
        print("✓ Using enhanced cloudscraper for JavaScript challenge bypass")
        try:
            scraper = cloudscraper.create_scraper(
                browser='chrome',
                debug=False,
                enable_tls_fingerprinting=True,
                enable_tls_rotation=True,
                enable_anti_detection=True,
                enable_enhanced_spoofing=True,
                spoofing_consistency_level='medium',
                enable_intelligent_challenges=True,
                enable_adaptive_timing=True,
                behavior_profile='focused',
                enable_ml_optimization=True,
                enable_enhanced_error_handling=True,
                enable_stealth=True,
                stealth_options={
                    'min_delay': 1.5,
                    'max_delay': 4.0,
                    'human_like_delays': True,
                    'randomize_headers': True,
                    'browser_quirks': True,
                    'simulate_viewport': True,
                    'behavioral_patterns': True
                },
                session_refresh_interval=3600,
                auto_refresh_on_403=True,
                max_403_retries=3
            )
            print("  → Enhanced features enabled: TLS fingerprinting, anti-detection")
            return scraper, 'cloudscraper-enhanced'
        except TypeError:
            print("  → Using basic cloudscraper (enhanced fork not detected)")
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
                delay=10
            )
            return scraper, 'cloudscraper-basic'
    elif CURL_CFFI_AVAILABLE:
        print("✓ Using curl_cffi for advanced challenge bypass")
        return None, 'curl_cffi'
    else:
        print("⚠ Using basic requests (limited challenge support)")
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session, 'requests'

# Initialize session globally
session, session_type = create_session()


# --- HELPER FUNCTIONS ---

def load_config(config_path):
    """Load configuration from JSON file and get category name."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Dosya isminden kategori ismini (uzantısız) al. Örn: turkish.json -> turkish
        filename_stem = Path(config_path).stem
        
        print(f"✓ Loaded {len(config)} stream(s) from config: {config_path}")
        return config, filename_stem
    except FileNotFoundError:
        print(f"✗ Config file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in config file: {e}")
        sys.exit(1)


def extract_redirect_url(html_content):
    """Extract redirect URL from JavaScript challenge page"""
    patterns = [
        r'location\.href\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
        r'location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^;]+;\s*url=([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_challenge_cookies(html_content):
    """Extract cookies set by JavaScript challenge"""
    cookies = {}
    cookie_patterns = [
        r'document\.cookie\s*=\s*["\']([^"\']+)["\']',
        r'document\.cookie\s*=\s*([^;]+);',
    ]
    
    for pattern in cookie_patterns:
        matches = re.finditer(pattern, html_content)
        for match in matches:
            cookie_str = match.group(1)
            if '=' in cookie_str:
                parts = cookie_str.split('=', 1)
                if len(parts) == 2:
                    cookies[parts[0].strip()] = parts[1].strip()
    return cookies


def solve_js_challenge_advanced(response, slug, base_url):
    """Detect and solve JavaScript challenge with multiple strategies"""
    content = response.text
    
    challenge_indicators = [
        '<script type="text/javascript" src="/aes.js"',
        'slowAES.decrypt',
        'Checking your browser',
        'Just a moment',
        'Please wait',
        'Verifying you are human'
    ]
    
    is_challenge = any(indicator in content for indicator in challenge_indicators)
    
    if is_challenge:
        print(f"  ⚠ JavaScript/Anti-bot challenge detected")
        
        # Strategy 1: Extract redirect URL
        redirect_url = extract_redirect_url(content)
        if redirect_url:
            print(f"  → Strategy 1: Found redirect URL")
            if redirect_url.startswith('/'):
                parsed = urlparse(base_url)
                redirect_url = f"{parsed.scheme}://{parsed.netloc}{redirect_url}"
            elif not redirect_url.startswith('http'):
                redirect_url = f"{base_url.rstrip('/')}/{redirect_url}"
            
            return {
                'type': 'redirect',
                'url': redirect_url,
                'cookies': extract_challenge_cookies(content)
            }
        
        # Strategy 2: Extract cookies
        cookies = extract_challenge_cookies(content)
        if cookies:
            print(f"  → Strategy 2: Found {len(cookies)} challenge cookie(s)")
            return {
                'type': 'cookies',
                'url': base_url,
                'cookies': cookies
            }
        
        # Strategy 3: Hidden form
        form_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if form_match:
            form_action = form_match.group(1)
            if form_action.startswith('/'):
                parsed = urlparse(base_url)
                form_action = f"{parsed.scheme}://{parsed.netloc}{form_action}"
            print(f"  → Strategy 3: Found form action")
            return {
                'type': 'form',
                'url': form_action,
                'cookies': {}
            }
        
        print(f"  ✗ Could not extract challenge solution")
        if VERBOSE:
            print(f"  → Content preview:\n{content[:500]}")
    
    return None


def make_request(url, timeout, headers, cookies=None, referer=None):
    """Make HTTP request using the best available method"""
    final_headers = headers.copy()
    if referer:
        final_headers['Referer'] = referer
    
    if session_type == 'curl_cffi':
        response = curl_requests.get(
            url,
            timeout=timeout,
            headers=final_headers,
            cookies=cookies,
            impersonate="chrome120",
            allow_redirects=True
        )
        return response
    else:
        response = session.get(
            url,
            timeout=timeout,
            headers=final_headers,
            cookies=cookies,
            allow_redirects=True
        )
        return response


def fetch_stream_url(stream_config, attempt_num=1):
    """Fetch the YouTube stream m3u8 URL"""
    stream_type = stream_config.get('type', 'channel')
    stream_id = stream_config['id']
    slug = stream_config['slug']
    
    if stream_type == 'video':
        query_param = 'v'
    elif stream_type == 'channel':
        query_param = 'c'
    else:
        print(f"✗ Unknown type '{stream_type}' for {slug}")
        return None, 'InvalidType'
    
    url = f"{ENDPOINT}/yt.php?{query_param}={stream_id}"
    print(f"  Fetching: {url}")
    
    try:
        # User-Agent is handled by the session/scraper automatically
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # --- RASTGELE GECİKME (RANDOM DELAY) ---
        random_delay = random.uniform(0.5, 2.0)
        print(f"  → Applying random human-like delay: {random_delay:.2f}s")
        time.sleep(random_delay)
        
        print(f"  → Sending GET request (timeout={TIMEOUT}s, attempt={attempt_num})...")
        
        response = make_request(url, TIMEOUT, headers)
        
        # Debug info
        # print(f"  → Status: {response.status_code}")
        
        response.raise_for_status()
        
        # Challenge Handling
        challenge_solution = solve_js_challenge_advanced(response, slug, url)
        
        if challenge_solution:
            solution_type = challenge_solution['type']
            target_url = challenge_solution['url']
            challenge_cookies = challenge_solution['cookies']
            
            print(f"  → Attempting to solve challenge (type: {solution_type})...")
            time.sleep(2)
            
            request_cookies = dict(response.cookies)
            if challenge_cookies:
                request_cookies.update(challenge_cookies)
            
            print(f"  → Following challenge solution to: {target_url}")
            response2 = make_request(
                target_url,
                TIMEOUT,
                headers,
                cookies=request_cookies if request_cookies else None,
                referer=url
            )
            response2.raise_for_status()
            
            second_challenge = solve_js_challenge_advanced(response2, slug, target_url)
            if second_challenge:
                print(f"  ✗ Still facing challenge after solution attempt")
                return None, 'ChallengeFailed'
            
            response = response2
        
        # Content Check
        content_preview = response.text[:200] if len(response.text) > 200 else response.text
        
        if '#EXTM3U' in content_preview:
            print(f"  ✓ Valid m3u8 content detected")
            return response.text, None
        elif '<html' in content_preview.lower() or '<!doctype' in content_preview.lower():
            print(f"  ✗ Error: Received HTML instead of m3u8")
            if any(i in response.text for i in ['Checking your browser', 'Just a moment', 'cloudflare']):
                return None, 'ChallengeNotSolved'
            return None, 'HTMLResponse'
        else:
            if '.m3u8' in content_preview or 'EXT-X-' in content_preview:
                print(f"  ⚠ Content might be valid m3u8 despite missing header")
                return response.text, None
            return None, 'InvalidContent'
            
    except requests.exceptions.Timeout:
        print(f"  ✗ Timeout error for {slug}")
        return None, 'Timeout'
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Connection error for {slug}")
        return None, 'ConnectionError'
    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTP error for {slug}: {e.response.status_code}")
        return None, f'HTTPError-{e.response.status_code}'
    except Exception as e:
        print(f"  ✗ Request error for {slug}: {type(e).__name__}")
        print(f"  → Details: {e}")
        return None, type(e).__name__


def fetch_stream_url_with_retry(stream_config):
    """Fetch stream URL with retry logic"""
    slug = stream_config['slug']
    last_error_type = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            delay = RETRY_DELAY * (2 ** (attempt - 2))
            print(f"  → Retry {attempt}/{MAX_RETRIES} after {delay}s delay...")
            time.sleep(delay)
        
        result, error_type = fetch_stream_url(stream_config, attempt)
        if result is not None:
            return result, None
        
        last_error_type = error_type
        if attempt < MAX_RETRIES:
            print(f"  → Attempt {attempt} failed, will retry...")
            
    print(f"  ✗ All {MAX_RETRIES} attempts failed for {slug}")
    return None, last_error_type


def reverse_hls_quality(m3u8_content):
    """Reverse the quality order in m3u8 playlist"""
    lines = m3u8_content.split('\n')
    stream_blocks = []
    current_block = []
    
    for line in lines:
        if line.startswith('#EXTM3U'):
            continue
        elif line.startswith('#EXT-X-STREAM-INF'):
            if current_block:
                stream_blocks.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)
            if line and not line.startswith('#'):
                stream_blocks.append(current_block)
                current_block = []
    
    if current_block:
        stream_blocks.append(current_block)
    
    stream_blocks.reverse()
    
    result = ['#EXTM3U']
    for block in stream_blocks:
        result.extend(block)
    
    return '\n'.join(result)


def get_output_path(stream_config):
    """Get the output file path based on category/subfolder"""
    slug = stream_config['slug']
    # 'category' alanı main fonksiyonunda yüklenirken eklenir
    subfolder = stream_config.get('category', '')
    
    if subfolder:
        output_dir = Path(FOLDER_NAME) / subfolder
    else:
        output_dir = Path(FOLDER_NAME)
    
    return output_dir / f"{slug}.m3u8"


def delete_old_file(stream_config):
    """Delete the old m3u8 file if it exists"""
    output_file = get_output_path(stream_config)
    try:
        if output_file.exists():
            output_file.unlink()
            print(f"  ⚠ Deleted old file: {output_file}")
            return True
    except Exception as e:
        print(f"  ⚠ Could not delete old file {output_file}: {e}")
        return False
    return False


def save_stream(stream_config, m3u8_content):
    """Save m3u8 content to file"""
    output_file = get_output_path(stream_config)
    output_dir = output_file.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    reversed_content = reverse_hls_quality(m3u8_content)
    
    try:
        with open(output_file, 'w') as f:
            f.write(reversed_content)
        print(f"  ✓ Saved: {output_file}")
        return True
    except Exception as e:
        print(f"  ✗ Error saving {output_file}: {e}")
        return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Update YouTube stream m3u8 playlists',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('config_files', nargs='+', help='Configuration file(s) to process')
    parser.add_argument('--endpoint', default=ENDPOINT, help=f'API endpoint URL (default: {ENDPOINT})')
    parser.add_argument('--folder', default=FOLDER_NAME, help=f'Output folder name (default: {FOLDER_NAME})')
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help=f'Request timeout (default: {TIMEOUT})')
    parser.add_argument('--retries', type=int, default=MAX_RETRIES, help=f'Max retries (default: {MAX_RETRIES})')
    parser.add_argument('--retry-delay', type=int, default=RETRY_DELAY, help=f'Retry delay (default: {RETRY_DELAY})')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--fail-on-error', action='store_true', help='Exit with error on fail')
    
    return parser.parse_args()


# --- TASK FUNCTION FOR CONCURRENCY ---
def process_stream_task(stream_config):
    """Worker function for concurrent execution"""
    slug = stream_config.get('slug', 'unknown')
    
    m3u8_content, error_type = fetch_stream_url_with_retry(stream_config)
    
    if m3u8_content:
        if save_stream(stream_config, m3u8_content):
            return 'success', slug, None
        else:
            delete_old_file(stream_config)
            return 'fail', slug, 'SaveError'
    else:
        delete_old_file(stream_config)
        return 'fail', slug, error_type


# --- MAIN EXECUTION ---
def main():
    """Main function"""
    global VERBOSE, ENDPOINT, FOLDER_NAME, TIMEOUT, MAX_RETRIES, RETRY_DELAY, MAX_CONCURRENCY
    args = parse_arguments()
    
    ENDPOINT = args.endpoint
    FOLDER_NAME = args.folder
    TIMEOUT = args.timeout
    MAX_RETRIES = args.retries
    RETRY_DELAY = args.retry_delay
    VERBOSE = args.verbose
    
    print("=" * 50)
    print("YouTube Stream Updater (Concurrent + Multi-Category)")
    print("=" * 50)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Output folder: {FOLDER_NAME}")
    print(f"Max Concurrency: {MAX_CONCURRENCY}")
    print("=" * 50)
    
    total_success = 0
    total_fail = 0
    error_summary = {}
    
    all_streams = []
    
    # 1. Load all config files
    for config_file in args.config_files:
        print(f"\n📄 Loading config: {config_file}")
        streams_from_file, filename_stem = load_config(config_file)
        
        if streams_from_file:
            # Set category based on filename (e.g., 'turkish' from 'turkish.json')
            category = filename_stem if filename_stem else "default"
            for stream in streams_from_file:
                stream['category'] = category
            
            all_streams.extend(streams_from_file)
            
    total_streams = len(all_streams)
    if total_streams == 0:
        print("No streams found to process. Exiting.")
        sys.exit(0)

    print(f"\n🔥 Starting concurrent process for {total_streams} streams (Max {MAX_CONCURRENCY} at once)...")
    
    # 2. Run concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        future_to_stream = {
            executor.submit(process_stream_task, stream): stream for stream in all_streams
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_stream), 1):
            stream = future_to_stream[future]
            slug = stream.get('slug', 'unknown')
            category = stream.get('category', 'unknown')
            
            print(f"\n[{i}/{total_streams}] Finished: {slug} (Category: {category})")
            
            try:
                status, stream_slug, error_type = future.result()
                
                if status == 'success':
                    total_success += 1
                else:
                    total_fail += 1
                    if error_type:
                        error_summary[error_type] = error_summary.get(error_type, 0) + 1
                    print(f"  ✗ FAILED: {error_type}")
            except Exception as exc:
                total_fail += 1
                error_type = type(exc).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
                print(f"  ✗ CRITICAL FAILURE: {exc}")

    # 3. Summary
    print("\n" + "=" * 50)
    print(f"Complete: {total_success} successful, {total_fail} failed")
    
    if error_summary:
        print("\nError Breakdown:")
        for error_type, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {error_type}: {count}")
    print("=" * 50)
    
    if total_fail > 0 and args.fail_on_error:
        sys.exit(1)

if __name__ == "__main__":
    main()
