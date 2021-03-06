#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import urllib2
import pymongo
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import urllib
import time
from mycrawler.settings import firmlist_fc, MONGO_URI

from multiprocessing.dummy import Pool as ThreadPool
import threading
import cPickle
from collections import namedtuple
from urlparse import urlsplit
import multiprocessing


conn = pymongo.MongoClient(MONGO_URI)
db = conn.firmware  # 使用数据库名为firmware
collection = db.scrapy_items  # 使用集合scrapy_items


dirs_root = "./media/ubuntu/Elements/test/"
file_size = 104857600  # 默认文件大小是100m
# 加header，模拟浏览器
header = {
    'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0"}


# global lock
lock = threading.Lock()


# default parameters
defaults = dict(
    thread_count=10,
    buffer_size=500 * 1024,
    block_size=100 * 1024)


def progress(percent, width=50):
    print "%s %d%%\r" % (('%%-%ds' % width) % (width * percent / 100 * '='), percent),
    if percent >= 100:
        print
        sys.stdout.flush()


def write_data(filepath, data):
    with open(filepath, 'wb') as output:
        cPickle.dump(data, output)


def read_data(filepath):
    with open(filepath, 'rb') as output:
        return cPickle.load(output)


FileInfo = namedtuple('FileInfo', 'url name size lastmodified')


def get_file_info(cur):

    res = urllib2.urlopen(urllib2.Request(
        cur['Link'], None, header), timeout=10)
    size = int(res.headers.get('content-length', 0))

    # 判断文件是否大于100m，大于的话，舍弃不下载
    if size >= file_size:
        collection.remove({"_id": cur['_id']})
        return

    lastmodified = res.headers.get('last-modified', '')
    return FileInfo(cur['Link'],
                    os.path.join(dirs_root,
                                 cur['Firm'],
                                 cur['Filename']), size, lastmodified)


def download(cur,
             thread_count=defaults['thread_count'],
             buffer_size=defaults['buffer_size'],
             block_size=defaults['block_size']):
    # get latest file info

    # print cur
    trytime = 3
    while trytime > 0:
        try:
            req = urllib2.Request(cur['Link'], None, header)
            rep = urllib2.urlopen(req, timeout=10)  # 回复超过十秒超时
            print "code", rep.code
            break
        except Exception, e:
            print e
            trytime -= 1
            print "下载", cur['Filename']
            print "超时次数：%d" % (3 - trytime)
    else:
        # collection.remove({"_id": cur['_id']})
        return

    if not get_file_info(cur):
        return

    file_info = get_file_info(cur)
    # init path
    output = file_info.name
    workpath = '%s.ing' % output
    infopath = '%s.inf' % output

    # split file to blocks. every block is a array [start, offset, end],
    # then each greenlet download filepart according to a block, and
    # update the block' offset.
    blocks = []

    if os.path.exists(infopath):
        # load blocks
        _x, blocks = read_data(infopath)
        if (_x.url != file_info.url or
                _x.name != file_info.name or
                _x.lastmodified != file_info.lastmodified):
            blocks = []

    if not len(blocks):
        # set blocks
        if block_size > file_info.size:
            blocks = [[0, 0, file_info.size]]
        else:
            block_count, remain = divmod(file_info.size, block_size)
            blocks = [[i * block_size, i * block_size,
                       (i + 1) * block_size - 1] for i in range(block_count)]
            blocks[-1][-1] += remain
        # create new blank workpath
        with open(workpath, 'wb') as fobj:
            fobj.write('')

    # start monitor
    threading.Thread(target=_monitor, args=(
        infopath, file_info, blocks)).start()

    print "开始下载", file_info.name
    with open(workpath, 'rb+') as fobj:
        args = [(file_info.url, blocks[i], fobj, buffer_size)
                for i in range(len(blocks)) if blocks[i][1] < blocks[i][2]]

        if thread_count > len(args):
            thread_count = len(args)

        pool = ThreadPool(thread_count)
        pool.map(_worker, args)
        pool.close()
        pool.join()
    print "完成下载", file_info.name

    try:
        # rename workpath to output
        if os.path.exists(output):
            os.remove(output)
        os.rename(workpath, output)

        # delete infopath
        if os.path.exists(infopath):
            os.remove(infopath)

        if not all([block[1] >= block[2] for block in blocks]):
            return
    except:
        return

    return True


def _worker((url, block, fobj, buffer_size)):

    req = urllib2.Request(url, None, header)
    req.headers['Range'] = 'bytes=%s-%s' % (block[1], block[2])
    res = urllib2.urlopen(req)

    while 1:
        chunk = res.read(buffer_size)
        if not chunk:
            break
        with lock:
            fobj.seek(block[1])
            fobj.write(chunk)
            block[1] += len(chunk)


def _monitor(infopath, file_info, blocks):
    while 1:
        with lock:
            percent = sum([block[1] - block[0]
                           for block in blocks]) * 100 / file_info.size
            progress(percent)
            if percent >= 100:
                break
            write_data(infopath, (file_info, blocks))
        time.sleep(2)


def download_url(cur):

    if not cur.has_key('Link'):  # 判断是否有Link这个属性，没有直接输出“no link”
        print "no link"
        return

    if not cur.has_key('Firm'):  # 判断是否有Firm属性
        print "no Firm"
        return

    if not cur.has_key('Filename'):  # 判断是否有filename属性
        print "no Filename"
        return

    name = cur['Filename']  # 把文件名赋值给name
    mylink = cur['Link']  # 把link赋值给mylink
    firmname = cur['Firm']  # 把firm赋值给firmname

    ids = cur["_id"]  # 把_id赋值给ids
    dirs = os.path.join(dirs_root, firmname)  # 在FIRMWARE下根据厂商名建立新文件夹
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    filename = os.path.join(dirs, name)  # 定义文件的绝对路径
    # 判断文件是否已经存在，若不存在，继续下载，若存在，输出路径不下载
    if os.path.exists(filename):
        print filename, '已经存在'  # 已经下载过的文件，修改status值
        collection.update({'_id': ids}, {"$set": {'Status': 0}})
        return

    if not download(cur):
        return

    collection.update({'_id': ids}, {
        "$set": {
            'Path': filename,
            'Status': 0,
            'Firmtype': firmname in firmlist_fc and'FactoryControl' or 'Not_FactoryControl'}})
    return True


def download1():

    while 1:
        while collection.find({'Status': 2}).count() > 0:
            print "Status:2"
            import random
            r_d = random.sample(
                list(collection.find({'Status': 2})), 3)

            if not len(r_d):
                break

            for r in r_d[0:-1]:
                multiprocessing.Process(
                    target=download_url, args=(r,)).start()

            multiprocessing.Process(
                target=download_url, args=(r,)).start()

            download_url(r_d[-1])
            print "Status:1"
            download_url(collection.find_one({'Status': 1}))

        else:
            for cur in collection.find({'Status': 1}).limit(10):
                print "Status:1"
                download_url(cur)

            if collection.find({'Status': {'$gt': 0}}).count() == 0:
                return
download1()

# # 使用多线程
# import threadpool
# while collection.find({'Status': 2}).count() > 0:
#     print "下载低优先级"
#     tpool = threadpool.ThreadPool(10)
#     requests = threadpool.makeRequests(
#         download_url, collection.find({'Status': 2}))
#     [tpool.putRequest(req) for req in requests]
#     tpool.wait()
#     print "优先级低的下载完毕"
# print "所有下载完毕"
# 是否filename这个绝对路径，没有的话新建，并打开
# urllib.urlretrieve(mylink, filename, callbackfunc)
# with open(filename, "ab+") as foo:
#     for f in response.readlines():
#         sys.stdout.write(".")
#         foo.write(f)  # 把str中的内容写进filename这个文件夹中


# response = urllib2.urlopen(urllib2.Request(
# mylink, None, header), timeout=30)  # 回复超过十秒超时
# 根据response header中的“content-length"判断文件大小

# if response.headers.has_key("content-length"):
#     # 判断文件是否大于100m，大于的话，舍弃不下载
#     size = int(response.headers["content-length"])
#     if size >= file_size:
#         collection.remove({"_id": ids})
#         return

# print "开始下载", name

# cur = collection.find({'Status': 1})
# a = cur.count()
# print a
# i = 0
# for i in range(0, a):
#     print i
#     if (cur[i].has_key('Link')):
#         # print  "have link"

#         # print mylink
#         if (cur[i].has_key('Firm')):

#             # print firmname
#             if(cur[i].has_key('Filename')):
#                 name = cur[i]['Filename']
#                 print "all count is  %s" % a
#                 print "now is %s" % i
#                 print name
#                 mylink = cur[i]['Link']
#                 print mylink
#                 firmname = cur[i]['Firm']
#                 ids = cur[i]["_id"]

#                 dirs = dirs_root + "%s" % firmname
#                 if os.path.exists(dirs) == False:
#                     os.makedirs(dirs)
#                 # else:
#                 #	print"have this folder "
#                 filename = dirs + "/" + name
#                 print filename

#                 if os.path.exists(filename) == False:
#                     #foo1 =open(filename,'w')
#                     #threadpool foo1.close()
#                     request = urllib2.Request(mylink, None, header)
#                     # response=requests.get(mylink)
#                     try:
#                         response = urllib2.urlopen(request)
#                         try:
#                             # response=requests.get(mylink)
#                             Size = response.headers["content-length"]
#                             Size = int(Size)
#                             print Size
#                             if Size < 104857600:
#                                 str = response.read()
#                                 print "下载"
#                                 print name
#                                 print mylink
#                                 foo = open(filename, "wb")
#                                 foo.write(str)
#                                 print "下载成功"
#                                 print "\n"
#                                 foo.close()
#                                 if firmname in firmlist_fc:
#                                     print "It  is   FactoryControl_firm"
#                                     collection.update({'_id': ids}, {
#                                                       "$set": {'Path': filename, 'Status': 0, 'Firmtype': 'FactoryControl'}})
#                                 else:
#                                     collection.update({'_id': ids}, {
#                                                       "$set": {'Path': filename, 'Status': 0, 'Firmtype': 'Not_FactoryControl'}})

#                             else:
#                                 collection.remove({"_id": ids})
#                                 print " remove  success!"
#                         except:
#                             print"no Size"
#                             str = response.read()
#                             print "下载"
#                             print name
#                             print mylink
#                             foo = open(filename, "wb")
#                             foo.write(str)
#                             print "下载成功"
#                             print "\n"
#                             foo.close()
#                             if firmname in firmlist_fc:
#                                 print "It  is   FactoryControl_firm"
#                                 collection.update({'_id': ids}, {
#                                                   "$set": {'Path': filename, 'Status': 0, 'Firmtype': 'FactoryControl'}})
#                             else:
#                                 collection.update({'_id': ids}, {
#                                                   "$set": {'Path': filename, 'Status': 0, 'Firmtype': 'Not_FactoryControl'}})

#                     except Exception, e:
#                         print e
#                 else:
#                     print "file path is" + filename
#                     collection.update({'_id': ids}, {
#                                       "$set": {'Path': filename, 'Status': 0, 'Firmtype': 'FactoryControl'}})
#             else:
#                 print "no Filename"
#         else:
#             print "no Firm"
#     else:
#         print "no link"

# print "low status download over"


# print "ALL FIRMWARE  DOWMLOAD OVER"
