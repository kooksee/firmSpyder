# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import md5
from settings import priority

class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            mongo_collection=crawler.settings.get('MONGO_COLLECTION', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # db[settings['MONGODB_COLLECTION']]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #		print "\n\t",self.mongo_uri,self.mongo_db
        #		print item

        if item["Firm"] in priority:
            item["Status"] = 2
        else:
            item["Status"] = 1
        mymd5 = md5.new(item["Rawlink"].encode("utf8"))
        item["id"] = mymd5.hexdigest()

        exist = self.db[self.mongo_collection].find_one(
            {"id": item.get('id'), "Status": {"$gte": 0}})
        if not exist:
            self.db[self.mongo_collection].update_one(
                {"id": item.get("id")}, {"$set": item}, True)
        return item
