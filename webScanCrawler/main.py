
from bs4 import BeautifulSoup as bs
import requests
from urllib.parse import urljoin
import tldextract
import re


# Global variables
security_headers = [
    'Strict-Transport-Security',    # i made these headers so check if response has these headers
    'Content-Security-Policy',
    'X-Content-Type-Options',
    'X-Frame-Options',
    'Referrer-Policy',
    'Permissions-Policy',
]
OUTDATED_SOFTWARE_REGEX = {
    "Apache": r"Apache\/(\d+)\.(\d+)(?:\.(\d+))?",      # regex to match version numbers of software
    "PHP": r"PHP\/(\d+)\.(\d+)(?:\.(\d+))?",
    "Nginx": r"Nginx\/(\d+)\.(\d+)(?:\.(\d+))?",
}

missing_headers=set()
outdated_software=set()
insecure_forms=set()
visited_urls = set()
count_of_urls_visited = 0
DEPT=0
missing_headers_report ={}
forms_issues_report = {}

# Function to extract the domain from a URL

def getdomain(url):
    ext=tldextract.extract(url)             #on cwaling there we might find urls with different domains so we need to extract domain from url
    return f"{ext.domain}.{ext.suffix}"     #so we need to extract domain from url to check if the url is from same domain or not

# checks if two uls are from same domain
def same_domain(url1):
    return getdomain(url1) == getdomain(base_url)

# send a request to url
def send_request(url):
    try:
        response = requests.get(url, timeout=5)         # i want this function to send a request to a url and 
        return response                                 # return the response if the request is successful      
    except requests.RequestException as e:
        print(f"An error occurred while requesting {url}: {e}")
        return None
# check if url has necessary security headers
def list_all_links(soup, base_url):
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)          # handles relative URLs by joining them with the base URL
        if not href or href.startswith("mailto:") or href.startswith("javascript:"):    # i realised that href might be empty or might be a 
            continue                                                                    # mailto or javascript link so 
        if full_url not in visited_urls and same_domain(full_url):                      #i need to check if 
            links.append(full_url)
    return links

def check_headers_security(response):
    missing_headers = []
    try:
        for header in security_headers:             #simply made to check if response has necessary headers or not
            if header not in response.headers:      # if response does not have the header then we add it to missing_headers
                missing_headers.append(header)
        return missing_headers
    except Exception as e:
        print(f"An error occurred while requesting: {e}")

# Function to check forms security
# checks if forms have action and method attributes
def check_forms_security(soup):
    forms = soup.find_all('form')
    issues=[]
    for form in forms:
        action = form.get('action', '')
        method = form.get('method', 'get').lower()
        if action=='':
            issues.append("Empty form Action")
        if method !='post':
            issues.append("Form dont use POST")
        return issues if issues else None
    
# Function to check software versions
# checks if software versions are outdated or not
def check_software_versions(headers):
    server_info = headers.get("Server", "")
    server_info += headers.get("X-Powered-By", "")
    outdated = []
    for software, pattern in OUTDATED_SOFTWARE_REGEX.items():
        match = re.search(pattern, server_info, re.IGNORECASE)
        if match:
            major, minor, patch = match.groups()
            major = int(major)
            minor = int(minor)
            patch = int(patch) if patch is not None else 0  
            if (software == "Apache" and (major, minor, patch) < (2, 4, 10)) or \
               (software == "PHP" and (major, minor, patch) < (7, 4, 13)) or \
               (software == "Nginx" and (major, minor, patch) < (1, 18, 0)):
                outdated.add(f"{software} {major}.{minor}.{patch}")
    return outdated if outdated else None
        

    # Main crawling function
def crawl(url):
    global DEPT
    global count_of_urls_visited
    
    if len(visited_urls) > 100:
        print("Visited more than 100 URLs, stopping the crawl.")
        return None
    count_of_urls_visited+=1
    if DEPT>20:
        DEPT-=1
        return None
    DEPT+=1
    print(f"\nCurrent Depth: {DEPT}")
    print(f"Visiting: {url}:")
    response = send_request(url)
    soup=bs(response.text, 'html.parser')
    if response is None:                    # response aayena vane aarko url ma jancha
        print(f"Failed to visit {url}")
        return None
    visited_urls.add(url)
    print(f"Visited URLs: {len(visited_urls)}")

    # checking if response has necessary security headers
    missing_header_of_url=check_headers_security(response)
    if missing_header_of_url:
        missing_headers_report [url]=missing_header_of_url
        missing_headers.update(missing_header_of_url)

    # checking forms
    url_from_issues= check_forms_security(soup)
    if url_from_issues:
        forms_issues_report[url] = url_from_issues
        insecure_forms.update(url_from_issues)

    # check if software versions are outdated or not
    outdated_software_of_url = check_software_versions(response.headers)
    if outdated_software_of_url:
        outdated_software.update(outdated_software_of_url)

    #current url ma visit gare paxi child links haru lai find garne    
    child_links= list_all_links(soup, url)
    for link in child_links:
        if link not in visited_urls and same_domain(link):
            crawl(link)
    DEPT-=1
    return None



#main function to start crawling
base_url=str(input("Enter the base URL to start crawling: "))
crawl(base_url)
print("Missing security headers:")
with open('missing_headers_report.txt', 'w') as f:
    for url, headers in missing_headers_report.items():
        f.write(f"{url}: {', '.join(headers)}\n")
with open('form_issues_report.txt', 'w') as f:
    for url, issues in forms_issues_report.items():
        f.write(f"{url}: {', '.join(issues)}\n")
        
# RRPORT
print(f"\n\n\tVULNERABILITY SCAN REPORT FOR {base_url}\n")

print(f"\tTotal URLs visited: {count_of_urls_visited}\n\n")

# Reporting missing security headers
if not missing_headers:
    print("\n- No missing security headers found.")
else:
    print("\n- MISSING HTTP SECURITY HEADERS::")
    for missing  in missing_headers:
        print(f"\t{missing}")


# Reporting outdated software
if not outdated_software:
    print("\n- No Outdated Software found.")
else:
    print("\n- Oudated Software version detected:")
    for software in outdated_software:
        print(f"\t{software}")

# Reporting forms security issues
if not insecure_forms:
    print("\n- No insecure forms found.")
else:
    print("\n- Insecure forms found:")
    for form in insecure_forms:
        print(f"\t{form}")
