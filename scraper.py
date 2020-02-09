# import re
# from urllib.parse import urlparse

# def scraper(url, resp):
#     print("Scraper")
#     links = extract_next_links(url, resp)
#     return [link for link in links if is_valid(link)]

# def extract_next_links(url, resp):
#     # Implementation requred.
#     # Testing
#     new_links = []
#     print("Extract_next_links")

#     try:
#         parsed = urlparse(url)
#         print("Parsed", parsed.netloc)
#     except:
#         print("except")
    
#     return new_links

# def is_valid(url):
#     print("is_valid", url)
#     try:
#         parsed = urlparse(url)
#         if parsed.scheme not in set(["http", "https"]):
#             return False
#         return not re.match(
#             r".*\.(css|js|bmp|gif|jpe?g|ico"
#             + r"|png|tiff?|mid|mp2|mp3|mp4"
#             + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
#             + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
#             + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
#             + r"|epub|dll|cnf|tgz|sha1"
#             + r"|thmx|mso|arff|rtf|jar|csv"
#             + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

#     except TypeError:
#         print ("TypeError for ", parsed)
#         raise
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from lxml import etree
from io import *


robots = {}


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def add_robot(base_url):

    # Adds the robots.txt in a global dictionary, returning the read robot.txt
    if base_url not in robots:
        robots_file = RobotFileParser()
        robots_file.set_url(base_url)
        robots_file.read()
        robots[base_url] = robots_file

    return robots[base_url]


def extract_next_links(url, resp):
    # Implementation required.
    final = []
    try:
        parsed = urlparse(url)
        if 200 <= resp.status <= 599:

            # gets the html root
            html = resp.raw_response.content.decode('utf-8')
            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(html), parser)
            root = tree.getroot()

            # creates a robots url for the parser
            base_url = parsed.scheme + '://' + parsed.netloc + '/robots.txt'
            robot_parser = add_robot(base_url)


            print(robot_parser.request_rate('*'))

            # checks to see if the url is able to be fetched in within the domain, based on the robots.txt
            if robot_parser.can_fetch('*', url):

                # loops through all <a> tag
                for i in root.xpath('/html')[0].getiterator('a'):

                    url_dict = i.attrib

                    # gets the href of the <a> tag
                    if 'href' in url_dict:
                        curr_url = url_dict['href']
                        final_url = ''

                        # creates the url to put in the frontier
                        if len(curr_url) >= 2 and curr_url[0] == '/' and curr_url[1] != '/':
                            final_url = parsed.scheme + '://' + parsed.netloc + curr_url
                        elif len(curr_url) > 0 and curr_url[0] != '/' and curr_url[0] != '#':
                            final_url = curr_url

                        # removes the fragment from the url
                        split_value = final_url.split('#')[0]
                        if split_value != '':
                            final.append(split_value)

    except Exception as e:
        print('ERROR OCCURED')
        with open('Error_file.txt', 'a+') as f:
            f.write(str(type(e)) + ' ' + str(e) + '\n')
    finally:
        return final


def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        match_domains = re.match(
            r".*\.(ics|cs|informatics|stat)\.uci\.edu\/.*|today\.uci\.edu\/department\/information_computer_sciences\/.*$",
            url
        )
        # print(url, parsed.path)
        return match_domains and not re.match(
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