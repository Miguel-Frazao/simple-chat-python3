import threading, socket, select, json

class Chat_Server:
	def __init__(self):
		self.conns = set() # all connections
		self.actives = set() # connections who provided an username
		self.data = {} # all data we want to store

	def run(self, addr, port):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.bind((addr, port))
			sock.listen(5)
			print('Server started at {}:{}\n'.format(addr, port))
			while True:
				client, addr = sock.accept()
				self.conns.add(client)
				t = threading.Thread(target=self.server_handler, args=(client,), name='t_{}'.format(self.client_name(client)))
				t.start()

	def client_name(self, client):
		return ':'.join(str(i) for i in client.getpeername())

	def client_close(self, client):
		self.conns.remove(client)
		del self.data[self.client_name(client)]
		if client in self.actives:
			self.actives.remove(client)

	def send_msg(self, msg, sender, to):
		to_send = {'from': sender, 'message': msg}
		to.send(json.dumps(to_send).encode('utf-8'))

	def send_to_all(self, msg, client, sender):
		if(sender != 'SERVER'):
			self.data[self.client_name(client)]['msgs_sent'].append(msg)
		ready_to_read,ready_to_write,in_error = select.select(self.actives, self.actives,[],0)
		for sock_write in ready_to_write:
			if(sock_write is not client):
				self.send_msg(msg, sender, sock_write)


	def server_handler(self, client):
		self.data[self.client_name(client)] = {'msgs_sent': [], 'username': None}
		msg = 'welcome...{}.\nThere are this users connected: {}\n\n'
		msg = msg.format(client.getpeername(), [i.getpeername() for i in self.conns])
		self.send_msg(msg, 'SERVER', client)
		while True:
			try:
				raw = client.recv(1024)
				req = raw.decode('utf-8').strip()
			except Exception as err:
				break
			if not req:
				self.client_close(client)
				break
			if(self.data[self.client_name(client)]['username'] is None):
				self.data[self.client_name(client)]['username'] = req
				self.send_to_all('{} HAS JOINED THE CHAT...'.format(req), client, 'SERVER')
				self.actives.add(client) # store all clients that gave an username
				continue

			self.send_to_all(req, client, self.data[self.client_name(client)]['username'])


chat = Chat_Server()
chat.run('', 9005) # adjust host/port