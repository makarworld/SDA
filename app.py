import os
from os import listdir
from os.path import isfile, join
import base64
import hmac
import struct
import time
from hashlib import sha1
import json

def generate_one_time_code(shared_secret: str, timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    time_buffer = struct.pack('>Q', timestamp // 30)  # pack as Big endian, uint64
    time_hmac = hmac.new(base64.b64decode(shared_secret), time_buffer, digestmod=sha1).digest()
    begin = ord(time_hmac[19:20]) & 0xf
    full_code = struct.unpack('>I', time_hmac[begin:begin + 4])[0] & 0x7fffffff  # unpack as Big endian uint32
    chars = '23456789BCDFGHJKMNPQRTVWXY'
    code = ''

    for _ in range(5):
        full_code, i = divmod(full_code, len(chars))
        code += chars[i]

    return code

def get_mafiles() -> list:
	mypath = os.path.dirname(os.path.abspath(__file__)) + r'\mafiles'
	mafiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

	if mafiles == []:
		raise MafilesNotFoundError("Put mafiles in {}".format(
				os.path.dirname(os.path.abspath(__file__)) + r'\mafiles'))
	return mafiles

def open_mafiles(mafiles: list) -> dict:
	response = {}

	for mafile in mafiles:
		with open(os.path.dirname(os.path.abspath(__file__)) + r'\mafiles\\' + mafile, 'r', encoding='utf-8') as f:
			mafile_data = json.load(f)
		response[mafile] = mafile_data

	return response

def find_name(name: str):
	if True in [name.lower() == mafile.replace(".maFile", "").lower() for mafile in mafiles]:
		return name + ".maFile"

	for mafile in mafiles_dict:
		if name.lower() == mafile.replace(".maFile", "").lower():
			return name + ".maFile"
		elif name.lower() == mafile.lower():
			return name
	try:
		name = int(name)
		if name > len(mafiles):
			print("Invalid index")
			return False

		return mafiles[name - 1]

	except ValueError:
		print("Invalid name")
		return False

mafiles = get_mafiles()
mafiles_dict = open_mafiles(mafiles)

print("mafiles:")
for item in mafiles:
	i = mafiles.index(item)
	print('{}. {}'.format(i + 1, mafiles_dict[item]['account_name']))

while True:
	print("input mafile name or index to generate GuardCode: ", end='')
	name = input()

	if name == "menu" or name == "accs" or name == "mafiles" or name == "m":
		print("mafiles:")
		for item in mafiles:
			print('{}. {}'.format(mafiles.index(item), item.replace(".maFile", "")))
		else:
			continue

	mafile_name = find_name(name)
	if mafile_name is not False:
		shared_secret = mafiles_dict[mafile_name]['shared_secret']
		code = generate_one_time_code(shared_secret)
		print('{} GuardCode: {}'.format(mafile_name.replace(".maFile", ""), code))


