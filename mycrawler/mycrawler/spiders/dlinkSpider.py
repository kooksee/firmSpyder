# -*- coding: UTF-8 -*-

from scrapy.spiders import Spider
from scrapy.http import Request
from mycrawler.items import BasicItem
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sets import Set
import logging
import scrapy


class DlinkSpider(Spider):
    name = "dlink"
    timeout = 8
    trytimes = 3
    start_urls = ["ftp://ftp2.dlink.com/PRODUCTS"]
    handle_httpstatus_list = [404]

    # must be lower character
    suffix = ["zip", "obj", "exe", "drv", "com", "lan",
              "dlf", "tar", "tgz", "gz", "iso", "img", "dmg"]
    allsuffix = Set()

    def start_requests(self):
        for url in DlinkSpider.start_urls:
            yield Request(url, meta={'ftp_user': 'anonymous', 'ftp_password': ''})

    def _loadcomplete(self, x):
        if len(x.find_elements_by_xpath("html/body/table/tbody/tr")) == self.finds:
            return True
        self.finds = len(x.find_elements_by_xpath("html/body/table/tbody/tr"))
        return False

    def parse(self, response):

        browser = webdriver.Firefox()
        browser.implicitly_wait(DlinkSpider.timeout)
        browser.set_page_load_timeout(DlinkSpider.timeout)

        t = DlinkSpider.trytimes
        try:
            browser.get(response.url)
        except TimeoutException:
            pass
        self.dirs = Set()
        for i in browser.find_elements_by_xpath("//a[@class='dir']"):
            #			print i.get_attribute("href")
            self.dirs.add(i.get_attribute("href"))
#		print len(self.dirs)
#		print self.dirs
#		return
        logging.log(logging.INFO, "Root Fetch:%d", len(self.dirs))
        items = Set()
        while len(self.dirs):
            d = self.dirs.pop()
            t = DlinkSpider.trytimes
            while True:
                try:
                    browser.get(d)
                    self.finds = -1
                    try:
                        WebDriverWait(browser, DlinkSpider.timeout).until(
                            self._loadcomplete)
                    except TimeoutException:
                        pass
                    lines = browser.find_elements_by_xpath(
                        "html/body/table/tbody/tr")
                    logging.log(logging.INFO, "Fetch:%s,len:%d", d, len(lines))
                    for l in lines:
                        a = l.find_element_by_xpath("td[1]//a")
                        if a.get_attribute("class") == "dir":
                            self.dirs.add(a.get_attribute("href"))
                        elif a.get_attribute("class") == "file":
                            filename = a.text
                            filetype = filename.rsplit(
                                ".", 1).pop().strip().lower()
                            DlinkSpider.allsuffix.add(filetype)
#							print "FileType",filetype
                            if filetype in DlinkSpider.suffix:
                                item = BasicItem()
                                item["Firm"] = "Dlink"
                                item["Link"] = a.get_attribute("href").strip()
                                item["Rawlink"] = item["Link"]
                                item["Filename"] = filename
                                item["Title"] = item["Filename"]
                                item["Descr"] = browser.find_element_by_xpath(
                                    "//h1").text.rsplit("/", 1)[0]
                                item["Info"] = {}
                                item["Info"]["Date"] = l.find_element_by_xpath(
                                    "td[3]").text
                                # items.add(item)
                                yield item
#						return items #debug
                except Exception, e:
                    t -= 1
                    if t == 0:
                        logging.exception(e)
                        break
                    continue
                else:
                    break

        logging.log(logging.CRITICAL, "AllSuffix: %s",
                    str(DlinkSpider.allsuffix))
        logging.log(logging.CRITICAL, "ParseSuffix: %s",
                    str(DlinkSpider.suffix))

        browser.quit()
        # return items
