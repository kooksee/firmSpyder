# -*- coding: utf-8 -*-
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from mycrawler.dbUtil import download_process, all_firm
import time


def process_download():
    while 1:
        print '厂商    已爬取    已下载'
        pp = list(download_process())
        for p in pp[0:]:
            print '%-10s%-10s%s' % (p[0], p[1], p[2])

        a = all_firm()
        print '总计:%9s%7s' % (a[0], a[1])
        sys.stdout.flush()
        time.sleep(5)
        os.system('clear')

        if a[0] == a[1]:
            print "已经下载完毕"
            break

process_download()
