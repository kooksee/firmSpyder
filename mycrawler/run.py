# encoding=utf-8
import os
import multiprocessing
from cmd import Cmd
from mycrawler.dbUtil import DbUtil
import signal
import commands


# 下载监控


def run_download_watch():
    os.system("gnome-terminal -x bash -c 'python ./download_process.py' ")


# 下载文件
def run_download():
    os.system("gnome-terminal -x bash -c 'python ./download.py' ")


# 爬虫
def run_spider(arg):
    for i in range(len(arg)):
        os.system("gnome-terminal -x bash -c 'scrapy crawl %s'" % arg[i])


def run_s(arg):
    os.system("gnome-terminal -x bash -c 'scrapy crawl %s'" % arg)


def print_spider():
    spyder = [
        (0, 'rockwell'), (5, 'vipa'),
        (1, 'abb'), (6, 'hikvision'),
        (2, 'foscam'), (7, 'tplink'),
        (3, 'schneider'), (8, 'dlink'),
        (4, 'openwrt'), (9, '爬取所有厂商'),
        ('d', '下载'), ('p', '监控'),
        ('q', '退出系统'), ('', '')
    ]
    for i in range(0, len(spyder) - 4, 2):
        print "          %-s:%-10s        %s:%-10s" % (spyder[i][0], spyder[i][1], spyder[i + 1][0], spyder[i + 1][1])
    print "          d:下载    p:监控    q:退出系统"


class CLI(Cmd):

    def __init__(self):
        Cmd.__init__(self)
        # 设置命令提示符
        self.prompt = ">>> "
        self.doc_header = ''
        self.undoc_header = ''
        self.nohelp = "*** 命令%s没有帮助文档"

    def preloop(self):
        print '''
    --------------------------------------------------
    +-+-+-+-+-+-----欢迎进入爬虫控制台-----+-+-+-+-+-+
    --------------------------------------------------

    【说明】本爬虫框架可以爬取Schneider、Rockwell、Vipa、
    Abb、Hikvision、Foscam、TPlink、Dlink、Openwrt等
    多个厂商的固件，涉及PLC、MTU、HMI、Building HAVC、
    Router、Printer、Camera、Android、Ios、Switch等十多
    种设备类型。

    【帮助】执行爬虫系统时，输入相应数字，即可爬取对应
    厂商的固件。
    例如：输入“0”，即为爬取Schneider固件
'''
        print_spider()

    # emptyline
    def emptyline(self):
        os.system('clear')
        print_spider()

    def do_download(self, arg):
        '''    下载文件'''

        p2 = multiprocessing.Process(target=run_download)
        p2.start()

    def do_0(self, arg):
        multiprocessing.Process(target=run_s, args=('rockwell',)).start()

    def do_1(self, arg):
        multiprocessing.Process(target=run_s, args=('abb',)).start()

    def do_2(self, arg):
        multiprocessing.Process(target=run_s, args=('foscam',)).start()

    def do_3(self, arg):
        multiprocessing.Process(target=run_s, args=('schneider',)).start()

    def do_4(self, arg):
        multiprocessing.Process(target=run_s, args=('openwrt',)).start()

    def do_5(self, arg):
        multiprocessing.Process(target=run_s, args=('vipa',)).start()

    def do_6(self, arg):
        multiprocessing.Process(target=run_s, args=('hikvision',)).start()

    def do_7(self, arg):
        multiprocessing.Process(target=run_s, args=('tplink',)).start()

    def do_8(self, arg):
        multiprocessing.Process(target=run_s, args=('dlink',)).start()

    def do_9(self, arg):
        self.do_run_all_spiders(1)

    def do_d(self, arg):
        # 运行下载
        multiprocessing.Process(target=run_download).start()

    def do_p(self, arg):
        # 运行下载监控
        multiprocessing.Process(target=run_download_watch).start()

    def do_help(self, arg):

        def ddoc(ss, arg):
            try:
                doc = getattr(ss, 'do_' + arg).__doc__
                if doc:
                    print arg + ":"
                    print doc
                    return
            except AttributeError:
                ss.stdout.write("%s\n" % str(ss.nohelp % (arg,)))

        cmds_doc = []
        for name in self.get_names():
            if name[:3] == 'do_':
                cmds_doc.append(name[3:])

        print self.doc_header
        for c in cmds_doc:
            ddoc(self, c)

    # 添加新的爬虫连接
    def do_add(self, args):
        """    新增链接(厂商网址)到数据库中
    输入格式为:add name abb;start_urls www.baidu.com www.baidu.com www.baidu.com
    add是添加命令，后面的是参数。start_urls后面可以跟随多条数据，空格分开"""

        if not args:
            print "输入内容为空，请查看帮助：help add"
            return

        print args
        data = dict([(bb.split(' ')[0], len(bb.split(' ')[1:]) == 1 and bb.split(
            ' ')[1] or bb.split(' ')[1:]) for bb in args.split(';')])
        print data
        DbUtil().conn().collection('url_items').insert(data)

    # 列出所有的爬虫
    def do_list_spider(self, args):
        '''     列出所有的爬虫'''

        print commands.getoutput("scrapy list")

    # 运行一个爬虫
    def do_run_spider(self, arg):
        '''     运行一个爬虫，例如run_spider abb'''

        multiprocessing.Process(
            target=run_spider, args=(arg,)).start()

    def do_run(self, args):
        '''    运行所有的程序'''

        # 运行爬虫
        self.do_run_all_spiders(1)

        # 运行下载
        multiprocessing.Process(target=run_download).start()

        # 运行下载监控
        multiprocessing.Process(target=run_download_watch).start()

    # 运行所有的爬虫
    def do_run_all_spiders(self, arg):
        '''    运行所有的爬虫'''

        s = commands.getoutput("scrapy list").split('\n')
        if not s:
            print "没有爬虫，请检验代码是否正确"
            return

        multiprocessing.Process(
            target=run_spider, args=(s,)).start()

    def do_q(self, arg):
        '''    退出系统'''
        return True

    # 当无法识别输入的command时调用该方法
    def default(self, line):
        print '命令' + repr(line) + '不存在'
        #，请输入help查看命令帮助

    # 退出之后调用该方法
    def postloop(self):
        print '谢谢使用'

    def completedefault(self, *ignored):
        return ['add', 'run_spider', 'run_all_spiders', 'list_spider']


if __name__ == "__main__":
    cli = CLI()
    cli.cmdloop()
