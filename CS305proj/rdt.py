from USocket import UnreliableSocket
from socket import socket, AF_INET, SOCK_DGRAM
import threading
import time
import random


class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)

    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode. 
    https://docs.python.org/3/library/socket.html#socket-timeouts

    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.debug = debug

        self.host = '127.0.0.1'
        self.port = 9999
        self.buff_size = 1024
        self.server_addr = ''
        self.client_addr = ''
        self.sock = socket(AF_INET, SOCK_DGRAM)

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def accept(self):
        """
        Accept a connection. The socket must be bound to an address and listening for 
        connections. The return value is a pair (conn, address) where conn is a new 
        socket object usable to send and receive data on the connection, and address 
        is the address bound to the socket on the other end of the connection.

        This function should be blocking. 
        """
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        # get syn
        data, addr = self.sock.recvfrom(self.buff_size)
        self.client_addr = addr
        if self.debug:
            print('receive from {}: {}'.format(addr, data))
        msg = Message()
        ret = msg.to_message(data)
        if msg.get_checksum() != msg.checksum:
            print('checksum error')
            return None, None
        # send ack
        msg.ack = msg.syn + 1
        syn = random.randint(0, 8)
        msg.syn = syn
        self.sock.sendto(msg.to_byte(), addr)
        if self.debug:
            print('send to {}: {}'.format(addr, msg.to_byte()))
        # get ack
        data, addr = self.sock.recvfrom(self.buff_size)
        if self.debug:
            print('receive from {}: {}'.format(addr, data))
        msg = Message()
        ret = msg.to_message(data)
        if not ret:
            print('message error')
            return None, None
        if msg.get_checksum() != msg.checksum:
            print('checksum error')
            return None, None
        if msg.ack != syn + 1:
            print('check ack failed')
            return None, None
        if self.debug:
            print('accept successful!')

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return self, addr

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        # send syn
        msg = Message()
        syn = random.randint(0, 8)
        msg.syn = syn
        self.sock.sendto(msg.to_byte(), address)
        self.server_addr = address
        if self.debug:
            print('send to {}: {}'.format(address, msg.to_byte()))
        # wait ack
        data, addr = self.sock.recvfrom(self.buff_size)
        if self.debug:
            print('receive from {}: {}'.format(addr, data))
        ret = msg.to_message(data)
        if not ret:
            print('message error')
            return
        if msg.get_checksum() != msg.checksum:
            print('checksum error')
            return
        if msg.ack != syn + 1:
            print('check ack failed')
            return
        # send ack
        msg.ack = msg.syn + 1
        self.sock.sendto(msg.to_byte(), address)
        if self.debug:
            print('send to {}: {}'.format(address, msg.to_byte()))
        if self.debug:
            print('connect successful!')

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def recv(self, bufsize: int) -> bytes:
        """
        Receive data from the socket. 
        The return value is a bytes object representing the data received. 
        The maximum amount of data to be received at once is specified by bufsize. 

        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        data, addr = self.sock.recvfrom(bufsize + 30)
        if self._rate:
            time.sleep(len(data)/self._rate)
        if self.debug:
            print('receive from {}: {}'.format(addr, data))
        msg = Message()
        ret = msg.to_message(data)
        # check package size
        if not ret:
            print('message error')
            return
        # check sum
        if msg.get_checksum() != msg.checksum:
            print('checksum error')
            return
        # client close
        if not msg.payload:
            return
        # send seq ack
        payload = msg.payload
        msg.seqack = msg.seq + 1
        msg.payload = b''
        if self.client_addr:
            self.sock.sendto(msg.to_byte(), self.client_addr)
        else:
            self.sock.sendto(msg.to_byte(), self.server_addr)
        if self.debug:
            if self.client_addr:
                print('send to {}: {}'.format(self.client_addr, msg.to_byte()))
            else:
                print('send to {}: {}'.format(self.server_addr, msg.to_byte()))
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return payload

    def send(self, b: bytes):
        """
        Send data to the socket. 
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        length = len(b)
        msg = Message()
        msg.seq = random.randint(0, 8)
        msg.payload = b
        if self.client_addr:
            self.sock.sendto(msg.to_byte(), self.client_addr)
        else:
            self.sock.sendto(msg.to_byte(), self.server_addr)
        if self.debug:
            if self.client_addr:
                print('send to {}: {}'.format(self.client_addr, msg.to_byte()))
            else:
                print('send to {}: {}'.format(self.server_addr, msg.to_byte()))
        # get seq ack package
        data, addr = self.sock.recvfrom(self.buff_size)
        if self.debug:
            print('receive from {}: {}'.format(addr, data))
        msgr = Message()
        ret = msgr.to_message(data)
        # check package size
        if not ret:
            print('message error')
            return
        # check sum
        if msg.get_checksum() != msg.checksum:
            print('checksum error')
            return
        # check seq ack
        if msgr.seqack != msg.seq + 1:
            print('seq error')
            
        

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        if self.server_addr:
            msg = Message()
            self.sock.sendto(msg.to_byte(), self.server_addr)
        self.sock.close()
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()

    def set_send_to(self, send_to):
        self._send_to = send_to

    def set_recv_from(self, recv_from):
        self._recv_from = recv_from


"""
You can define additional functions and classes to do thing such as packing/unpacking packets, or threading.

"""


class Message():
    def __init__(self):
        self.syn = 0
        self.fin = 0
        self.ack = 0
        self.seq = 0
        self.seqack = 0
        self.len = 0
        self.checksum = 0
        self.payload = b''

    def to_byte(self):
        self.len = len(self.payload)
        self.checksum = self.get_checksum()
        msg = '{}{}{}{:0>4d}{:0>4d}{:0>4d}{:0>2d}'.format(
            self.syn,
            self.fin,
            self.ack,
            self.seq,
            self.seqack,
            self.len,
            self.checksum)
        return msg.encode('utf-8') + self.payload

    def to_message(self, msg):
        try:
            self.payload = msg[17:]
            msg = msg.decode('utf-8')
            self.syn = int(msg[0])
            self.fin = int(msg[1])
            self.ack = int(msg[2])
            self.seq = int(msg[3:7])
            self.seqack = int(msg[7:11])
            self.len = int(msg[11:15])
            self.checksum = int(msg[15:17])
            return True
        except:
            return False

    def get_checksum(self):
        sum = (self.syn * 11
               + self.fin * 13
               + self.ack * 17
               + self.seq * 19
               + self.seqack * 23
               + self.len * 29)
        payload = self.payload
        if type(self.payload) == str:
            payload = payload.encode('utf-8')
        for ch in payload:
            sum += ch * 31
        return sum % 100
