# import cryptography
import os, unittest, random

DEFAULT_NAME = 'default'
DEFAULT_TMP_NONCE_LENGTH = 8


def init(name=DEFAULT_NAME, block_size=1024*1024):
	"""Initialize a local folder, with a fixed block of noise"""

	# Will raise an exception if the folder already exists
	os.makedirs(name)


def nuke(name):
	"""Destroy the entire database, hazardous, will be removed later"""
	os.rmdir(name)




class Tests(unittest.TestCase):
	def test_initialization(self):
		# First of all, we choose an unique name to avoid messing with actual data
		name = 'tmp.%s' % hex(random.randint(0, 16**DEFAULT_TMP_NONCE_LENGTH))[2:].zfill(DEFAULT_TMP_NONCE_LENGTH)

		try:
			init(name)
			print('Database initialized in %s' % name)
		finally:
			# I don't want to left trash
			nuke(name)
			print('Database %s deleted' % name)
