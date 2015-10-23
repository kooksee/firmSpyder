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


class OpenwrtSpider(Spider):
    name = "openwrt"
    timeout = 8
    trytimes = 3
    start_urls = [
        "http://downloads.openwrt.org.cn/OpenWrt-DreamBox/",
        "http://downloads.openwrt.org.cn/PandoraBox/",
        "http://downloads.openwrt.org.cn/openwrtcn_img/",
        "http://downloads.openwrt.org.cn/ar_series_img/",
        "http://downloads.openwrt.org.cn/zjhzzyf_img/",
    ]

    # must be lower character
    suffix = ["bin", "bix", "trx", "img", "dlf", "tfp", "rar", "zip"]
    allsuffix = Set()

    def parse(self, response):
        request = scrapy.Request(response.url, callback=self.parse_page)
        request.meta["prototype"] = BasicItem()
        request.meta["prototype"]["Info"] = {}
        request.meta["prototype"]["Firm"] = "Openwrt"
        yield request

    def parse_page(self, response):
        r = response.selector.xpath(
            "//pre").re("<a[ ]*href=\"(.*)\".*>.*</a>[ ]*(.*:[0-9]{2}).*\r\n")
        i = 0
        prototype = response.meta['prototype']
        prototype["Title"] = response.selector.xpath(
            "//h1/text()").extract().pop()
        while i < len(r):
            if r[i][-1] == "/":
                request = scrapy.Request(
                    response.url + r[i], callback=self.parse_page)
                request.meta["prototype"] = response.meta["prototype"]
                yield request
            elif r[i].rsplit(".").pop() in OpenwrtSpider.suffix:
                item = BasicItem(prototype)
                item["Filename"] = r[i]
                item["Link"] = response.url + r[i]
                item["Rawlink"] = item["Link"]
                item["Info"]["Date"] = r[i + 1]

                yield item

            i += 2

        return
