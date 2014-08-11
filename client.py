# -*- coding: utf-8 -*-
import PushbulletTargets

STREAM_BASE_URL = 'wss://stream.pushbullet.com/websocket/{0}'

TARGETS = None

DEBUG = PushbulletTargets.DEBUG
LOG = PushbulletTargets.LOG

def registerDevice(device):
	assert TARGETS != None, 'Client not initialized!'
	return TARGETS.registerDevice(device)
	
def unregisterDevice(ID):
	assert TARGETS != None, 'Client not initialized!'
	return TARGETS.unregisterDevice()

def init(token):
	global TARGETS
	TARGETS = PushbulletTargets.Targets(token)
	
def start():
	assert TARGETS != None, 'Client not initialized!'
	try:
		TARGETS.connect()
		return True
	except:
		TARGETS.close()
	return False	

def stop():
	global TARGETS
	if not TARGETS: return
	TARGETS.close()
	TARGETS = None
		
	
def wait():
	assert TARGETS != None, 'Client not initialized!'
	try:
		TARGETS.run_forever()
	except KeyboardInterrupt:
		LOG('Closing...')
		stop()
