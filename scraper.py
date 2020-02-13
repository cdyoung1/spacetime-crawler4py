import re
from urllib.parse import urlparse, urldefrag, urljoin
from urllib.request import urlopen
from urllib import robotparser
import os

# Additional packages
from bs4 import BeautifulSoup
from simhash import Simhash, SimhashIndex

visited = set()
robots = dict()
wordsDict = dict()
stats = {"longest-page-count": 0, "longest-page" : ""}
subdomains = dict()
SimIndex = SimhashIndex([])
interval = 1

disallowed = ["https://wics.ics.uci.edu/events/","http://www.ics.uci.edu/community/events/", "https://grape.ics.uci.edu/wiki/public/wiki/", "https://ngs.ics.uci.edu/blog/page/","https://www.ics.uci.edu/~eppstein/pix/chron.html"]
trap_parts = ["/calendar","replytocom=","wp-json","share=","format=xml", "/feed", "/feed/", ".pdf", ".php", ".zip", ".sql", "action=login", "?ical=", ".ppt", "version="]

def scraper(url, resp):
    global subdomains
    global stats
    global wordsDict
    global interval

    scraped_links = set()
    links = extract_next_links(url, resp)

    if resp.raw_response != None:
        tokenize(url, resp.raw_response.content)

    print()
    print("--------scraper()---------")
    print("BASE URL:", url)
    print("TOTAL VISITED AFTER SCRAPING THIS URL:", len(visited))
    print("--------scraper()---------")
    print()

    for link in links:
        if is_valid(link):
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

    with open("links.txt", "a+") as links_file:
        links_file.write(url + "\n")

    if interval % 8 == 0:
        with open("subdomains.txt", "w") as subdomain_file:
            for kv in sorted(subdomains.items(), key = lambda x : x[0]):
                subdomain_file.write(str(kv[0]) + ", " + str(kv[1]) + "\n")

        with open("stats.txt", "w") as stats_file:
            stats_file.write(str(stats))

        if len(wordsDict) >= 50:
            with open("words.txt", "w") as words_file:
                for kv in sorted(wordsDict.items(), key = lambda x : x[1], reverse = True):
                    words_file.write(str(kv[0]) + " -> " + str(kv[1]) + "\n")
    interval += 1

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

    # print()
    # print("----------FIX_RELATIVE_URL--------------")
    # print("URL to be tested:", url)
    # print("URL to be tested parse:", parse_raw)
    # print("Base url:", base_parse.geturl())
    # print("URLJOINED with base:", urljoin(base_parse.geturl(), url))
    # print("Fixed:", fixed)
    # print("----------FIX_RELATIVE_URL--------------")
    # print()

    return fixed

def tokenize(url, html):
    global wordsDict
    global stats
    stopwords = {"about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's""me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}

    bs = BeautifulSoup(html, "lxml")
    text = bs.get_text().lower()

    words = re.sub(r"[^a-zA-Z\']", " ", text).split()
    wordCount = 0

    for word in words:
        word.strip("'")
        if word not in stopwords:
            if len(word) <= 1:
                continue
            
            wordCount+=1
            if word not in wordsDict:
                wordsDict[word] = 1
            else:
                wordsDict[word] += 1
    if stats["longest-page-count"] < wordCount:
        stats["longest-page-count"] = wordCount
        stats["longest-page"] = url  


def extract_next_links(url, resp):
    global sim_index
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

        url_sim = Simhash(bs.get_text())
        if SimIndex.get_near_dups(url_sim):
            print()
            print("-------SIMHASH-------")
            print("THIS IS A NEAR DUPLICATE ACCORDING TO SIMHASH:", url)
            print("-------SIMHASH-------")
            print()
            with open("near_dupes.txt", "a+") as dupes_file:
                dupes_file.write(url + "\n")
            return []        

        # print()
        # print("--------BASE---------")
        # print("BASE URL:", url)
        # print("TOTAL VISITED UP TO BEFORE SCRAPING THIS URL:", len(visited))
        # print("--------BASE---------")
        # print()

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

            # print("-----------------------")
            # print("Original:", defragged_link)
            # print("Absolute:", absolute_link)
            # print("Relative parse:", parse_relative)
            # print("content-type:", resp_content_type)
            # print("-----------------------")
            # print()

        # Add new Simhash object after fixing link
        SimIndex.add(url, url_sim)

    return list(new_links)


def check_robot(url, parsed):
    # print("------------------------------")
    # print("IN CHECK_ROBOT WITH URL:", url)
    # print("------------------------------")
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

        dates_v1 = r".*((\/\d{4}\/\d{1,2})|(\/\d{1,2}\/\d{4})).*"
        dates_v2 = r".*(\d{4}-\d{2}-\d{2}).*"
        pages = r".*\/pages?\/\d+(\/.*)?"

        # Checks for calendar-like or pagination-like paths (only used for indexing other pages that are already checked)
        if re.match(dates_v1, url.lower()) or re.match(dates_v2, url.lower()) or re.match(pages, url.lower()):
            return False

        # Check that url does not contain invalid types in middle of path
        invalid_mid_path = (r".*(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|feed"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|php|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz).*$")

        if re.match(invalid_mid_path, parsed.path.lower()):
            return False

        invalid_end_path = re.match(
            r".*\.(css|js|pix|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|php|pptx|doc|docx|xls|xlsx|names"
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
