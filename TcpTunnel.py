#coding=utf8
#codeby ydhcui
#tcp端口复用程序
import socket
from threading import Thread
import sys,os,re

ROUTES = [
   #(服务,(主机,端口),是否关闭连接,是否接收完成再发送,发包规则,路由规则)
    ('HTTP',  ('127.0.0.1',    8081 ), True , True , {1:1} , b'^(GET|POST)'),
    ('JRMP',  ('127.0.0.1',    8009 ), False, False, {2:2} , b'^JRMI'),
    ('NC'  ,  ('127.0.0.1',    51   ), False, False, {1:1} , b'.*?')
]

class TcpTunnel(Thread):
    SOCKS = {}
    def __init__(self,client,clientaddr):
        Thread.__init__(self)
        self.client = client
        self.clientaddr = clientaddr
        self.sock = self.SOCKS[client] if client in self.SOCKS else socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.isclose = True
        self.recont = {1:1}
        self.isrecvall = True

    def run(self):
        i = 0
        while True:
            buff = self.client.recv(10240)
            if not buff:
                break
            i += 1
            if self.client not in self.SOCKS:
                for service,addr,isclose,isrecvall,recont,signs in ROUTES:
                    if re.search(signs,buff,re.IGNORECASE):
                        print('Create route %s <--> %s'%(str(addr),str(self.clientaddr)))
                        self.isclose = isclose
                        self.recont = recont
                        self.isrecvall = isrecvall
                        self.sock.connect(addr)
                        break
                self.SOCKS[self.client] = self.sock
            if i in self.recont:
                for k in range(self.recont[i]-1):
                    buff += self.client.recv(10240)
            #print('recv',buff)
            self.sock.sendall(buff)
            data = b''
            while True:
                buff = self.sock.recv(10240)
                if not buff:
                    break
                if self.isrecvall:
                    data += buff
                else:
                    data = buff
                    break
            #print('send',data)
            self.client.sendall(data)
            if self.isclose:
                self.client.close()
                self.sock.close()
                break

class SockProxy(object):
    def __init__(self,host='0.0.0.0',port=53,listen=20):
        self.host = host
        self.port = port
        self.listen = listen
        self.clientsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clientsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientsock.bind((self.host,self.port))

    def start(self):
        self.clientsock.listen(self.listen)
        print('Start Proxy Listen - %s:%s'%(self.host,self.port))
        while True:
            client,addr = self.clientsock.accept()
            T = TcpTunnel(client,addr)
            T.start()

if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except:
        port = 1222
    try:
        c = SockProxy('0.0.0.0',port)
        c.start()
    except KeyboardInterrupt:
        sys.exit()
