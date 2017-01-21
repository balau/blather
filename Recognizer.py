#This is part of Blather
# -- this code is licensed GPLv3
# Copyright 2013 Jezra

import os.path
import sys

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
Gst.init(None)

#define some global variables
this_dir = os.path.dirname( os.path.abspath(__file__) )


class Recognizer(GObject.GObject):
	__gsignals__ = {
		'finished' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING,))
	}
	def __init__(self, language_file, dictionary_file, src = None):
		GObject.GObject.__init__(self)
		self.commands = {}
		if src:
			audio_src = 'alsasrc device="hw:%d,0"' % (src)
		else:
			audio_src = 'autoaudiosrc'

		#build the pipeline
		cmd = audio_src+' ! audioconvert ! audioresample ! pocketsphinx name=asr ! appsink sync=false'
		try:
			self.pipeline=Gst.parse_launch( cmd )
		except Exception, e:
			print e.message
			print "You may need to install gstreamer0.10-pocketsphinx"
			raise e
		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect('message::element', self.element_message)
		#get the Auto Speech Recognition piece
		asr=self.pipeline.get_by_name('asr')
		asr.set_property('lm', language_file)
		asr.set_property('dict', dictionary_file)
		asr.set_property('configured', True)

	def element_message(self, bus, msg):
		"""Receive element messages from the bus."""
		msgtype = msg.get_structure().get_name()
		if msgtype != 'pocketsphinx':
			return
		if msg.get_structure().get_value('final'):
			self.emit("finished", msg.get_structure().get_value('hypothesis'))

	def listen(self):
		self.pipeline.set_state(Gst.State.PLAYING)

	def pause(self):
		self.pipeline.set_state(Gst.State.PAUSED)

