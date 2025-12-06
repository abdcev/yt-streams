# Fallback to standard requests
import requests

# =========================
# Configuration (MULTI-ENDPOINT)
# =========================

# Eski tek ENDPOINT desteği için default
DEFAULT_ENDPOINT = os.environ.get('ENDPOINT')

# ENDPOINT1..ENDPOINT10 listesini oku
ENDPOINTS = []
for i in range(1, 11):  # ENDPOINT1..ENDPOINT10
    val = os.environ.get(f'ENDPOINT{i}')
    if val:
        ENDPOINTS.append(val)

# Eğer hiç ENDPOINT1..10 yoksa, eski ENDPOINT'i kullan
if not ENDPOINTS:
    ENDPOINTS = [DEFAULT_ENDPOINT]

# Configuration
ENDPOINT = os.environ.get('ENDPOINT', 'https://your-endpoint.com')
FOLDER_NAME = os.environ.get('FOLDER_NAME', 'streams')
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
VERBOSE = False


def create_session():
"""Create the best available HTTP session"""
if CLOUDSCRAPER_AVAILABLE:
print("✓ Using enhanced cloudscraper for JavaScript challenge bypass")

        
# Use the zinzied/cloudscraper enhanced fork features
try:
scraper = cloudscraper.create_scraper(
@@ -125,7 +108,6 @@ def create_session():
session.mount('https://', adapter)
return session, 'requests'


# Initialize session
session, session_type = create_session()

@@ -157,25 +139,25 @@ def extract_redirect_url(html_content):
# Pattern 3: meta refresh
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

    
# Look for document.cookie patterns
cookie_patterns = [
r'document\.cookie\s*=\s*["\']([^"\']+)["\']',
r'document\.cookie\s*=\s*([^;]+);',
]

    
for pattern in cookie_patterns:
matches = re.finditer(pattern, html_content)
for match in matches:
@@ -185,14 +167,14 @@ def extract_challenge_cookies(html_content):
parts = cookie_str.split('=', 1)
if len(parts) == 2:
cookies[parts[0].strip()] = parts[1].strip()

    
return cookies


def solve_js_challenge_advanced(response, slug, base_url):
"""Detect and solve JavaScript challenge with multiple strategies"""
content = response.text

    
# Check if this is a JS challenge page
challenge_indicators = [
'<script type="text/javascript" src="/aes.js"',
@@ -202,12 +184,12 @@ def solve_js_challenge_advanced(response, slug, base_url):
'Please wait',
'Verifying you are human'
]

    
is_challenge = any(indicator in content for indicator in challenge_indicators)

    
if is_challenge:
print(f"  ⚠ JavaScript/Anti-bot challenge detected")

        
# Strategy 1: Extract redirect URL
redirect_url = extract_redirect_url(content)
if redirect_url:
@@ -218,13 +200,13 @@ def solve_js_challenge_advanced(response, slug, base_url):
redirect_url = f"{parsed.scheme}://{parsed.netloc}{redirect_url}"
elif not redirect_url.startswith('http'):
redirect_url = f"{base_url.rstrip('/')}/{redirect_url}"

            
return {
'type': 'redirect',
'url': redirect_url,
'cookies': extract_challenge_cookies(content)
}

        
# Strategy 2: Extract cookies and retry original URL
cookies = extract_challenge_cookies(content)
if cookies:
@@ -234,7 +216,7 @@ def solve_js_challenge_advanced(response, slug, base_url):
'url': base_url,
'cookies': cookies
}

        
# Strategy 3: Look for hidden form submission
form_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', content, re.IGNORECASE)
if form_match:
@@ -248,11 +230,11 @@ def solve_js_challenge_advanced(response, slug, base_url):
'url': form_action,
'cookies': {}
}

        
print(f"  ✗ Could not extract challenge solution")
if VERBOSE:
print(f"  → Content preview:\n{content[:500]}")

    
return None


@@ -261,7 +243,7 @@ def make_request(url, timeout, headers, cookies=None, referer=None):
final_headers = headers.copy()
if referer:
final_headers['Referer'] = referer

    
if session_type == 'curl_cffi':
# Use curl_cffi for tough challenges
response = curl_requests.get(
@@ -286,48 +268,34 @@ def make_request(url, timeout, headers, cookies=None, referer=None):


def fetch_stream_url_with_retry(stream_config):
    """
    Fetch stream URL with retry logic.
    Burada çoklu ENDPOINT desteği var:
    ENDPOINT1 olmazsa ENDPOINT2, o da olmazsa ENDPOINT3 ... şeklinde ilerler.
    """
    """Fetch stream URL with retry logic"""
slug = stream_config['slug']
last_error_type = None

    for ep_index, endpoint in enumerate(ENDPOINTS, start=1):
        print(f"  → Using endpoint {ep_index}: {endpoint}")
        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                delay = RETRY_DELAY * (2 ** (attempt - 2))  # Exponential backoff
                print(f"  → Retry {attempt}/{MAX_RETRIES} on endpoint {ep_index} after {delay}s delay...")
                time.sleep(delay)

            result, error_type = fetch_stream_url(stream_config, attempt, endpoint)
            if result is not None:
                if ep_index > 1:
                    print(f"  ✓ Succeeded on fallback endpoint {ep_index}")
                return result, None

            last_error_type = error_type
            if attempt < MAX_RETRIES:
                print(f"  → Attempt {attempt} failed on endpoint {ep_index}, will retry...")

        print(f"  ✗ Endpoint {ep_index} failed for {slug}, trying next endpoint (if any)...")

    print(f"  ✗ All endpoints failed for {slug}")
    
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            delay = RETRY_DELAY * (2 ** (attempt - 2))  # Exponential backoff
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


def fetch_stream_url(stream_config, attempt_num=1, endpoint=None):
    """Fetch the YouTube stream m3u8 URL for a given endpoint"""
def fetch_stream_url(stream_config, attempt_num=1):
    """Fetch the YouTube stream m3u8 URL"""
stream_type = stream_config.get('type', 'channel')
stream_id = stream_config['id']
slug = stream_config['slug']

    if endpoint is None:
        # Teorik olarak gelmez ama fallback olarak kalsın
        endpoint = ENDPOINTS[0] if ENDPOINTS else DEFAULT_ENDPOINT

    
# Build query string based on type
if stream_type == 'video':
query_param = 'v'
@@ -336,12 +304,12 @@ def fetch_stream_url(stream_config, attempt_num=1, endpoint=None):
else:
print(f"✗ Unknown type '{stream_type}' for {slug}")
return None, 'InvalidType'

    
# Build request URL
    url = f"{endpoint.rstrip('/')}/yt.php?{query_param}={stream_id}"

    url = f"{ENDPOINT}/yt.php?{query_param}={stream_id}"
    
print(f"  Fetching: {url}")

    
try:
# Prepare headers
headers = {
@@ -352,44 +320,44 @@ def fetch_stream_url(stream_config, attempt_num=1, endpoint=None):
'Connection': 'keep-alive',
'Upgrade-Insecure-Requests': '1'
}

        
print(f"  → Sending GET request (timeout={TIMEOUT}s, attempt={attempt_num})...")

        
# Make initial request
response = make_request(url, TIMEOUT, headers)

        
# Log response details
print(f"  → Status Code: {response.status_code}")
print(f"  → Content Type: {response.headers.get('Content-Type', 'N/A')}")
print(f"  → Content Length: {len(response.content)} bytes")

        
# Log redirect chain if any
if hasattr(response, 'history') and response.history:
print(f"  → Redirects: {len(response.history)} redirect(s)")
for i, hist_resp in enumerate(response.history, 1):
print(f"    {i}. {hist_resp.status_code} → {hist_resp.url}")
print(f"  → Final URL: {response.url}")

        
response.raise_for_status()

        
# Check if we got a challenge page
challenge_solution = solve_js_challenge_advanced(response, slug, url)

        
if challenge_solution:
solution_type = challenge_solution['type']
target_url = challenge_solution['url']
challenge_cookies = challenge_solution['cookies']

            
print(f"  → Attempting to solve challenge (type: {solution_type})...")

            
# Wait a bit before following (simulate human behavior)
time.sleep(2)

            
# Merge any cookies from the challenge
request_cookies = dict(response.cookies)
if challenge_cookies:
request_cookies.update(challenge_cookies)

            
# Make follow-up request
print(f"  → Following challenge solution to: {target_url}")
response2 = make_request(
@@ -399,49 +367,49 @@ def fetch_stream_url(stream_config, attempt_num=1, endpoint=None):
cookies=request_cookies if request_cookies else None,
referer=url
)

            
print(f"  → Second request status: {response2.status_code}")
print(f"  → Content Length: {len(response2.content)} bytes")
print(f"  → Content Type: {response2.headers.get('Content-Type', 'N/A')}")

            
response2.raise_for_status()

            
# Check if we still have a challenge
second_challenge = solve_js_challenge_advanced(response2, slug, target_url)
if second_challenge:
print(f"  ✗ Still facing challenge after solution attempt")
return None, 'ChallengeFailed'

            
response = response2  # Use the second response

        
# Check if content looks like m3u8
content_preview = response.text[:200] if len(response.text) > 200 else response.text

        
if '#EXTM3U' in content_preview:
print(f"  ✓ Valid m3u8 content detected")
return response.text, None
elif '<html' in content_preview.lower() or '<!doctype' in content_preview.lower():
print(f"  ✗ Error: Received HTML instead of m3u8")
if VERBOSE:
print(f"  → Content preview: {content_preview[:300]}...")

            
# Check if it's still a challenge page
if any(indicator in response.text for indicator in ['Checking your browser', 'Just a moment', 'cloudflare']):
return None, 'ChallengeNotSolved'

            
return None, 'HTMLResponse'
else:
print(f"  ⚠ Warning: Content doesn't start with #EXTM3U")
if VERBOSE:
print(f"  → Content preview: {content_preview[:150]}...")

            
# If content looks like it might be m3u8 without the header, try to use it
if '.m3u8' in content_preview or 'EXT-X-' in content_preview:
print(f"  ⚠ Content might be valid m3u8 despite missing header")
return response.text, None

            
return None, 'InvalidContent'

        
except requests.exceptions.Timeout:
error_type = 'Timeout'
print(f"  ✗ Timeout error for {slug}: Request exceeded {TIMEOUT}s")
@@ -474,11 +442,11 @@ def reverse_hls_quality(m3u8_content):
   High quality streams will appear first
   """
lines = m3u8_content.split('\n')

    
# Find all stream definitions (lines starting with #EXT-X-STREAM-INF)
stream_blocks = []
current_block = []

    
for line in lines:
if line.startswith('#EXTM3U'):
# Keep header
@@ -493,40 +461,40 @@ def reverse_hls_quality(m3u8_content):
# End of this stream block
stream_blocks.append(current_block)
current_block = []

    
# Add any remaining block
if current_block:
stream_blocks.append(current_block)

    
# Reverse the order (high quality first)
stream_blocks.reverse()

    
# Reconstruct m3u8
result = ['#EXTM3U']
for block in stream_blocks:
result.extend(block)

    
return '\n'.join(result)


def get_output_path(stream_config):
"""Get the output file path for a stream"""
slug = stream_config['slug']
subfolder = stream_config.get('subfolder', '')

    
# Build output path
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
@@ -535,95 +503,25 @@ def delete_old_file(stream_config):
except Exception as e:
print(f"  ⚠ Could not delete old file {output_file}: {e}")
return False

    
return False

def select_best_variant(m3u8_content):
    """
    Master m3u8 içinden sadece EN YÜKSEK kalite varyantı seçer.
    Önce BANDWIDTH'e, o yoksa RESOLUTION'a göre karar verir.
    Eğer master playlist değilse (varyant yoksa) orijinali döner.
    """
    lines = m3u8_content.split('\n')

    stream_blocks = []
    current_block = []

    for line in lines:
        if line.startswith('#EXT-X-STREAM-INF'):
            # Yeni bir varyant bloğu başlıyor
            if current_block:
                stream_blocks.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)
            # Varyant URL satırı .m3u8 ile biter, burada bloğu tamamlıyoruz
            if line.strip().endswith('.m3u8'):
                stream_blocks.append(current_block)
                current_block = []

    # Son blok eklenmemişse ekle
    if current_block:
        stream_blocks.append(current_block)

    # Eğer hiç varyant yoksa (demek ki bu zaten media playlist), dokunmadan geri ver
    if not stream_blocks:
        return m3u8_content

    best_block = None
    best_score = -1

    for block in stream_blocks:
        info_line = block[0]  # #EXT-X-STREAM-INF satırı

        # Önce BANDWIDTH bak
        bw_match = re.search(r'BANDWIDTH=(\d+)', info_line)
        if bw_match:
            score = int(bw_match.group(1))
        else:
            # BANDWIDTH yoksa RESOLUTION'a göre puan ver
            res_match = re.search(r'RESOLUTION=(\d+)x(\d+)', info_line)
            if res_match:
                w = int(res_match.group(1))
                h = int(res_match.group(2))
                score = w * h
            else:
                score = 0

        if score > best_score:
            best_score = score
            best_block = block

    # Güvenlik: yine de hiçbir şey bulamadıysak orijinali döndür
    if not best_block:
        return m3u8_content

    # Yeni playlist: sadece en iyi varyant
    result_lines = ['#EXTM3U']
    result_lines.extend(best_block)

    return '\n'.join(result_lines)


def save_stream(stream_config, m3u8_content):
"""Save m3u8 content to file"""
slug = stream_config['slug']

    
# Get output file path
output_file = get_output_path(stream_config)
output_dir = output_file.parent

    
# Create directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

    
# Reverse quality order
    # Önce master playlist içinden sadece EN YÜKSEK kaliteyi seç
    best_only = select_best_variant(m3u8_content)
    reversed_content = reverse_hls_quality(m3u8_content)

    # İstersen hala sırayı ters çevirebilirsin (tek varyantta fark etmez ama zararı yok)
    reversed_content = reverse_hls_quality(best_only)

# Write to file
    # Write to file
try:
with open(output_file, 'w') as f:
f.write(reversed_content)
@@ -634,7 +532,6 @@ def save_stream(stream_config, m3u8_content):
return False



def parse_arguments():
"""Parse command line arguments"""
parser = argparse.ArgumentParser(
@@ -648,121 +545,108 @@ def parse_arguments():
 python update_streams.py config.json --retries 5 --timeout 60
       """
)

    
parser.add_argument(
'config_files',
nargs='+',
help='Configuration file(s) to process'
)

    # Buradaki endpoint parametresi artık "primary" endpoint gibi,
    # ENV üzerinden gelen ENDPOINT1..10 listesine 1. eleman olarak yazıyoruz.
    
parser.add_argument(
'--endpoint',
        default=DEFAULT_ENDPOINT,
        help=f'Primary API endpoint URL (default: {DEFAULT_ENDPOINT})'
        default=ENDPOINT,
        help=f'API endpoint URL (default: {ENDPOINT})'
)

    
parser.add_argument(
'--folder',
default=FOLDER_NAME,
help=f'Output folder name (default: {FOLDER_NAME})'
)

    
parser.add_argument(
'--timeout',
type=int,
default=TIMEOUT,
help=f'Request timeout in seconds (default: {TIMEOUT})'
)

    
parser.add_argument(
'--retries',
type=int,
default=MAX_RETRIES,
        help=f'Maximum retry attempts per endpoint (default: {MAX_RETRIES})'
        help=f'Maximum retry attempts (default: {MAX_RETRIES})'
)

    
parser.add_argument(
'--retry-delay',
type=int,
default=RETRY_DELAY,
help=f'Initial retry delay in seconds (default: {RETRY_DELAY})'
)

    
parser.add_argument(
'-v', '--verbose',
action='store_true',
help='Enable verbose debug output'
)

    
parser.add_argument(
'--fail-on-error',
action='store_true',
help='Exit with error code if any streams fail (default: exit successfully)'
)

    
return parser.parse_args()


def main():
"""Main execution function"""
    global VERBOSE, FOLDER_NAME, TIMEOUT, MAX_RETRIES, RETRY_DELAY
    global DEFAULT_ENDPOINT, ENDPOINTS

    global VERBOSE
args = parse_arguments()

    
# Update globals with command line arguments
    DEFAULT_ENDPOINT = args.endpoint
    global ENDPOINT, FOLDER_NAME, TIMEOUT, MAX_RETRIES, RETRY_DELAY
    ENDPOINT = args.endpoint
FOLDER_NAME = args.folder
TIMEOUT = args.timeout
MAX_RETRIES = args.retries
RETRY_DELAY = args.retry_delay
VERBOSE = args.verbose

    # ENDPOINTS listesini CLI primary endpoint ile güncelle
    if not ENDPOINTS:
        ENDPOINTS = [DEFAULT_ENDPOINT]
    else:
        # ENV'den gelenler varsa, birinci sırayı CLI endpoint ile override et
        ENDPOINTS[0] = DEFAULT_ENDPOINT

    
print("=" * 50)
print("YouTube Stream Updater (Improved)")
print("=" * 50)
    print(f"Primary endpoint: {ENDPOINTS[0]}")
    print("Endpoint list (fallback order):")
    for idx, ep in enumerate(ENDPOINTS, start=1):
        print(f"  {idx}. {ep}")
    print(f"Endpoint: {ENDPOINT}")
print(f"Output folder: {FOLDER_NAME}")
print(f"Config files: {', '.join(args.config_files)}")
print(f"Timeout: {TIMEOUT}s")
    print(f"Max retries per endpoint: {MAX_RETRIES}")
    print(f"Max retries: {MAX_RETRIES}")
print(f"Retry delay: {RETRY_DELAY}s")
print(f"Verbose: {VERBOSE}")
print(f"Session type: {session_type}")
print("=" * 50)

    
total_success = 0
total_fail = 0
error_summary = {}  # Track error types

    
# Process each config file
for config_file in args.config_files:
print(f"\n📄 Processing config: {config_file}")
print("-" * 50)

        
# Load configuration
streams = load_config(config_file)

        
# Process each stream
for i, stream in enumerate(streams, 1):
slug = stream.get('slug', 'unknown')
print(f"\n[{i}/{len(streams)}] Processing: {slug}")

            # Fetch stream URL with retry (ve çoklu endpoint fallback)
            
            # Fetch stream URL with retry
m3u8_content, error_type = fetch_stream_url_with_retry(stream)

            
if m3u8_content:
# Save to file
if save_stream(stream, m3u8_content):
@@ -779,19 +663,19 @@ def main():
# Track error type
if error_type:
error_summary[error_type] = error_summary.get(error_type, 0) + 1

    
# Summary
print("\n" + "=" * 50)
print(f"Complete: {total_success} successful, {total_fail} failed")

    
# Error breakdown
if error_summary:
print("\nError Breakdown:")
for error_type, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
print(f"  • {error_type}: {count}")

    
print("=" * 50)

    
# Handle exit code based on --fail-on-error flag
if total_fail > 0:
if args.fail_on_error:
