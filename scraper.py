import re
from urllib.parse import urlparse, urldefrag
from urllib import robotparser
import os

# Additional packages
from lxml import html
from bs4 import BeautifulSoup

visited = set()
disallowed = ["https://wics.ics.uci.edu/events/","http://www.ics.uci.edu/community/events/"]
trap_parts = ["calendar","replytocom","wp-json","?share=","format=xml", "/feed", "/feed/"]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    print()
    print("--------scraper()---------")
    print("BASE URL:", url)
    print("TOTAL VISITED AFTER SCRAPING THIS URL:", len(visited))
    print("New links (not validated):")
    for link in links:
        print(link, "->", is_valid(link))
    print("--------scraper()---------")
    print()
    return [link for link in links if is_valid(link)]


def fix_relative_url(url, base_parse):
    fixed = ""

    if url == "":
        return fixed

    parse_raw = urlparse(url)
    path_separator = ""
    if parse_raw.path != "" and parse_raw.path[0] != "/":
        path_separator = "/"

    # Fix relative urls
    if parse_raw.scheme == "" and parse_raw.netloc == "":
        # /community/news -> https://www.stat.uci.edu/community/news
        print("Base_parse:", base_parse)
        fixed = base_parse.geturl().lower() + path_separator + parse_raw.geturl().lower()
    elif parse_raw.scheme == "":
        # //www.ics.uci.edu/community/news/view_news?id=1689 -> https://www.ics.uci.edu/community/news/view_news?id=1689
        fixed = "https:" + parse_raw.geturl().lower()
    else:
        fixed = url.lower()
    return fixed    


def extract_next_links(url, resp):
    new_links = set()
    parsed_base = urlparse(url)
    if 200 <= resp.status <= 299 and  resp.status != 204:

        # Checking that only text/HTML pages are scraped (so other types such as calendars won't be)
        resp_content_type = resp.raw_response.headers['Content-Type'].split(';')[0]
        if resp_content_type != "text/html":
            print()
            print("----------------------")
            print("----------------------")
            print("content-type != text/html. it is:", resp_content_type)
            print("----------------------")
            print("----------------------")
            print()
            return []

        # Add base url to visited
        visited.add(url)

        # Scrape for links using bs4
        bs = BeautifulSoup(resp.raw_response.content, "lxml")

        # Check for status code 200 and no content
        if resp.status == 200 and str(bs) == "":
            return []

        print()
        print("--------BASE---------")
        print("BASE URL:", url)
        print("TOTAL VISITED UP TO BEFORE SCRAPING THIS URL:", len(visited))
        print("--------BASE---------")
        print()

        for link in bs.find_all("a"):
            link = link.get("href")
            
            # Remove fragment, if any
            defragged_link = urldefrag(link)[0]
            absolute_link = fix_relative_url(defragged_link, parsed_base)
            parse_relative = urlparse(defragged_link)

            # Skip empty links
            if absolute_link == "":
                continue

            if absolute_link not in visited:
                visited.add(absolute_link)
                new_links.add(absolute_link)

            print("-----------------------")
            print("Original:", defragged_link)
            print("Absolute:", absolute_link)
            print("Relative parse:", parse_relative)
            print("content-type:", resp_content_type)
            print("-----------------------")
            print()

    return list(new_links)


def check_robot(url, parsed):
    print("------------------------------")
    print("IN CHECK_ROBOT WITH URL:", url)
    print("------------------------------")

    robot = robotparser.RobotFileParser()
    robot.set_url(parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt")
    if robot:
        robot.read()
        return robot.can_fetch("*", url)
    return True


def is_valid(url):
    print("------------------------------")
    print("IN IS_VALID WITH URL:", url)
    print("------------------------------")
    try:
        parsed = urlparse(url)

        # Check if already visited
        # if url in visited:
        #     return False

        # Check scheme of url
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check if url is too long
        if len(url) > 175:
            return False

        # Check for trap websites
        for trap_website in disallowed:
            if trap_website in url:
                return False

        for trap in trap_parts:
            if trap in url:
                return False
        
        # Match allowed domains
        valid_domains = re.match(r".*\.ics|cs|informatics|stat\.uci\.edu(\/.*)*" + r"today\.uci\.edu\/department\/information_computer_sciences(\/.*)*", parsed.netloc.lower()) 

        if not valid_domains:
            return False

        # Check that url does not contain invalid types in middle or in query
        valid_mid_and_query = (r".*\/(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|feed"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz).*$")

        if re.match(valid_mid_and_query, parsed.query.lower()) or re.match(valid_mid_and_query, parsed.path.lower()):
            print("invalid mid and query: ", url);
            return False

        invalid_end_url = re.match(
            r".*\.(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|php|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        if invalid_end_url:
            print("invalid end url: ", url);
            return False

        # Create and check robots.txt
        if not check_robot(url, parsed):
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
