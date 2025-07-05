import os
from socket import *
import socket
import threading
import time
import sys
import logging
import ssl




from http import HttpServer

httpserver = HttpServer()


class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		while True:
			# logging.warning("menunggu data dari client")
			try:
				# logging.warning("menerima data dari client")
				data = self.connection.recv(32)
				# logging.warning("data dari client: {}" . format(data))
				if data:
					# logging.warning("data diterima dari client: {}" . format(data))
					#merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n\r\n
					d = data.decode('utf-8', errors='surrogateescape')
					rcv=rcv+d
					# logging.warning("data yang diterima: {}" . format(rcv))
					if '\r\n\r\n' in rcv:
						#end of command, proses string
						
						# Check if there is header content length
						content_length = 0
						for line in rcv.split("\r\n"):
							if line.lower().startswith("content-length:"):
								try:
									content_length = int(line.split(":", 1)[1].strip())
								except ValueError:
									content_length = 0
								break
						# If there is a body, read until full body is received
						if content_length > 0:
							headers_end = rcv.find("\r\n\r\n") + 4
							body = rcv[headers_end:]
							while len(body.encode('utf-8', errors='surrogateescape')) < content_length:
								data = self.connection.recv(32)
								if not data:
									break
								d = data.decode('utf-8', errors='surrogateescape')
								body += d
							rcv = rcv[:headers_end] + body

						hasil = httpserver.proses(rcv)
						#hasil akan berupa bytes
						#untuk bisa ditambahi dengan string, maka string harus di encode
						hasil=hasil+"\r\n\r\n".encode()
						#logging.warning("balas ke  client: {}" . format(hasil))
						#hasil sudah dalam bentuk bytes
						self.connection.sendall(hasil)
						rcv=""
						self.connection.close()
						return
				else:
					break
			except OSError as e:
				pass
		self.connection.close()
		return



class Server(threading.Thread):
	def __init__(self,hostname='testing.net'):
		self.the_clients = []
#------------------------------
		self.hostname = hostname
		cert_location = os.getcwd() + '/certs/'
		self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
		self.context.load_cert_chain(certfile=cert_location + 'domain.crt',
									 keyfile=cert_location + 'domain.key')
#---------------------------------
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0', 8889))
		self.my_socket.listen(1)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			try:
				self.secure_connection = self.context.wrap_socket(self.connection, server_side=True)
				logging.warning("connection from {}".format(self.client_address))
				clt = ProcessTheClient(self.secure_connection, self.client_address)
				clt.start()
				self.the_clients.append(clt)
			except ssl.SSLError as essl:
				print(str(essl))




def main():
	svr = Server()
	svr.start()

if __name__=="__main__":
	main()