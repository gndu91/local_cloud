# import cryptography
import os, unittest, random

DEFAULT_NAME = 'default'
DEFAULT_TMP_NONCE_LENGTH = 8

# This is only here to have an ordered
# 	folder, with 002 before 100
BLOCK_INDEX_LENGTH = 4

def init(name=DEFAULT_NAME, block_size=1024*1024, noise_as_background=True):
	"""Initialize a local folder, with a fixed block of noise or zeros"""
	# TODO: Decide if it is a good idea to restrain block sizes to fit with
	# 	aes block size
	# Will raise an exception if the folder already exists
	os.makedirs(name)

	with open(os.path.join(name, os.path.join('BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))), 'wb') as f:
		# TODO: Optimize to make it chunk by chunk for big block sizes
		f.write(os.urandom(block_size) if noise_as_background else bytes([0]*block_size))


def nuke(name):
	"""Destroy the entire database, hazardous, will be removed later"""
	# First of all, remove the blocks
	continue_, index = False, 0
	while not continue_:
		try:
			# TODO: Improve it with a database
			os.remove(os.path.join(name, 'BLOCK%s' % str(index).zfill(BLOCK_INDEX_LENGTH)))
		except FileNotFoundError:
			continue_ = True


	os.rmdir(name)





class Tests(unittest.TestCase):
	def test_initialization(self):
		# First of all, we choose an unique name to avoid messing with actual data

		for noise in (False, True):
			name = 'tmp.%s' % hex(random.randint(0, 16**DEFAULT_TMP_NONCE_LENGTH))[2:].zfill(DEFAULT_TMP_NONCE_LENGTH)
			block_size = 1024*1024
			try:
				init(name, block_size, noise)
				print('Database initialized in %s' % name)
				with open(os.path.join(name, 'BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH)), 'rb') as f:
					data = f.read()
					self.assertEqual(len(data), block_size, len(data))
					if not noise:
						self.assertEqual(set(data), {0}, set(data))
			finally:
				# I don't want to left trash
				nuke(name)
				print('Database %s deleted' % name)
