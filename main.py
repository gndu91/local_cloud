"""WARNING: AT THIS STAGE, THIS LIBRARY IS NOR THREAD SAFE, NOR PROCESS SAFE"""
# import cryptography
import os, unittest, random, math, dbm.dumb

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


# For the moment, deciphering with a wrong key is like accessing an non reserved
# 	memory adress, sometimes it crashes, sometimes it passes (in this case it
# 	fails to unpad the deciphered data)
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
BLOCK_SIZE = 1024
CHUNK_SIZE = 1024 * 1024


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
	key_length = ENCRYPTION_KEY_SIZE // 8

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


def fetch_key(name, key_name='default'):
	"""Ask the password and return the key"""
	# TODO: Fix this big hole to become thread safe
	key_name = key_name.lower()
	assert isinstance(name, str)
	assert isinstance(key_name, str)
	assert os.path.exists(name)
	assert os.path.exists(os.path.join(name, "keyring", key_name))
	with open(os.path.join(name, "keyring", key_name), 'rb') as f:
		encrypted_key = f.read()
	message0 = message = 'Please enter the %r key of %r' % (key_name, name)
	message1 = 'Error, password incorrect, Please retry.\n' + message0
	decrypted_key = b''
	while not decrypted_key.endswith(b' is the right key'):
		try:
			decrypted_key = decrypt_data(getpass.getpass(message).encode().zfill(
				ENCRYPTION_KEY_SIZE // 8)[:ENCRYPTION_KEY_SIZE // 8], encrypted_key)
		except ValueError:
			decrypted_key = b'Nope'
		if not decrypted_key.endswith(b' is the right key'):
			message = message1
	kkk = len(b' is the right key')
	print(decrypted_key[:-kkk])
	return decrypted_key[:-kkk]


def init(name=DEFAULT_NAME, chunk_size=CHUNK_SIZE, noise_as_background=True):
	"""Initialize a local folder, with a fixed block of noise or zeros"""
	# TODO: Decide if it is a good idea to restrain block sizes to fit with
	# 	aes block size
	# Will raise an exception if the folder already exists
	os.makedirs(name)
	assert chunk_size == CHUNK_SIZE

	with open(os.path.join(name, os.path.join('BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))), 'wb') as f:
		# TODO: Optimize to make it chunk by chunk for big block sizes
		f.write(os.urandom(chunk_size) if noise_as_background else bytes(block_size))

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


def read(name, path):
	# TODO: Checks
	with dbm.dumb.open(os.path.join(name, 'BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))) as db:
		return decrypt_data(fetch_key(name), db[path])


def write(name, path, content):
	# TODO: Checks
	with dbm.dumb.open(os.path.join(name, 'BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))) as db:
		db[path] = encrypt_data(fetch_key(name), content)

	"""assert isinstance(content, bytes)
	length = len(content)
	size = length * 8
	number_of_blocks = math.ceil(size / BLOCK_SIZE)
	with open(os.path.join(name, 'bitmap'), 'rb') as f:
		bitmap = f.read()"""

	"""return
	# TODO: Go deeper and search free bits.
	# Will raise ValueError if it doesn't find anything
	# TODO: Make data more sparse
	# TODO: Automatically add blocs, and warn if too much of them
	index = bitmap.index(bytes(number_of_blocks // 8)) # 1 byte -> 8 blocks
	with open(os.path.join(name, os.path.join('BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))), 'ab') as f:
		pass
	# TODO: Make sure we don't overlap
	with open(os.path.join(name, os.path.join('BLOCK%s' % str(0).zfill(BLOCK_INDEX_LENGTH))), 'ab') as f:
		# TODO: Optimize to make it chunk by chunk for big block sizes
		f.seek(index)
		f.write(encrypted)"""


class Tests(unittest.TestCase):

	# TODO: Use random values to initialize database key, to not have to silent
	# 	those tests
	@unittest.skip("Skipping it while we don't change the initialization function")
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

	def test_download(self):
		try:
			init('Download')
		except:
			pass
		url = "http://www.geeksforgeeks.org/get-post-requests-using-python/"
		import requests
		write('Download', url, requests.get(url))
		read('Download', url)

	@unittest.skip("Skipping it while we don't change the function")
	def test(self):
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

			text = input('Enter the text you want to save').encode()
			write(name, 'main.txt', text)
			r = read(name, 'main.txt')
			print(r)
			assert r == text

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
