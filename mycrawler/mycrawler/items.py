# -*- coding: UTF-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
class BasicItem(scrapy.Item):
	id=scrapy.Field()
	Firm=scrapy.Field()
	Title=scrapy.Field()
	Link=scrapy.Field()
	Rawlink=scrapy.Field()
	Filename=scrapy.Field()
	Descr=scrapy.Field()
	Info=scrapy.Field()
	Status=scrapy.Field()



