from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

httpserver = HttpServer()

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#untuk menggunakan processpoolexecutor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection,address):
		rcv=""
		while True:
			# logging.warning("menunggu data dari client")
			try:
				# logging.warning("menerima data dari client")
				data = connection.recv(32)
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
								data = connection.recv(32)
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
						connection.sendall(hasil)
						rcv=""
						connection.close()
						return
				else:
					break
			except OSError as e:
				pass
		connection.close()
		return



def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8889))
	my_socket.listen(1)

	with ProcessPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				#logging.warning("connection from {}".format(client_address))
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				#menampilkan jumlah process yang sedang aktif
				jumlah = ['x' for i in the_clients if i.running()==True]
				print(jumlah)





def main():
	Server()

if __name__=="__main__":
	main()

