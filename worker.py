#!/usr/bin/env python
# -*- coding: utf8 -*-

import Queue
import threading
import requests
import lxml.html
import urlparse


class ProducerThread(threading.Thread):
    """request host"""
    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue

    def run(self):
        while True:
            host = self.queue.get()

            try:
                response = requests.get(host)
            except requests.exceptions.ReadTimeout:
                print('ERROR. Read timeout occured')
            except requests.exceptions.ConnectTimeout:
                print('ERROR. Connection timeout occured!')
            except requests.exceptions.ConnectionError:
                print('ERROR. Seems like dns lookup failed..')
            except requests.exceptions.HTTPError as err:
                print('ERROR. HTTP Error occured')
                print('Response is: {content}'.format(content=err.response.content))

            self.out_queue.put(response)
            self.queue.task_done()


class ConsumerThread(threading.Thread):
    """data parser"""
    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.found_links = set()

    def run(self):
        while True:
            self.found_links = set()
            response = self.out_queue.get()

            parsed_body = lxml.html.fromstring(response.content)
            print '\ntitle -->', parsed_body.xpath('//title/text()')

            links = [urlparse.urljoin(response.url, url)   \
                for url in parsed_body.xpath('//a/@href') ]

            for link in links:
                if link.startswith(u'http'):
                    self.found_links.add(link)

            print '    links -->'
            x = 0
            for row in self.found_links:
                x += 1
                print '    %d  %s' % (x, row)

            print '------------------'
            self.out_queue.task_done()


def main():
    HOSTS = ["http://yandex.ru", "http://txodds.com",
        "http://opennet.ru", "http://example.com"]

    queue = Queue.Queue()
    out_queue = Queue.Queue()

    for host in HOSTS:
        queue.put(host)

    pt = ProducerThread(queue, out_queue)
    pt.setDaemon(True)
    pt.start()

    ct = ConsumerThread(out_queue)
    ct.setDaemon(True)
    ct.start()

    queue.join()
    out_queue.join()


main()

