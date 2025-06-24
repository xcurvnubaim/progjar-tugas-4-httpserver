import logging
import sys
import os.path
import uuid
from glob import glob
from datetime import datetime

logging.basicConfig(filename='httpserver.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.targetdir='./target/'
		if not os.path.exists(self.targetdir):
			os.makedirs(self.targetdir)
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'

	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		
		requests = data.split("\r\n")
		#print(requests)
		logging.info(f"Received request: {requests}")
		baris = requests[0]
		#print(baris)
		all_headers = [n for n in requests[1:] if n!=""]

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				# Ambil body dari request (setelah header kosong)
				body = ""
				if "" in requests:
					body_index = requests.index("")
					body = "\r\n".join(requests[body_index+1:])
				logging.info(f"POST request to {object_address} with body: {body}")
				return self.http_post(object_address, all_headers, body)
			if (method=='DELETE'):
				object_address = j[1].strip()
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})

	def http_get(self,object_address,headers):
		files = glob(self.targetdir + '*') #ambil semua file yang ada di targetdir
		#print(files)
		thedir='./'
		if (object_address == '/'):
			file_list = [os.path.basename(f) for f in files]
			body = "\n".join(file_list)
			return self.response(200, 'OK', body, {'Content-type': 'text/plain'})

		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())
		# Daftar file di direktori
		if (object_address == '/files'):
			file_list = [os.path.basename(f) for f in files]
			body = "\n".join(file_list)
			return self.response(200, 'OK', body, {'Content-type': 'text/plain'})
		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types.get(fext, 'application/octet-stream')
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)

	def http_post(self,object_address,headers,body):
		# Upload file ke server, endpoint: /upload?filename=namafile
		if object_address.startswith('/files'):
			import urllib.parse
			parsed = urllib.parse.urlparse(object_address)
			params = urllib.parse.parse_qs(parsed.query)
			# filename = params.get('filename', [None])[0]
			contentDisposition = next((h for h in headers if h.startswith('Content-Disposition:')), None)
			if contentDisposition:
				# Mengambil nama file dari header Content-Disposition
				filename = contentDisposition.split('filename=')[1].strip('"')
			else:
				filename = params.get('filename', [None])[0]
			# logging.info(f"filename: {filename}, contentDisposition: {contentDisposition}, headers: {headers}")
			if not filename:
				return self.response(400, 'Bad Request', 'Filename not specified', {})
			try:
				with open(self.targetdir + filename, 'wb') as f:
					f.write(body.encode('utf-8', errors='surrogateescape') if isinstance(body, str) else body)
				return self.response(200, 'OK', f'File {filename} uploaded', {})
			except Exception as e:
				return self.response(500, 'Internal Server Error', str(e), {})
		headers ={}
		isi = "kosong"
		return self.response(200,'OK',isi,headers)
	
	def http_delete(self,object_address,headers):
		# Hapus file, endpoint: /delete/namafile
		if object_address.startswith('/files/'):
			filename = object_address[len('/files/'):]
			if not filename or '/' in filename or '\\' in filename:
				return self.response(400, 'Bad Request', 'Invalid filename', {})
			if not os.path.exists(self.targetdir + filename):
				return self.response(404, 'Not Found', 'File not found', {})
			try:
				os.remove(self.targetdir + filename)
				return self.response(200, 'OK', f'File {filename} deleted', {})
			except Exception as e:
				return self.response(500, 'Internal Server Error', str(e), {})
		return self.response(400, 'Bad Request', 'Invalid delete request', {})

#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
	d = httpserver.proses('GET / HTTP/1.0')
	print(d.decode())
	d = httpserver.proses('DELETE /files/testing.txt HTTP/1.0')
	print(d.decode())
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)















