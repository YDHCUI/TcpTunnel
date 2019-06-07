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
        'name'      :'HTTP',
        'addr'      :('47.98.160.198',8315),
        'route'     :b'^(GET|POST)',
        'hack'      :HttpHack,
    },{
        'name'      :'JRMP',
        'addr'      :('47.98.160.198',8009),
        'route'     :b'^JRMI',
        'hack'      :Hack,
    },{
        'name'      :'SSH',
        'addr'      :('47.98.160.198',22),
        'route'     :b'^SSH',
        'hack'      :Hack,
    },{
        'name'      :'RDP',
        'addr'      :('112.124.12.101',3389),
        'route'     :b'^\x03\x00\x00',
        'hack'      :Hack,
    },{
        'name'      :'PostgreSQL',
        'addr'      :('127.0.0.1',5432),
        'route'     :b'^\x00\x00\x00\x08\x04',
        'hack'      :Hack,
    },{
        'name'      :'Oracle',
        'addr'      :('127.0.0.1',1521),
        'route'     :b'^\x00(\xec|\xf1)\x00\x00\x01\x00\x00\x00\x019\x01',
        #'route'     :b'\(DESCRIPTION=\(CONNECT_DATA=\(SERVICE_NAME=',
        'hack'      :Hack,
    },{
        'name'      :'MSSQL',
        'addr'      :('127.0.0.1',1433),
        'route'     :b'^\x12\x01\x00',
        'hack'      :Hack,
    },{
        'name'      :'NC',
        'addr'      :('127.0.0.1',51),
        'route'     :b'.*',
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
        self.iskeep  = True

    def s(self,dstsock,srcsock):
        while self.iskeep:
            try:
                buff = dstsock.recv(10240)
            except Exception as e:
                break
            buff = self.hack.response(buff)
            #print('recv',buff)
            srcsock.sendall(buff)
            if not buff:
                self.iskeep = False
                break
        srcsock.close()

    def run(self):
        while self.iskeep:
            try:
                buff = self.srcsock.recv(10240)
            except Exception as e:
                break
            if not buff:
                self.iskeep = False
                break
            if self.srcsock not in self.SOCKS:
                for value in ROUTES:
                    if re.search(value['route'],buff,re.IGNORECASE):
                        print('[+]Connect %s%s <--> %s'%(value['name'],str(value['addr']),str(self.srcaddr)))
                        self.hack = value['hack'](self.srcaddr,value['addr'])
                        self.dstsock.connect(value['addr'])
                        break
                self.SOCKS[self.srcsock] = self.dstsock
                Thread(target=self.s,args=(self.dstsock,self.srcsock,)).start()
            buff = self.hack.request(buff)
            #print('send',buff)
            self.dstsock.sendall(buff)
        self.dstsock.close()
        print('[+]DisConnect %s%s <--> %s'%(value['name'],str(value['addr']),str(self.srcaddr)))

class SockProxy(object):
    def __init__(self,host='0.0.0.0',port=1111,listen=100):
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
