from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
import time

from urllib.parse import urlparse
from urllib import robotparser


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.robots = dict()
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            try:
                tbd_url = self.frontier.get_tbd_url()
                if not tbd_url:
                    self.logger.info("Frontier is empty. Stopping Crawler.")
                    break
                resp = download(tbd_url, self.config, self.logger)
                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                scraped_urls = scraper(tbd_url, resp, str(self.config.user_agent))
                for scraped_url in scraped_urls:

                    parsed = urlparse(parsed)
                    robots_url = parsed.scheme + "://" + parsed.netloc.lower() + "/robots.txt"
                    netloc = parsed.netloc.lower()
                    can_crawl = True

                    if netloc not in self.robots:
                        robot = robotparser.RobotFileParser()
                        robot.set_url(robots_url)
                        if robot != None:
                            robot.read()
                            self.robots[netloc] = robot
                        

                    if netloc in self.robots and self.robots[netloc]:
                        can_crawl self.robots[netloc].can_fetch("*", url)

                    if can_crawl:
                        self.frontier.add_url(scraped_url)
                        
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)
            except Exception as e:
                print("Exception:",e)
                with open("errors.txt", "a+") as errors_file:
                    errors_file.write("url: " + tbd_url + "\n")
                    errors_file.write("Exception: " + e + "\n\n")
                continue
