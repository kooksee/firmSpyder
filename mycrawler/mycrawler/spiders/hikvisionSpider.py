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
class HikvisionSpider(Spider):
	name="hikvision"
	start_urls= [
		"http://www.hikvision.com/cn/download_more_871.html",
		"http://www.hikvision.com/cn/download_more_607.html",
		"http://www.hikvision.com/cn/download_more_699.html",
		"http://www.hikvision.com/cn/download_more_714.html",
	]
	timeout=5
	trytimes=3
	ajaxlink="http://www.hikvision.com/ashx/xzs2015.ashx?type=0&id="
	

	def parse(self,response):

		link=response.url
		browser=webdriver.Firefox()
		browser.implicitly_wait(HikvisionSpider.timeout)
		browser.set_page_load_timeout(HikvisionSpider.timeout)
		try:
			browser.get(link)
		except TimeoutException:
			pass
		
		element=WebDriverWait(browser,HikvisionSpider.timeout).until(EC.presence_of_element_located((By.CLASS_NAME,"doxx")))
		lines=element.find_elements_by_class_name("doxx2")
		items=Set()
		for l in lines:
			t=HikvisionSpider.trytimes
			while 1:
				try:
					did=l.find_element_by_xpath("a").get_attribute("name")
					nbrowser=webdriver.Firefox()
					nbrowser.set_page_load_timeout(HikvisionSpider.timeout)
					try:
						nbrowser.get(HikvisionSpider.ajaxlink+did)
					except TimeoutException:
						pass
					rawlink=nbrowser.find_element_by_xpath("//body").text
#			print rawlink
#			continue
					item=BasicItem()
					item["Firm"]="Hikvision"
					item["Info"]={}
					item["Link"]="http://download.hikvision.com/"+rawlink
					item["Rawlink"]=item["Link"]
					item["Filename"]=rawlink.rsplit("/",1).pop()
					item["Title"]=l.find_element_by_class_name("doxx4").text
					item["Descr"]=l.find_element_by_class_name("doxx10").text
				except Exception,e:
					nbrowser.quit()
					t-=1
					if t==0:
						logging.exception(e)
						break
				else:
					nbrowser.quit()
					items.add(item)
					break
		browser.quit()
		return items
