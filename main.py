"""WARNING: AT THIS STAGE, THIS LIBRARY IS NOR THREAD SAFE, NOR PROCESS SAFE"""
# import cryptography
import os, unittest, random

USE_GETPASS = True

if USE_GETPASS:
	import getpass
else:
	from easygui import passwordbox

	getpass = type('getpass', (object,), dict(
		getpass=passwordbox
	))

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend

BACKEND = default_backend()

# For the moment, this will be written in the code, later it will be
# 	written in a database.
ENCRYPTION_ALGORITHM = algorithms.AES
ENCRYPTION_BACKEND = BACKEND
ENCRYPTION_MODE = modes.CTR
ENCRYPTION_KEY_SIZE = next(iter(reversed(list(i for i in ENCRYPTION_ALGORITHM.key_sizes if i < 512))))


def encrypt_data(key, data) -> bytes:
	# Encrypt using the configuration above, later, will return config along
	# 	with data, for now, it return None as a config element, because
	# 	I don't know how it is going to be
	assert isinstance(data, bytes), type(data)
	nonce = os.urandom(ENCRYPTION_ALGORITHM.block_size // 8)
	cipher = Cipher(ENCRYPTION_ALGORITHM(key), ENCRYPTION_MODE(nonce), backend=ENCRYPTION_BACKEND)
	encryptor, padder = cipher.encryptor(), PKCS7(ENCRYPTION_ALGORITHM.block_size).padder()
	return nonce + encryptor.update(padder.update(data) + padder.finalize()) + encryptor.finalize()


def decrypt_data(key, data) -> bytes:
	# Encrypt using the configuration above, later, will return config along
	# 	with data, for now, it return None as a config element, because
	# 	I don't know how it is going to be
	assert isinstance(data, bytes), type(data)
	nonce, data = data[:ENCRYPTION_ALGORITHM.block_size // 8], data[ENCRYPTION_ALGORITHM.block_size // 8:]
	cipher = Cipher(ENCRYPTION_ALGORITHM(key), ENCRYPTION_MODE(nonce), backend=ENCRYPTION_BACKEND)
	decryptor, unpadder = cipher.decryptor(), PKCS7(ENCRYPTION_ALGORITHM.block_size).unpadder()
	return unpadder.update(decryptor.update(data) + decryptor.finalize()) + unpadder.finalize()


# This is only here to have an ordered
# 	folder, with 002 before 100
BLOCK_INDEX_LENGTH = 4
DEFAULT_NAME = 'default'
DEFAULT_TMP_NONCE_LENGTH = 8


# TODO: Create recovery methods, and store them at the end of blocks
def generate_key(name, key_name='DEFAULT'):
	"""Generate a key inside the keyring sub folder, then ask for a password
	Raise an exception if the key is already defined."""

	# TODO: Backward compatibility
	if isinstance(key_name, bytes):
		key_name = key_name.decode()

	key_name = key_name.lower()

	# TODO: Create a batter Exception type
	assert key_name == 'default', 'For now, everything will be encrypted using it'

	# First step: Generate the encryption key
	# We don't need more than 256, so we take the highest under 512 bits
	# Key sizes are sorted by default, so we just have to take the last one
	key_length = ENCRYPTION_KEY_SIZE * 8

	print('Generating a %s bits key...' % key_length, flush=True, end='')
	key = os.urandom(key_length)
	print('done', flush=True)

	try:
		os.chdir(name)
	except FileNotFoundError:
		# TODO: Create a batter Exception type
		raise
	else:
		try:
			os.makedirs('keyring', exist_ok=True)
			os.chdir('keyring')
			try:
				# !!! WARNING !!! RACE CONDITION
				# Process-based and Thread-bases
				try:
					open(key_name, 'rb').close()
				except FileNotFoundError:
					password, confirmation = '01'

					msg = msg0 = 'Please enter a password to encrypt it:'
					msg1 = 'Passwords mismatch, Please re enter a password to encrypt it:'

					while password != confirmation:
						# TODO: Restrict password to secure ones
						password = getpass.getpass(msg)
						confirmation = getpass.getpass('Please confirm your password to encrypt it:')
						# TODO: Create a special type of password: PIN code
						if password != confirmation:
							msg = msg1
						elif len(password) > ENCRYPTION_KEY_SIZE // 8:
							msg = 'Password too long' + msg0
							password, confirmation = '01'

					# A way to check the key, maybe I can do better
					key = encrypt_data(password.encode().zfill(ENCRYPTION_KEY_SIZE // 8), key + b' is the right key')
					with open(key_name, 'wb') as f:
						f.write(key)

				else:
					raise RuntimeError(
						'Key already defined'
					)
			finally:
				os.chdir('..')
		finally:
			os.chdir('..')


def init(name=DEFAULT_NAME, block_size=1024 * 1024, noise_as_background=True):
	"""Initialize a local folder, with a fixed block of noise or zeros"""
	# TODO: Decide if it is a good idea to restrain block sizes to fit with
	# 	aes block size
	# Will raise an exception if the folder already exists
	os.makedirs(name)

	with open(os.path.join(name, os.path.join('BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))), 'wb') as f:
		# TODO: Optimize to make it chunk by chunk for big block sizes
		f.write(os.urandom(block_size) if noise_as_background else bytes(block_size))

	generate_key(name, 'default')


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

	for i in os.scandir(os.path.join(name, 'keyring')):
		os.remove(i.path)

	os.rmdir(os.path.join(name, 'keyring'))
	os.rmdir(name)


class Tests(unittest.TestCase):
	def test_initialization(self):
		# First of all, we choose an unique name to avoid messing with actual data

		noise = random.choice((False, True))
		name = 'tmp.%s' % hex(random.randint(0, 16 ** DEFAULT_TMP_NONCE_LENGTH))[2:].zfill(DEFAULT_TMP_NONCE_LENGTH)
		block_size = 1024 * 1024
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
			print(os.path.abspath('.'))
			nuke(name)
			print('Database %s deleted' % name)

	@unittest.skip("Skipping it while we don't change the function")
	def test_encryption(self):
		"""Check that encryption is working properly.
		For now, the entire encryption is based on hard-coded preferences, later, this will change"""
		key = os.urandom(ENCRYPTION_KEY_SIZE // 8)
		data = bytes(ENCRYPTION_ALGORITHM.block_size * 1024 // 8)
		self.assertEqual(decrypt_data(key, encrypt_data(key, data)), data)
