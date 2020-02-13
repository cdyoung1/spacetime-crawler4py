import re
from urllib.parse import urlparse, urldefrag, urljoin
from urllib import robotparser
import os
import configparser

# Additional packages
from bs4 import BeautifulSoup
from simhash import Simhash, SimhashIndex
from config import USERAGENT

visited = set()
robots = dict()
subdomains = dict()
SimIndex = SimhashIndex([])

config = configparser.ConfigParser()
config.read("config.ini")

disallowed = ["https://wics.ics.uci.edu/events/","http://www.ics.uci.edu/community/events/", "https://grape.ics.uci.edu/wiki/public/wiki/", "https://ngs.ics.uci.edu/blog/page/","https://www.ics.uci.edu/~eppstein/pix/chron.html"]
trap_parts = ["/calendar","replytocom=","wp-json","share=","format=xml", "/feed", "/feed/", "action=", "/pdf", ".pdf", ".php", ".zip", "action=login", "?ical=", ".ppt"]

def scraper(url, resp, useragent):
    global subdomains

    # if 399 < resp.status < 609 or resp.status == 204:
    #     return []

    scraped_links = set()
    links = extract_next_links(url, resp)
    # global link_num
    print()
    print("--------scraper()---------")
    print("BASE URL:", url)
    print("TOTAL VISITED AFTER SCRAPING THIS URL:", len(visited))
    print("--------scraper()---------")
    print()
    for link in links:
        if is_valid(link, useragent):
            scraped_links.add(link)
            parsed = urlparse(link)
            subdomain = re.match(r"^(www)?(?P<sub>.*)\.ics\.uci\.edu.*$", parsed.netloc.lower())
            sub = ""
            if subdomain != None:
                sub = subdomain.group("sub").strip()
                if sub == None or sub == "": 
                    continue
                elif sub in subdomains:
                    subdomains[sub] += 1
                else:
                    subdomains[sub] = 1
    with open("links.txt", "w") as links_file:
        links_file.write(link + "\tsubdomain: " + sub + "\n")
    with open("subdomains.txt", "w") as subdomain_file:
        for kv in sorted(subdomains.items(), key = lambda x : x[0]):
            subdomain_file.write(str(kv[0]) + ", " + str(kv[1]) + "\n")
        # subdomain_file.write(str(sorted(subdomains.items(), key=lambda kv : kv[1], reverse=True)))
    # if link_num % 10 == 0:

    # link_num +=1
    return list(scraped_links)



def fix_relative_url(url, base_parse):
    fixed = ""

    if url == "":
        return fixed

    parse_raw = urlparse(url)

    if url.startswith("//"):
        fixed = urljoin("https://", url).rstrip("/")
    elif url.startswith("/"):
        fixed = urljoin("https://"+base_parse.netloc, url).rstrip("/")
    else:
        fixed = url


    # # Check if url already exists in base path
    # possible_repeat_path = url
    # if possible_repeat_path[-1] == "/":
    #     possible_repeat_path = possible_repeat_path[:-1]

    print()
    print("----------FIX_RELATIVE_URL--------------")
    print("URL to be tested:", url)
    print("URL to be tested parse:", parse_raw)
    print("Base url:", base_parse.geturl())
    print("URLJOINED with base:", urljoin(base_parse.geturl(), url))
    print("Fixed:", fixed)
    print("----------FIX_RELATIVE_URL--------------")
    print()

    return fixed


def get_text(parser):

    allowed_tags = {'p', 'span', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'blockquote', 'code', 'li', 'ol', 'ul', 'mark', 'ins', 'del', 'sup', 'sub', 'small', 'i', 'b', 'title', 'td', 'th', 'caption'}

    result = ""
    text_list = parser.find_all(lambda tag : tag.name in allowed_tags)
    for text in text_list:
        result += text.get_text().lower() + "\n"
    return result


def tokenize():
    pass


def extract_next_links(url, resp):
    global sim_index
    new_links = set()
    parsed_base = urlparse(url)
    if 200 <= resp.status <= 599 and  resp.status != 204:

        # Checking that only text/HTML pages are scraped (so other types such as calendars won't be)
        resp_content_type = resp.raw_response.headers['Content-Type'].split(';')[0]

        # if resp_content_type == "text/calendar":
        #     return []

        # Add base url to visited
        visited.add(url)

        # Scrape for links using bs4
        bs = BeautifulSoup(resp.raw_response.content, "lxml")

        # Check for status code 200 and no content
        if resp.status == 200 and str(bs) == "":
            return []

        url_sim = Simhash(get_text(bs))
        if SimIndex.get_near_dups(url_sim):
            print()
            print("-------SIMHASH-------")
            print("THIS IS A NEAR DUPLICATE ACCORDING TO SIMHASH")
            print("-------SIMHASH-------")
            print()
            return []        

        print()
        print("--------BASE---------")
        print("BASE URL:", url)
        print("TOTAL VISITED UP TO BEFORE SCRAPING THIS URL:", len(visited))
        print("--------BASE---------")
        print()

        for link in bs.find_all("a"):
            link = link.get("href")

            if link == None or link == "":
                continue
            else:
                link = link.lower()
            
            # Remove fragment, if any
            defragged_link = urldefrag(link)[0].rstrip("/")
            absolute_link = fix_relative_url(defragged_link, parsed_base)
            parse_relative = urlparse(defragged_link)

            # Skip empty links
            if absolute_link == "":
                continue

            # Check if relative path already exists in base_url (checks for relative traps)
            # possible_path_link = defragged_link[:-1] if defragged_link[-1] == '/' else defragged_link
            # if possible_path_link in url:
            #     print("Possible repeating pathing from '" + url + "' to '" + possible_path_link + "'")
            #     continue

            if absolute_link not in visited:
                visited.add(absolute_link)
                new_links.add(absolute_link)
            else:
                continue

            print("-----------------------")
            print("Original:", defragged_link)
            print("Absolute:", absolute_link)
            print("Relative parse:", parse_relative)
            print("content-type:", resp_content_type)
            print("-----------------------")
            print()

        # Add new Simhash object after fixing link
        SimIndex.add(absolute_link, url_sim)

    return list(new_links)


def check_robot(url, parsed, useragent):
    print("------------------------------")
    print("IN CHECK_ROBOT WITH URL:", url)
    print("------------------------------")

    robots_url = parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt"
    netloc = parsed.netloc.lower()
    if netloc not in robots:
        robot = robotparser.RobotFileParser()
        robot.set_url(robots_url)
        if robot:
            robot.read()
            robots[netloc] = robot

    if netloc in robots and robots[netloc]:
        return robots[netloc].can_fetch(useragent, url)
    return True


def is_valid(url, useragent):
    print("------------------------------")
    print("IN IS_VALID WITH URL:", url)
    print("------------------------------")
    try:
        parsed = urlparse(url)

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
        valid_domains = r"((.*\.)?(ics|cs|informatics|stat)\.uci\.edu)|(today\.uci\.edu\/department\/information_computer_sciences)\/?.*" 

        if not re.match(valid_domains, parsed.netloc.lower()):
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
            return False

        invalid_end_url = re.match(
            r".*\.(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        if invalid_end_url:
            print("invalid end url: ", url);
            return False

        # Create and check robots.txt
        if not check_robot(url, parsed, useragent):
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
