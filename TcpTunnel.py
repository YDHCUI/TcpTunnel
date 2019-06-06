#coding = utf-8
#codeby ydhcui
import socket
import sys
import os
import re
from threading import Thread

class Hack(object):
    def __init__(self,src_addr=None,dst_addr=None):
        self.src_addr = src_addr
        self.dst_addr = dst_addr

    def request(self,data):
        return data

    def response(self,data):
        return data

class HttpHack(Hack):
    def request(self,data):
        data = re.sub('Host:.*?\r\n','Host: %s:%s\r\n'%(self.dst_addr),data.decode())
        return data.encode()

ROUTES = [
    {
        'name'      :'HTTPS',
        'addr'      :('127.0.0.1',443),
        'route'     :b'^CONNECT',
        'hack'      :Hack,
    },{
        'name'      :'HTTP',
        'addr'      :('47.98.160.198',8315),
        'route'     :b'^(GET|POST)',
        'hack'      :HttpHack,
    },{
        'name'      :'JRMP',
        'addr'      :('127.0.0.1',8009),
        'route'     :b'^JRMI',
        'hack'      :Hack,
    },{
        'name'      :'SSH',
        'addr'      :('47.98.160.198',22),
        'route'     :b'^SSH',
        'hack'      :Hack,
    },{
        'name'      :'NC',
        'addr'      :('127.0.0.1',51),
        'route'     :b'.*?',
        'hack'      :Hack,
    }
]

class TcpTunnel(Thread):
    SOCKS = {}
    def __init__(self,srcsock,srcaddr):
        Thread.__init__(self)
        self.srcsock = srcsock
        self.srcaddr = srcaddr
        self.dstsock = self.SOCKS[srcsock] if srcsock in self.SOCKS else socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    def s(self,dstsock,srcsock):
        while True:
            buf=dstsock.recv(10240)
            srcsock.sendall(buf)
            if not buf:
                break
        dstsock.close()

    def run(self):
        while True:
            buff = self.srcsock.recv(10240)
            if not buff:
                break
            if self.srcsock not in self.SOCKS:
                for value in ROUTES:
                    if re.search(value['route'],buff,re.IGNORECASE):
                        print('Create %s%s <--> %s'%(value['name'],str(value['addr']),str(self.srcaddr)))
                        self.hack = value['hack'](self.srcaddr,value['addr'])
                        self.dstsock.connect(value['addr'])
                        break
                self.SOCKS[self.srcsock] = self.dstsock
                Thread(target=self.s,args=(self.dstsock,self.srcsock,)).start()
            self.dstsock.sendall(buff)
        self.srcsock.close()

class SockProxy(object):
    def __init__(self,host='0.0.0.0',port=53,listen=100):
        self.host = host
        self.port = port
        self.listen = listen
        self.socks = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socks.bind((self.host,self.port))

    def start(self):
        self.socks.listen(self.listen)
        print('Start Proxy Listen - %s:%s'%(self.host,self.port))
        while True:
            sock,addr = self.socks.accept()
            T = TcpTunnel(sock,addr)
            T.start()

if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except:
        port = 1111
    try:
        c = SockProxy('0.0.0.0',port)
        c.start()
    except KeyboardInterrupt:
        sys.exit()
