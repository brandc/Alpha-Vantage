import time
import requests

from enum import Enum

class request_type(Enum):
	BALANCE_SHEET = "BALANCE_SHEET"
	INCOME_STATEMENT = "INCOME_STATEMENT"
	OVERVIEW = "OVERVIEW"


class NotListed(Exception):
	pass
class APILimit(Exception):
	pass

import json
class AlphaVantage(object):
	def __init__(self, api_key, rpm=5):
		self.api_key = api_key
		# We are kind to AlphaVantage and it's resources, so we try to limit our connection creations
		self.r = requests.Session()
		# Calculating delay
		self.delay_amount = 60.0 / rpm
		self.target_next_use = time.time() + self.delay_amount
		return
	def __del__(self):
		del self.api_key
		del self.r
	def __download(self, url):
		delta = self.target_next_use - time.time()
		if delta > 0.0:
			time.sleep(delta)
		# There are many exceptions that remain to be caught
		req = self.r.get(url)
		# Update cooldown
		self.target_next_use = time.time() + self.delay_amount

		raw = json.dumps(req.json())
		js  = json.loads(raw)

		# This means that the stock is not listed
		if len(raw) == 2:
			# This should be helpful for distinguishing companies
			raise NotListed("%s" % url)
		# If the "Information" key is present, then we've hit the API limit
		try:
			info = js["Information"]
			raise APILimit(raw)
		except KeyError:
			pass
		# Return the data
		return js
		
	def __build_url(self, function, ticker):
		return "https://www.alphavantage.co/query?function=%s&symbol=%s&apikey=%s" % (function.name, ticker, self.api_key)
	def get(self, ticker, request):
		if type(request) != request_type:
			raise TypeError("\"request\" should be of type \"request_type\"")
		url = self.__build_url(request, ticker)
		try:
			data = self.__download(url)
			dump = json.dumps(data)
			return json.loads(dump)
		except NotListed as e:
			raise NotListed(e)







