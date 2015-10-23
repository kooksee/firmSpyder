# -*- coding: UTF-8 -*-

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.selector import Selector
from mycrawler.items import BasicItem
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sets import Set
import logging
import scrapy


class VipaSpider(Spider):
    name = "vipa"
    timeout = 8
    trytimes = 3
    start_urls = ["http://www.vipa.com/en/service-support/downloads/firmware"]
    # must be lower character
    typefilter = ["txt", "pdf"]
    allsuffix = Set()

    def parse(self, response):
        request = scrapy.Request(response.url, callback=self.parse_page)
        request.meta["prototype"] = BasicItem()
        request.meta["prototype"]["Info"] = {}
        request.meta["prototype"]["Firm"] = "Vipa"
        yield request

    def parse_page(self, response):
        lines = response.selector.xpath(
            "//div[@id='sbfolderdownloadWrap']/div/div/a")
        prototype = response.meta['prototype']
        dirs = response.selector.xpath(
            "//div[@id='sbfolderFolderWrap']/div[@class='sbfolderFolder']/a/@href").extract()
        for i in dirs:
            request = scrapy.Request(
                response.urljoin(i), callback=self.parse_page)
            request.meta["prototype"] = response.meta["prototype"]
            yield request
        for a in lines:
            filename = a.xpath("text()").extract().pop()
            filetype = filename.rsplit(".", 1).pop().strip().lower()
            VipaSpider.allsuffix.add(filetype)
            if not filetype in VipaSpider.typefilter:
                item = BasicItem()
                item["Firm"] = "Vipa"
                item["Link"] = response.urljoin(
                    a.xpath("@href").extract().pop())
                item["Rawlink"] = item["Link"].split("&", 1)[0]
                item["Filename"] = filename
                item["Title"] = item["Filename"]
                item["Descr"] = str().join(
                    a.xpath("//div[@class='up']//text()").extract())
                item["Info"] = {}
                yield item
