import re
from urllib.parse import urlparse, urldefrag, urljoin
from urllib import robotparser
import os
from io import *

# Additional packages
from bs4 import BeautifulSoup             # BeautifulSoup is a Python web scraping library that parses HTML/XML data
from lxml import etree, html              # lxml is a Python web scraping library that parses HTML/XML data
from simhash import Simhash, SimhashIndex # This library is from Leon Sim's Python Simhash which can be found at: https://github.com/leonsim/simhash

# Data structures used to detect unique/valid links
visited = set()             # Set of unique links that have been visited
robots = dict()             # Dict of unique robots (per subdomain). Maps subdomain -> RobotParser object
SimIndex = SimhashIndex([]) # Object from simhash library used to store simhashes and calculate near dupes

# Data structures used to calculate and store statistics
stats = {"longest-page-count": 0, "longest-page" : ""} # Question 2: Longest page and its # of words
pageWordCounts = dict()                                # Dict that maps valid urls -> word count
subdomains = dict()                                    # Dict that maps unique subdomains -> unique pages
wordsDict = dict()                                     # Dict that maps unique words -> # of occurences

# URLs and keywords to ignore based off a page's URL

# Hardcoded pages that are either traps or used for indexing (low textual content)
disallowed = ["https://wics.ics.uci.edu/events/","https://grape.ics.uci.edu/wiki/public/timeline", 
            "https://ngs.ics.uci.edu/blog/page/","https://www.ics.uci.edu/~eppstein/pix/"]
# Hardcoded keywords to check a URL for either traps or disallowed actions/file types
trap_parts = ["/calendar","replytocom=","wp-json","share=","format=xml", "/feed", "/feed/", 
            ".pdf", ".zip", ".sql", "action=login", "?ical=", ".ppt", "version=", "action=diff", "do=diff", "difftype=sidebyside"]


# scrape a URL and its response to check for additional URLs to add to frontier
def scraper(url, resp):
    global stats, pageWordCounts, subdomains, wordsDict

    scraped_links = set() # set of unique, valid links to add to frontier and return from scraper
    links = extract_next_links(url, resp)

    # If url has a response, tokenize page and add statistics information
    if resp.raw_response != None:
        tokenize(url, resp.raw_response.content.decode('utf-8'))

    print()
    print("--------scraper()---------")
    print("BASE URL:", url)
    print("TOTAL VISITED AFTER SCRAPING THIS URL:", len(visited))
    print("--------scraper()---------")
    print()

    # Iterate through scraped links from url and check if it is valid
    for link in links:
        if is_valid(link):
            scraped_links.add(link)
            parsed = urlparse(link)

            # Use regex to parse for [subdomain].ics.uci.edu and add to subdomain page count if so
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
    # Try/except for writing statistics into respective files
    try:
        # Add url to links.txt in order of frontier
        with open("links.txt", "a+") as links_file:
            links_file.write(url + "\n")

        # Update subdomains.txt in alphabetical order
        with open("subdomains.txt", "w") as subdomain_file:
            for kv in sorted(subdomains.items(), key = lambda x : x[0]):
                subdomain_file.write(str(kv[0]) + ", " + str(kv[1]) + "\n")

        # Update largest page/word count statistics
        with open("stats.txt", "w") as stats_file:
            stats_file.write(str(stats) + "\n")
            stats_file.write("================================")
            for kv in sorted(pageWordCounts.items(), key = lambda x : x[1], reverse = True):
                stats_file.write(str(kv[0]) + " -> " + str(kv[1]) + "\n")

        # Update word count statistics
        if len(wordsDict) >= 50:
            with open("words.txt", "w") as words_file:
                for kv in sorted(wordsDict.items(), key = lambda x : x[1], reverse = True):
                    words_file.write(str(kv[0]) + " -> " + str(kv[1]) + "\n")
    except Exception as e:
        print("Exception: ", e)
    finally:
        return list(scraped_links)


# Fix url (either relative or absolute) to its absolute path
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

    return fixed

# Parse url and its html content for statistics (word count, longest page/word count)
def tokenize(url, html):
    global wordsDict, pageWordCounts, stats

    # Stopwords from https://www.ranks.nl/stopwords - Default English Stopwords
    stopwords = {"about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's""me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}

    words = []
    wordCount = 0

    parser = etree.HTMLParser()
    et = etree.parse(StringIO(html), parser)
    r = et.getroot()

    for i in r.xpath('/html')[0].getiterator('*'):
        if i.tag not in {"script", "style"}:
            if i.text is not None:
                words.append(i.text.lower())

    # Replace anything that is not A-Z, a-z, 0-9, or " ' " with a space and split it
    text = ' '.join(words)
    words = re.sub(r"[^a-zA-Z0-9\']", " ", text).split()

    for word in words:

        # strip ends of apostrophes and spaces ( bobs' -> bobs)
        word = word.strip()
        word = word.strip("'") 

        if word == None or word == "":
            continue

        if word not in stopwords:

            # Ignore single characters
            if len(word) <= 1:
                continue

            wordCount+=1
            if word not in wordsDict:
                wordsDict[word] = 1
            else:
                wordsDict[word] += 1

    pageWordCounts[url] = wordCount

    if stats["longest-page-count"] < wordCount:
        stats["longest-page-count"] = wordCount
        stats["longest-page"] = url  


# Scrape all urls from text/html pages that have not been scraped yet (aka not in visited set() yet)
# Also check for near dupes using Simhash and SimhashIndex
def extract_next_links(url, resp):
    new_links = set()
    parsed_base = urlparse(url)

    if 200 <= resp.status <= 599 and  resp.status != 204:

        # Checking that only text/HTML pages are scraped (so other types such as calendars won't be)
        resp_content_type = resp.raw_response.headers['Content-Type'].split(';')[0]

        if resp_content_type != "text/html":
            return []

        # Add base url to visited
        visited.add(url)

        # Scrape for links using bs4
        bs = BeautifulSoup(resp.raw_response.content, "lxml")

        # Check for status code 200 and no content
        if resp.status == 200 and str(bs) == "":
            return []

        # Generate a Simhash object based off page's text
        url_sim = Simhash(bs.get_text())

        # Check for near dupes, and if so, return an empty list
        if SimIndex.get_near_dups(url_sim):
            return []        

        # For every url, fix it to it's absolute url and add to new_links set if it has not been visited
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

            if absolute_link not in visited:
                visited.add(absolute_link)
                new_links.add(absolute_link)
            else:
                continue

        # Add new Simhash object for base url to SimhashIndex
        SimIndex.add(url, url_sim)

    return list(new_links)


# Check if a robot for a URL's subdomain exists, and use it. If not, create a new one
def check_robot(url, parsed):
    try:
        robots_url = parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt"
        netloc = parsed.netloc.lower()
        if netloc not in robots:
            robot = robotparser.RobotFileParser()
            robot.set_url(robots_url)
            if robot:
                robot.read()
                robots[netloc] = robot
        if netloc in robots:
            return robots[netloc].can_fetch("*", url)
        return True
    except:
        return True


# Check if a url is valid (valid scheme, [sub]domain, and for traps/disallowed sites)
def is_valid(url):
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

        dates_v1 = r".*((\/\d{4}\/\d{1,2})|(\/\d{1,2}\/\d{4})).*" # Ex. 2014/02 or 02/2014
        dates_v2 = r".*(\d{4}-\d{2}-\d{2}).*"                     # Ex. 2014-02-12
        pages = r".*\/pages?\/\d+(\/.*)?"                         # Ex. /pages/3 or /page/3

        # Checks for calendar-like or pagination-like paths (only used for indexing other pages that are already checked)
        if re.match(dates_v1, url.lower()) or re.match(dates_v2, url.lower()) or re.match(pages, url.lower()):
            return False

        # Check that url does not contain invalid types in middle of path
        invalid_mid_path = (r".*(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|feed"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz).*$")

        if re.match(invalid_mid_path, parsed.path.lower()):
            return False

        # Check the end of path for invalid types
        invalid_end_path = re.match(
            r".*\.(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        if invalid_end_path:
            return False

        # Create and check robots.txt
        if not check_robot(url, parsed):
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
