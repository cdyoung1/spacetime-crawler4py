import re
from urllib.parse import urlparse, urldefrag
from urllib import robotparser
import shelve

# Additional packages
from lxml import html

# Setting up robots
robots = dict()
robot_urls = ["https://www.ics.uci.edu/robots.txt","https://www.cs.uci.edu/robots.txt", "https://www.informatics.uci.edu/robots.txt","https://www.stat.uci.edu/robots.txt", "https://today.uci.edu/robots.txt"]
illegal = ["/pdf/",".pdf","/?ical=1","/calendar/","format=xml","replytocom","wp-json","?share=google-plus","?share=facebook","?share=twitter"]
traps = ["https://wics.ics.uci.edu/events/","http://sli.ics.uci.edu/PmWiki/PmWiki"]

def createRobots():
    for robot_url in robot_urls:
        if robot_url not in robot_urls:
            robot = robotparser.RobotFileParser()
            robot.set_url(robot_url)
            robot.read()
            robots[robot_url] = robot

def scraper(url, resp):
    createRobots()
    # links = extract_next_links(url, resp)

    if 400 <= resp.status <= 608 or resp.status ==  204:
        return list()
 
    valid_links = [link for link in extract_next_links(url, resp) if is_valid(link)]
    final_links = set()

    url_shelve = shelve.open("urls.shelve")
    for link in valid_links:
        if link not in url_shelve:
            url_shelve[link] = 1
            # print("New Link:", link)
            final_links.add(link)
        else:
            url_shelve[link] += 1
            # print("Link already exists:", link, ", Count:", url_shelve[link])
    print("Current unique url count:", len(url_shelve))
    url_shelve.close()

    return list(final_links)

    
def robot_allowed_link(url):
    for robot in robots.values():
        if not robot.can_fetch("*", url):
            return False
    return True

def extract_next_links(url, resp):
    # url_shelve = shelve.open("urls.shelve")
    new_links = set()

    doc = html.fromstring(resp.raw_response.content)
    doc_links = list(doc.iterlinks())
    # print("Doc_links:",  doc_links)
    
    for link in doc_links:
        defragged_link = urldefrag(link[2])[0]
        # print(defragged_link)
        new_links.add(defragged_link)
    return list(new_links)

def is_valid(url):
    try:
        parsed = urlparse(url)
        print("Parsed:", url, parsed)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not robot_allowed_link(url):
            return False
        
        for s in illegal:
            if s in url:
                print("DETECTED DISALLOWED PART OF URL", url)
                return False
        
        for trap in traps:
            if s in url:
                print("TRAP SITE", url)
                return False

        valid_domains = r"((.*\.)(ics|cs|informatics|stat)\.uci\.edu(\/.*)*)|(today\.uci\.edu\/department\/information_computer_sciences(\/.*)*)"
        return re.match(valid_domains, url.lower()) and not re.match(
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
