import sys, time, json
try:
	import requests2 as requests
except ImportError:
	import requests

import ws4py
sys.modules['ws4py'] = ws4py
from ws4py.client.threadedclient import WebSocketClient


STREAM_BASE_URL = 'wss://stream.pushbullet.com/websocket/{0}'

DEBUG = False
def LOG(msg):
	print 'PushbulletTargets: {0}'.format(msg)


class Device:
	settings = {}
	
	def __init__(self,ID,name=None,data=None):
		self.ID = ID
		self.name = name
		self.data = data
		self._bulletHoles = {}

	def getSetting(self,sid):
		default = self.settings.get(sid)
		value = self.data.get(sid)
		try:
			return type(default)(value)
		except:
			pass
		return default	

	def setSetting(self,sid,value):
		self.data[sid] = value

	def getShot(self,bullet):
		ID = bullet.get('iden')
		modified = bullet.get('modified')
		if self._bulletHoles.get(ID) >= modified: return
		self._bulletHoles[ID] = modified
		bType = bullet.get('type')
		if bType == 'note':
			return self.note(bullet)
		else:
			return self.unknown(bullet)
		
	def note(self,data):
		LOG('NOTE_NOT_IMPL: {0}'.format(data))

	def unknown(self,data):
		LOG('UNKNOWN_NOT_IMPL: {0}'.format(data))

class Client:
	baseURL = 'https://api.pushbullet.com/v2/{0}'
	
	def __init__(self,token):
		self.token = token

	def pushes(self):
		req = requests.get(self.baseURL.format('pushes'),auth=(self.token,''))
		data = req.json()
		return data.get('pushes')

	def dismissPush(self,ID):
		requests.post(self.baseURL.format('pushes/{0}'.format(ID)),auth=(self.token,''),data={'dismissed':'true'})
		
	def deletePush(self,ID):
		requests.delete(self.baseURL.format('pushes/{0}'.format(ID)),auth=(self.token,''))

class Targets(WebSocketClient):
	def __init__(self,token):
		self.lastPing = time.time()
		self.client = Client(token)
		self.devices = {}
		WebSocketClient.__init__(self,STREAM_BASE_URL.format(token))

	def opened(self):
		LOG('CONNECTED')
		self.gunfire()

	def closed(self,code,reason=None):
		LOG('DISCONNECTED ({0}) {1}'.format(code,reason or ''))
		
	def received_message(self,message):
		try:
			data = json.loads(unicode(message))
		except:
			LOG('JSON MESSAGE ERROR: {0}'.format(repr(message)[:100]))
			return
		mType = data.get('type')
		if mType == 'nop':
			self.pinged()
		elif mType == 'tickle':
			subType = data.get('subtype')
			if subType == 'push':
				self.gunfire()
			elif subType == 'device':
				self.changed()
		else:
			if DEBUG:
				try:
					LOG('UNHANDLED MESSAGE: {0}'.format(json.loads(unicode(message)).get('type')))
				except:
					pass
			
	def gunfire(self):
		pushes = self.client.pushes()
		for bullet in pushes:
			if not bullet.get('active') or bullet.get('dismissed'): continue
			tID = bullet.get('target_device_iden')
			if tID in self.devices:
				dev = self.devices[tID]
				if DEBUG: LOG('SHOT: {0}'.format(dev.name))
				if dev.getShot(bullet):
					self.client.deletePush(bullet.get('iden'))

	def pinged(self):
		now = time.time()
		if DEBUG: LOG('PING: {0:.2f}'.format(now - self.lastPing))
		self.lastPing = now

	def changed(self):
		if DEBUG: LOG('CHANGED')
		
	def registerDevice(self,device):
		if not device.ID in self.devices: self.devices[device.ID] = device
	
	def unregisterDevice(self,ID):
		if ID in self.devices: del self.devices[ID]
		
	def close(self):
		WebSocketClient.close(self)
		self.client_terminated = True
		self.server_terminated = True