import re
from urllib.parse import urlparse
from urllib import robotparser

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

def extract_next_links(url, resp):
    # Implementation requred.
    new_links = []

    try:
        parse = urlparse(url)
        robot = createRobot(parse.scheme + "://" + parse.netloc + "/robots.txt")
        print(parse)
        if 200 <= resp.status <= 599:
            raw = resp.raw_response
            print(raw.text)
    except:
        print("Except")
        
    return new_links

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        console.log("Parsed", parsed)
        validPath = r".*\.(ics|cs|informatics|stat)\.uci\.edu/.*|today\.uci\.edu/department/information_computer_sciences/.*"
        # return re.match(validPath, parsed.path.lower()) and not re.match(
        return not re.match(
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
