import re
from urllib.parse import urlparse
from urllib import robotparser

# Additional packages
from bs4 import BeautifulSoup

robots = dict()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def createRobot(url):
    if url not in robots:
        rp = robotparser.RobotFileParser(url)
        rp.read()
        robots[url] = rp
    return robots[url]

def extract_raw_links(raw):
    links = []
    soup = BeautifulSoup(raw, features="lxml")
    for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
        links.append(link)
    return links

def extract_next_links(url, resp):
    # Implementation requred.
    new_links = set()

    try:
        parse = urlparse(url)
        robot = createRobot(parse.scheme + "://" + parse.netloc + "/robots.txt")
        print(parse)
        if 200 <= resp.status <= 599:
            raw = resp.raw_response
            raw_links = extract_raw_links(raw.text)
            print(raw_links)
            for link in raw_links:
                if robot.can_fetch("*", link):
                    new_links.add(link.get("href"))
    except Exception as e:
        print("Except", e)
        
    return list(new_links)

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        console.log("Parsed", parsed)
        validPath = r".*\.(ics|cs|informatics|stat)\.uci\.edu/.*|today\.uci\.edu/department/information_computer_sciences/.*"
        return re.match(validPath, url.lower()) and not re.match(
        # return not re.match(
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
