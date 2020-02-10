import re
from urllib.parse import urlparse, urldefrag
from urllib import robotparser
import os

# Additional packages
from lxml import html
from bs4 import BeautifulSoup

visited = set()
disallowed = ["https://wics.ics.uci.edu/events/","https://www.ics.uci.edu/community/involved/","https://www.ics.uci.edu/ugrad/policies/Grade_Options/", "https://www.ics.uci.edu/accessibility/community/", "https://www.ics.uci.edu/involved/corporate_partner.php/"]
# trap_parts = ["calendar"]

def scraper(url, resp):
    new_links = set()
    if 200 <= resp.status <= 299 and resp.status != 204:
        # URLs that are scraped are already validated
        print("Before url1")
        print("URLLLLL1" ,url)
        visited.add(url)
        links = extract_next_links(url, resp)
        for link in links:
            parsed = urlparse(link)
            if is_valid(link):
                new_links.add(link)
                print("URL:",link,"Parsed:", parsed)
                print("-----------------")

    return list(new_links)

def extract_next_links(url, resp):

    # log scraped urls
    header_response = resp.raw_response.headers['Content-Type'].split(';')[0]
    with open("scraped_urls.txt", "w") as output_file:
        output_file.write(header_response + ' ' + url + '\n')
    print("after header write")

    # Check if HTTP status code 200 has no content
    if resp.status == 200 and str(resp.raw_response.content) == "":
        return list()

    new_links = set()

    doc = html.fromstring(resp.raw_response.content)
    doc_links = list(doc.iterlinks())
    
    for link in doc_links:
        print("urldefrag")
        defragged_link = urldefrag(link[2])[0]
        print("afterdefrag")
        # print("DEFRAG--------------DEFRAG")
        # print("Defragged link:", defragged_link)
        if (defragged_link != ""):
            new_links.add(defragged_link)
    return list(new_links)

def check_robot(url, parsed):
    print("insider check robot")
    robot = robotparser.RobotFileParser()
    # robot.set_url(parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt")
    if robot:
        robot.read()
        return robot.can_fetch("*", url)
    return True

def is_valid(url):
    try:
        parsed = urlparse(url)
        print("URL2:",url,"Parsed:", parsed)
        print("-----------------")
        
        if url in visited:
            return False

        for trap in disallowed:
            if trap in url:
                return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        # Create and check robots.txt
        if not check_robot(url, parsed):
            return False

        if len(url) > 175:
            return False

        valid_domains = re.match(r".*\.ics|cs|informatics|stat\.uci\.edu(\/.*)*" + r"today\.uci\.edu\/department\/information_computer_sciences(\/.*)*", parsed.netloc.lower()) 

        return valid_domains and not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
