# -*- coding: UTF-8 -*-

from scrapy.spiders import Spider
from mycrawler.items import BasicItem
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sets import Set
import scrapy
import logging


class TplinkSpider(Spider):
    name = "tplink"
    start_urls = [
        "http://service.tp-link.com.cn/list_download_software_1_0.html"
    ]
    timeout = 5
    trytimes = 3

    def parse(self, response):

        browser = webdriver.Firefox()
        browser.implicitly_wait(TplinkSpider.timeout)
        browser.set_page_load_timeout(TplinkSpider.timeout)

        t = TplinkSpider.trytimes
        try:
            browser.get(response.url)
        except TimeoutException:
            pass

        page = u"0"
        t = TplinkSpider.trytimes
        links = Set()
        while True:
            try:
                tmpfunc = lambda d: page != (d.find_element_by_id(
                    "paging").find_element_by_class_name("selected").text)
                WebDriverWait(browser, TplinkSpider.timeout)\
                    .until(tmpfunc)
            except WebDriverException, e:
                try:
                    browser.find_element_by_id("paging")\
                        .find_element_by_xpath("a[last()]").click()
                except TimeoutException:
                    pass
                if t == 0:
                    browser.quit()
                    raise e
                t -= 1
                continue
            else:
                page = browser.find_element_by_id("paging")\
                    .find_element_by_class_name("selected").text

            try:
                table = browser.find_element_by_id("mainlist")
            except NoSuchElementException, e:
                t -= 1
                if t == 0:
                    browser.quit()
                    raise e

            t = TplinkSpider.trytimes
            rows = table.find_elements_by_xpath("//tr[position()>1]")

            for tr in rows:
                # links.add(tr.find_element_by_xpath(
                  #  'td[1]/a').get_attribute("href"))

                t = TplinkSpider.trytimes
                while True:
                    try:
                        nbrowser = webdriver.Firefox()
                        yield self.parse_page(tr.find_element_by_xpath(
                            'td[1]/a').get_attribute("href"), nbrowser)
                    except WebDriverException, e:
                        t -= 1
                        nbrowser.quit()
                        if t == 0:
                            logging.log(logging.ERROR,
                                        "Link %s parse failed", link)
                            logging.exception(e)
                            break
                    else:
                        nbrowser.quit()
                        break

            if browser.find_element_by_id("paging")\
                    .find_element_by_xpath("a[last()-1]").get_attribute("class") == "selected":
                break
#			break #debug

            logging.log(
                logging.INFO, "Page %s finished: Total %d links", page, len(links))

            try:
                browser.find_element_by_id("paging")\
                    .find_element_by_xpath("a[last()]").click()
            except TimeoutException:
                pass
            t = TplinkSpider.trytimes

        files = Set()
        i = 0
        for link in links:
            break
            t = TplinkSpider.trytimes
            while True:
                try:
                    nbrowser = webdriver.Firefox()
                    files.update(self.parse_page(link, nbrowser))
                except WebDriverException, e:
                    t -= 1
                    nbrowser.quit()
                    if t == 0:
                        logging.log(logging.ERROR,
                                    "Link %s parse failed", link)
                        logging.exception(e)
                        break
                else:
                    nbrowser.quit()
                    break
            i += 1
            logging.log(
                logging.INFO, "[Progress] Link %d/%d parse finished, get %d items", i, len(links), len(files))
        browser.quit()
        # return files

    def parse_page(self, link, browser):

        browser.implicitly_wait(TplinkSpider.timeout)
        browser.set_page_load_timeout(TplinkSpider.timeout)
        try:
            browser.get(link)
        except TimeoutException:
            pass

        element = WebDriverWait(browser, TplinkSpider.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "download")))
        lines = element.find_elements_by_xpath(
            "table/tbody/tr[position()<last()]")
        item = BasicItem()
        item["Firm"] = "Tplink"
        item["Info"] = {}
        for l in lines:
            key = l.find_element_by_xpath("td[1]").text.lstrip()
            val = l.find_element_by_xpath("td[2]")
            if key == u"立即下载":
                item["Link"] = val.find_element_by_xpath(
                    "a").get_attribute("href")
                item["Rawlink"] = item["Link"]
                item["Filename"] = item["Rawlink"].rsplit("/", 1).pop()
            elif key == u"软件名称":
                item["Title"] = val.text
            elif key == u"软件简介":
                item["Descr"] = val.text
            else:
                item["Info"][key] = val.text
        return item
