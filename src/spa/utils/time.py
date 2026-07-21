import time

def get_timestamp(file_format=False):
	"""
	Utility function to get a properly formatted timestamp. 

	Args:
		file_format (bool): If true, timestamp will not include ':' characters
			for a more OS-friendly string that can be used in less risky file 
			names [default: False ]
	"""
	if file_format:
		return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
	else:
		return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())