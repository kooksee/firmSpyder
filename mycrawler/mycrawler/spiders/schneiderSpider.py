# -*- coding: UTF-8 -*-

from scrapy.spiders import Spider
from mycrawler.items import BasicItem
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sets import Set
import logging
import scrapy


class SchneiderSpider(Spider):
    name = "schneider"
    start_urls = [
        "http://www.schneider-electric.com/download/ww/en/results/3541958-SoftwareFirmware/1555893-Firmware--Released/?showAsIframe=false",
        "http://www.schneider-electric.com/download/ww/en/results/3541958-SoftwareFirmware/1555902-Firmware--Updates/?showAsIframe=false",
    ]
    timeout = 5
    trytimes = 3

    # must be lower character
    suffix = ["zip", "bin", "exe", "rar", "upg", "7z", "tar", "gz", "tgz"]
    allsuffix = Set()

    def parse(self, response):

        browser = webdriver.Firefox()
        browser.implicitly_wait(SchneiderSpider.timeout)
        browser.set_page_load_timeout(SchneiderSpider.timeout)
# return

# self.parse_page("http://www.schneider-electric.com/download/ww/en/details/987961741-ComX-510-v1144-Firmware-EBX510/?showAsIframe=false&reference=ComX510v1-1-44_Firmware_EBX510",browser)

        t = SchneiderSpider.trytimes
        while True:
            try:
                browser.get(response.url)
            except TimeoutException:
                pass
            try:
                table = browser.find_element_by_id("gridResults")
            except Exception, e:
                t -= 1
                if t == 0:
                    browser.quit()
                    raise e
            else:
                break

#		sel=Selector(table)
#		print table.get_attribute("innerHTML")
        page = u"0"
        t = SchneiderSpider.trytimes
        links = Set()
        while True:
            try:
                WebDriverWait(browser, SchneiderSpider.timeout).until(
                    lambda d: page != (d.find_element_by_id(
                        "gridPager_right").find_element_by_class_name("sel").text))
            except WebDriverException, e:
                if t == 0:
                    browser.quit()
                    raise e
                t -= 1
                continue
            page = browser.find_element_by_id(
                "gridPager_right").find_element_by_class_name("sel").text
            rows = table.find_elements_by_xpath("//tr[position()>1]")
            for tr in rows:
                links.add(tr.find_element_by_xpath(
                    'td[5]/a[1]').get_attribute("href"))
            if browser.find_element_by_id("gridPager_right").find_element_by_xpath("a[last()-1]").get_attribute("class") == "sel":
                break
            try:
                browser.find_element_by_id(
                    "gridPager_right").find_element_by_xpath("a[last()]").click()
            except TimeoutException:
                pass
            t = SchneiderSpider.trytimes

        files = Set()
        for link in links:
            t = SchneiderSpider.trytimes
            while True:
                try:
                    nbrowser = webdriver.Firefox()
                    yield self.parse_page(link, nbrowser)
                except WebDriverException, e:
                    t -= 1
                    nbrowser.quit()
                    if t == 0:
                        break
                else:
                    nbrowser.quit()
                    break
        browser.quit()
        # return files

#	def parse_page(self,response):
#		link=response.url
    def parse_page(self, link, browser):
        browser.implicitly_wait(SchneiderSpider.timeout)
        browser.set_page_load_timeout(SchneiderSpider.timeout)
        try:
            browser.get(link)
            WebDriverWait(browser, SchneiderSpider.timeout, 500).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jqgfirstrow")))
        except TimeoutException:
            pass

        scope = browser.find_element_by_class_name("mainPadding")
        item = BasicItem()
        item["Title"] = scope.find_element_by_xpath("//h1").text
        item["Firm"] = "Schneider"
        item["Info"] = {}

        labels = scope.find_elements_by_xpath("div/div/div[@class='label']/p")
        label_contents = scope.find_elements_by_xpath(
            "div/div/div[@class='labelContent']/p")
        for i in range(len(labels)):
            lable = labels[i]
            lst = lable.text.rstrip().rstrip(":").split(" ")
            if len(lst) == 0:
                continue

            key = lst[-1].lower()
            if key == "description":
                item["Descr"] = label_contents[i].text
            elif key in ["version", "ranges", "date", "reference"]:
                item["Info"][key] = label_contents[i].text

        datas = Set()
        links = scope.find_elements_by_xpath(
            "//table[@id='gridResults']/tbody/tr/td/a[@class='open-popup']")
        for l in links:
            filetype = l.text.split(".").pop()
            SchneiderSpider.allsuffix.add(filetype)
            if filetype in SchneiderSpider.suffix:
                item["Link"] = l.get_attribute("href")
                item["Rawlink"] = item["Link"].split("/?")[0]
                item["Filename"] = l.text
                # result.add(tmp)
                print "\n\n\n\nsucess"
                datas.update(item)
                return item
        return datas
#				print "\n\n\n",tmp,"\n\n\n"
#		print "\t\n",len(result),"\t\n"

        # logging.log(logging.INFO,"Page:%s,fetch %d links,get %d items",link,len(links),len(result))
        # return result
