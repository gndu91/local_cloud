# import cryptography
import os, unittest, random


def init(name='default', block_size=1024*1024):
	"""Initialize a local folder, with a fixed block of noise"""

	# Will raise an exception if the folder already exists
	os.makedirs(name)


def nuke(name):
	"""Destroy the entire database, hazardous, will be removed later"""
	raise NotImplementedError




class Tests(unittest.TestCase):
	def test_initialization(self):

		# First of all, we create a temporary folder
		folder = 'tmp.%s' % hex(random.randint(0, 16**8))[2:].zfill(8)
		os.makedirs(folder, exist_ok=True)

		# Then, we go inside it
		os.chdir(folder)

		try:
			print(input(os.path.abspath('.')))
		finally:
			os.chdir('..')
			os.rmdir(folder)
