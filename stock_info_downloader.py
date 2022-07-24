import os
import conf
import json
import alpha
import utils

import sys

annual_r = "annualReports"
quarterly_r = "quarterlyReports"
fiscal_d = "fiscalDateEnding"

class stock(object):
	def __init__(self, path, ticker):
		self.base_path = "./" + path
		if not os.path.exists(self.base_path):
			os.makedirs(self.base_path)
		self.output    = self.base_path + "/" + ticker + ".json"
		if os.path.exists(self.output):
			with open(self.output, "r") as f:
				self.data = json.load(f)
		else:
			self.data = dict()
			self.data[alpha.request_type.BALANCE_SHEET.name] = dict()
			self.data[alpha.request_type.INCOME_STATEMENT.name] = dict()
			for i in self.data:
				self.data[i][annual_r] = dict()
				self.data[i][quarterly_r] = dict()

	def __commit(self):
		tmp_path = self.output + ".tmp"

		with open(tmp_path, "w+") as f:
			f.write(json.dumps(self.data, sort_keys=True, indent=4))
		if os.path.exists(self.output):
			os.unlink(self.output)
		os.link(tmp_path, self.output)
		os.unlink(tmp_path)

	def __format(self, item):
		for instance in item:
			value = item[instance]
			try:
				v = float(value)
				value = v
			except ValueError:
				pass
			if value == "None":
				value = 0.0
			item[instance] = value

		return item

	def __getitem__(self, it, key, annual=True):
		qa = annual_r
		if annual:
			qa = quarterly_r
		return self.__format(self.data[it.name][qa][key])

	def update(self, it, data):
		an = data[annual_r]
		qu = data[quarterly_r]

		# refactor later
		for report in an:
			rt = report[fiscal_d]
			try:
				nothing = self.data[it.name][annual_r][rt]
			except KeyError:
				self.data[it.name][annual_r][rt] = report
		for report in qu:
			rt = report[fiscal_d]
			try:
				nothing = self.data[it.name][quarterly_r][rt]
			except KeyError:
				self.data[it.name][quarterly_r][rt] = report

		self.__commit()



if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("You must supply the api_key")
		sys.exit()
	api_key = sys.argv[1]

	print("Loading the skip list")
	skip_list = utils.p_array(conf.not_listed_fn)
	have_list = utils.p_array(conf.have_list_fn)

	a = alpha.AlphaVantage(api_key)

	tickers = utils.load_tickers(conf.tickers_fn)

	requests = [alpha.request_type.BALANCE_SHEET, alpha.request_type.INCOME_STATEMENT] #, alpha.request_type.OVERVIEW]

	i = 0
	for ticker in tickers:
		i += 1
		print("Ticker: %3d/%3d" % (i, len(tickers)))
		if skip_list.isin(ticker):
			print("Skipping unlisted ticker: %s" % ticker)
			continue
		if have_list.isin(ticker):
			print("Already have ticket: %s" % ticker)
			continue
		st = stock(conf.data_path, ticker)
		for request in requests:
			try:
				print("Requesting: %s" % request.name)
				data = a.get(ticker, request)
				print("Committing Request")
				st.update(request, data)
				print("Request committed")
			except alpha.APILimit as e:
				print("API limit reached")
				sys.exit(1)
			except alpha.NotListed as e:
				print("Unlisted ticker %s" % ticker)
				skip_list.append(ticker)
				skip_list.commit()
				break
		have_list.append(ticker)
		have_list.commit()




