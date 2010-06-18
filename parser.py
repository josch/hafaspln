from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus, urlretrieve
from gzip import GzipFile
from cStringIO import StringIO
from struct import unpack
from time import sleep
from datetime import timedelta, date, time, datetime
from lxml import etree

def get_id(station):
	return get_ids(station+"!")[0]

def search_ids(station):
	return get_ids(station+"?")

def get_ids(query):
	req = Request("http://railnavigator.bahn.de/bin/rnav/query.exe/dn",
			'<?xml version="1.0" encoding="UTF-8" ?><ReqC ver="1.1" prod="String" lang="DE"><MLcReq><MLc n="%s" t="ST" /></MLcReq></ReqC>'%query,
			{"User-Agent":"Java/1.6.0_0"})
	# <MLc t="ST" n="Bahlen Germann "Bahler Buur", Dinklage" i="A=1@O=Bahlen Germann "Bahler Buur", Dinklage@X=81
	# grrrrrrrrr - too stupid to escape their xml!!!!
	parser = etree.XMLParser(recover=True, encoding='iso-8859-1')
	tree = etree.parse(urlopen(req), parser)
	# make sure None entries from badly parsed nodes are not in the output
	return [elem.get("i") for elem in tree.findall(".//MLc") if elem.get("i")]

def parse_i(i):
	tokens = i.strip('@').split("@")
	d = dict()
	for t in tokens:
		key, value = t.split("=", 1)
		d[key] = value
	return d

def compile_i_from_station(station):
	return get_id(station)

def compile_i_from_stationid(stationid):
	return "A=1@L=%09d@"%stationid

def compile_i_from_coords(x, y, name=None):
	if not name:
		name="---"
	return "A=16@O=%s@X=%d@Y=%d@"%(name, int(x*1000000), int(y*1000000))

#infile = open("../cities_germany_211009.clean.txt", "r")
#outfile = open("../cities_germany_291009.out.txt", "w")
#for city in infile:
#	print city,
#	for station in search_ids(city):
#		outfile.write("%s\t%s\t%s\t%s\n"%(station["O"], station["X"], station["Y"], station["L"]))
#	sleep(10)
#infile.close()
#outfile.close()
#exit()


#big plan
def get_big_pln_data():
	req = Request("http://persoenlicherfahrplan.bahn.de/bin/pf/query-p2w.exe/dn", 
			urlencode({"start":"1",
				   "pp":"5",
					   "ZID":"A=1@X=10885568@Y=48365444@O=Augsburg Hbf@L=008000013@U=80@K=S1-0N1@G=8000013@C=49@a=128@B=1@",
					   "output":"pln",
					   "hcount":"0",
					   "h2gversion":"6.20.7",
					   "spmo":"1",
					   "htype":"MicroEmulator-2.0",
					   "SID":"A=1@X=6092250@Y=50767829@O=Aachen Hbf@L=008000001@U=80@K=S1-0N1@G=8000001@C=49@a=128@B=1@",
					   "L":"vs_javapln",
					   "p2wIVRoute":"1",
					   "p2wCreateMaps":"1"}),
			{"User-Agent":"Java/1.6.0_0"})
	tokens = urlopen(req).read().split()
	time = ""
	url = ""
	for t in tokens:
		key, value = t.split("=", 1)
		if key == "url":
			url = value
		elif key == "time":
			time = value

def test_pln():
	url2 = ""
	while url2 == "":
		tokens = urlopen(url).read().strip().split("\n")
		print tokens
		for t in tokens:
			key, value = t.split("=", 1)
			if key == "url":
				url2 = value
				break
			elif key == "time":
				sleep(10)
				print value
	urlretrieve(url2, "pln")

# next: ignoreMinuteRound=yes&REQ0HafasScrollDir=1&h2g-direct=1&seqnr=1&ident=ox.0348695.1256054390&


def get_departures(station, dt):
	if isinstance(station, str):
		station = parse_i(get_id(station))["L"]
	req = Request("http://mobile.bahn.de/bin/mobil/bhftafel.exe/dn?",
			urlencode({
				"start":"yes",
				"date":dt.strftime("%d.%m.%Y"),
				"time":dt.strftime("%H:%M"),
				"boardType":"dep",
				"sTI":"0",
				"L":"vs_java3",
				"input":dep_station,
				"productsFilter":"1"*14
				}),
			{"User-Agent":"Java/1.6.0_0"})
	stops = urlopen(req).read()[4:-4].split("\n/>\n<Journey ")
	result = list()
	for stop in stops:
		tokens = stop.split("\n")
		evaid, name = tokens[0].split(" ", 1)
		s = dict()
		s["L"] = evaid.split("=")[1].strip("\"")
		s["O"] = name.split("=")[1].strip("\"")
		for t in tokens[1:]:
			key, value = t.split("=", 1)
			value = value.strip("\" ")
			if value:
				s[key] = value
		result.append(s)
	return result

def get_stops(train, dep_station, arr_station, dt):
	if isinstance(dep_station, str):
		station = parse_i(get_id(dep_station))["L"]
	if isinstance(arr_station, str):
		station = parse_i(get_id(arr_station))["L"]
	req = Request("http://mobile.bahn.de/bin/mobil/bhftafel.exe/dn?",
			urlencode({
				"start":"yes",
				"REQTrain_name":train,
				"date":dt.strftime("%d.%m.%Y"),
				"time":dt.strftime("%H:%M"),
				"boardType":"dep",
				"sTI":"1",
				"L":"vs_java3",
				"input":dep_station,
				"dirInput":arr_station,
				"productsFilter":"1"*14
				}),
			{"User-Agent":"Java/1.6.0_0"})
	stops = urlopen(req).read()[4:-4].split("\n/>\n<St ")
	result = list()
	for stop in stops:
		tokens = stop.split("\n")
		evaid, name = tokens[0].split(" ", 1)
		s = dict()
		s["L"] = evaid.split("=")[1].strip("\"")
		s["O"] = name.split("=")[1].strip("\"")
		for t in tokens[1:]:
			key, value = t.split("=", 1)
			value = value.strip("\" ")
			if value:
				s[key] = value
		result.append(s)
	return result

print get_stops('RE 36072', 8010334, 8010310, datetime(2010, 06, 18, 15, 43))

#late:
#http://mobile.bahn.de/bin/mobil/bhftafel.exe/dn?
#	start=yes
#	&time=actual
#	&rT.2=13%3A51
#	&rT.1=13%3A51
#	&boardType=dep
#	&hcount=0
#	&h2gversion=6.20.7
#	&rZ.2=RE%2010125
#	&htype=MicroEmulator-2.0
#	&rZ.1=RE%2010125
#	&L=vs_java
#	&input=%238000001&

def get_pln_data(start, end, stop1=None, stop2=None, dt=None, bike=False,
	ice=True, ic=True, ir=True, re=True, sbahn=True, bus=True, boat=True,
	subway=True, tram=True, taxi=True):
	if dt is None:
		dt = datetime.now()
	query = {"ignoreMinuteRound":"yes",
			"date":dt.strftime("%d.%m.%Y"),
			"ZID":end,
			"h2g-direct":"1",
			"time":dt.strftime("%H:%M"),
			"SID":start,
			"start":"1"}
	
	if not all([ice, ic, ir, re, sbahn, bus, boat, subway, tram, taxi]):
		query["REQ0JourneyProduct_prod_list_1"] = \
				"".join(str(int(x)) for x in [ice, ic, ir, re, sbahn, bus, boat, subway, tram, taxi])+"1111"
	if bike:
		query["REQ0JourneyProduct_opt3"] = "1"
	if stop1:
		query["VID1"]=stop1
		if stop2:
			query["VID2"]=stop2
	
	req = Request("http://mobile.bahn.de/bin/mobil/query.exe/dn",
			urlencode(query),
			{"User-Agent":"Java/1.6.0_0"})
	r = urlopen(req) # is a file like object but does not have tell()	
	s = StringIO(r.read()) # this is why a stringio has to be created for gzip
	return GzipFile(mode="r", fileobj=s) # possibly replacable by manually reading the gzip header

class PlnParse:
	"""
	all data in little endian
	offsets are always counted from start of the file
	latitude, longitude are in wgs84 format
	ushort is of size 2
	uint is of size 4
	"""
	def __init__(self, fh):
		self.f = fh
		self.strings = dict()
		self.connections = list()
	   
		self.f.seek(0x00)
		self.version, = unpack("<H", self.f.read(2))
		"""
		pos	 type	description
		0x00	ushort  version
		"""
		if self.version != 5:
			raise IOError, "unknown version: %d"%self.version
		
		self.f.seek(0x02)
		start_station, u1, sX, sY = unpack("<H3I", self.f.read(14))
		"""
		pos	 type	description
		0x02	ushort  string reference to start station name
		0x04	uint	unknown
		0x08	uint	longitude of start station
		0x0C	uint	latitude of start station
		"""
		
		self.f.seek(0x10)
		end_station, u1, eX, eY = unpack("<H3I", self.f.read(14))
		"""
		pos	 type	description
		0x10	ushort  string reference to end station name
		0x12	uint	unknown
		0x16	uint	longitude of end station
		0x1A	uint	latitude of end station
		"""
		
		self.f.seek(0x1e)
		number_of_conn, self.frequencies_offset, self.strings_offset = unpack("<HII", self.f.read(10))
		"""
		pos	 type	description
		0x1e	ushort  number of connections found
		0x20	uint	position of connection frequency data
		0x24	uint	position of string block
		"""
		#print "number_of_conn: %d, frequencies_offset: %d, strings_offset: %d"%(number_of_conn, self.frequencies_offset, self.strings_offset)
		
		#now that we read the string_offset, get the station names
		self.start_station = {"name":self.get_string(start_station), "X":sX, "Y":sY}
		self.end_station = {"name":self.get_string(end_station), "X":eX, "Y":eY}
		
		self.f.seek(0x28)
		timetable_begin, timetable_end, today, timetable_remaining = unpack("<4H", self.f.read(8))
		"""
		pos	 type	description
		0x28	ushort  begin date of current timetable version
		0x2a	ushort  end date of current timetable version
		0x2c	ushort  date of query
		0x2e	ushort  remaining days in current timetable version
		"""
		self.timetable_info = {
			"timetable_begin":self.parse_date(timetable_begin),
			"timetable_end":self.parse_date(timetable_end),
			"today":self.parse_date(today),
			"timetable_remaining":timetable_remaining}
		
		self.f.seek(0x30)
		#print "unknown string: %s"%self.f.read(6)
		
		self.f.seek(0x36)
		self.cities_offset, self.train_props_offset \
			= unpack("<II", self.f.read(8))
		"""
		pos	 type	description
		0x36	uint	position of city descriptions
		0x3a	uint	position of train property data
		"""
		
		#TODO: <begin big (46 bytes) ugly unknown section>
		# a lot of unknown stuff which consists either of never changing data
		# or of zero-ed data
		# but seems to be not important for the rest as its size is static and
		# no static information seems to be missing
		# probably 46 bytes of obsolete data?
		self.f.seek(0x3e)
		#print "cities_offset: %d, train_props_offset: %d"%(self.cities_offset, self.train_props_offset)
		additional_offset1, u2, additional_offset2 \
			= unpack("<3I", self.f.read(12))
		#print "additional_offset1: %d, u2: %d, additional_offset2: %d"%(additional_offset1, u2, additional_offset2)
		
		self.f.seek(additional_offset1)
		u1, = unpack("<H", self.f.read(2))
		#print "u1: %d"%u1

		self.f.seek(additional_offset2)
		u1, u2, u3, request_id, u5_offset, u6, u7, u8_offset, u9, u10, u11, u12 \
			= unpack("<IIHHIHHI4H", self.f.read(32))
		#print "u1: %d, u2: %d, u3: %d, request_id: %s, u5_offset: %d, u6: %d, u7: %s, u8_offset: %d, u9: %d, u10: %d, u11: %d, u12: %d"%(u1, u2, u3, self.get_string(request_id), u5_offset, u6, self.get_string(u7), u8_offset, u9, u10, u11, u12)
		
		# the only useful stuff:
		self.reqest_id = self.get_string(request_id)
		self.products = self.parse_products(self.get_string(u7))
		#TODO: </end big ugly unknown section>
		
		for i in xrange(number_of_conn):
			self.f.seek(0x4a + 12*i)
			freq, train_list_offset, number_of_trains, number_of_changes, duration \
				= unpack("<HI3H", self.f.read(12))
			"""
			0 <= i < number_of_conn
			pos		 type	description
			0x4a+12*i   ushort  frequency of this connection
			0x4c+12*i   uint	position of train list after train_list_offset
			0x50+12*i   ushort  number of changes
			0x52+12*i   ushort  duration of this connection
			"""
			trains = list()
			for j in xrange(number_of_trains):
				self.f.seek(0x4a + train_list_offset + j*20)
				dep_time, dep_station, arr_time, arr_station, transportation, \
				train, arr_track, dep_track, note, train_proporties \
					= unpack("<10H", self.f.read(20))
				"""
				0 <= j < number_of_trains
				pos				type	description
				0x4a+train_list_offset+j*20	ushort	departure time
				0x4a+train_list_offset+j*20	ushort	departure station
				0x4a+train_list_offset+j*20	ushort	arrival time
				0x4a+train_list_offset+j*20	ushort	arrival station
				0x4a+train_list_offset+j*20	ushort	transportation method
				0x4a+train_list_offset+j*20	ushort	train identification
				0x4a+train_list_offset+j*20	ushort	arrival track
				0x4a+train_list_offset+j*20	ushort	departure track
				0x4a+train_list_offset+j*20	ushort	notes like final destination of tram
				0x4a+train_list_offset+j*20	ushort	train proporties
				"""
				trains.append({
					"dep_time":self.parse_time(dep_time),
					"dep_station":self.get_city(dep_station),
					"arr_time":self.parse_time(arr_time),
					"arr_station":self.get_city(arr_station),
					"transportation_type":self.parse_transportation(transportation),
					"train":self.get_string(train),
					"arr_track":self.get_string(arr_track),
					"dep_track":self.get_string(dep_track),
					"note":self.get_string(note),
					"train_properties":self.get_train_props(train_proporties)})
			self.connections.append({
				"freq":self.get_frequency(freq),
				"number_of_changes":number_of_changes,
				"duration":self.parse_timedelta(duration),
				"trains":trains})
	
	def parse_products(self, products):
		"""
		used means of transportation for a returned connection set is given as
		10 chars being "1" or "0" depending wether the product is being
		considered or not.
		this method maps this string to a dict
		"""
		if products and len(products) == 14:
			p = ["ice", "ic", "ir", "re", "sbahn", "bus", "boat", "subway", "tram", "taxi"]
			return dict(zip(p, map(bool, map(int, products[:10]))))
	
	def parse_timedelta(self, t):
		"""
		time is stored as an integer which, when represented as a string can be
		split to get a string representation of the time
		1345 => 13:54
		512 => 5:12
		"""
		t = "%03d"%t
		return timedelta(hours=int(t[:-2]), minutes=int(t[-2:]))

	def parse_time(self, t):
		"""
		time is stored as an integer which, when represented as a string can be
		split to get a string representation of the time
		1345 => 13:54
		512 => 5:12
		"""
		t = "%03d"%t
		return time(hour=int(t[:-2]), minute=int(t[-2:]))

	def parse_date(self, d):
		"""
		dates are expressed as integers of days since 01.01.1980
		"""
		return date(1980, 1, 1)+timedelta(days=d)

	def parse_transportation(self, t):
		"""
		transportation can be by some train or by foot
		"""
		if t == 1:
			return "feet"
		elif t == 2:
			return "train"
		else:
			raise Exception, "transportation %d unexpected"%t

	def get_frequency(self, offset):
		"""
		given the offset, get the frequency a connection is scheduled from the
		data block beginning at frequencies_offset
		the last three values are still a myth as they dont seem to correspond
		with the information in the string referenced by the first value
		"""
		self.f.seek(self.frequencies_offset+offset)
		#TODO: what do the last values mean?
		#TODO: where are the days of service properly encoded?
		freq, u1, u2, u3 = unpack("<4H", self.f.read(8))
		return self.get_string(freq), u1, u2, u3

	def get_string(self, offset):
		"""
		given the offset, return a zero terminated string from the stringblock
		"""
		if offset in self.strings:
			# get it from dict to prevent ugly f.read(1)
			return self.strings[offset]
		else:
			self.f.seek(self.strings_offset+offset)
			result = ""
			# read zero terminated string.. ugly in py..
			while True:
				b = self.f.read(1)
				if b == "\0":
					# some strings come with many whitespaces at the end
					result = result.strip()
					# by convention of the format "---" means None
					if result == "---":
						result = None
					# fill a dict with strings to prevent too much ugly f.read(1)
					self.strings[offset] = result
					return result
				else:
					result += b

	def get_train_props(self, offset):
		"""
		given the offset, get the string list of train properties from the
		data block beginning at train_props_offset. the first ushort marks the
		amount of properties
		"""
		self.f.seek(self.train_props_offset+offset)
		n, = unpack("<H", self.f.read(2))
		return map(self.get_string, unpack("<%dH"%n, self.f.read(2*n)))

	def get_city(self, offset):
		"""
		given the offset, get data about a city from the data block beginning
		at cities_offset.
		the data includes the city name, its code and latitude, longitude
		"""
		self.f.seek(self.cities_offset+offset*14)
		name, L, X, Y = unpack("<H3I", self.f.read(14))
		return {"name":self.get_string(name), "L":L, "X":X, "Y":Y}

#f = open("stendal-salzwedel-1st.bin", "r")
f = GzipFile("stendal-salzwedel-1st.bin", "r")
#a = PlnParse(get_pln_data(compile_i_from_station("Bremen"), compile_i_from_station("Karlsruhe"), dt = datetime.today()+timedelta(days=1)))
#a = PlnParse(get_pln_data(compile_i_from_coords(8.6535, 53.1667), compile_i_from_station("Bremen"), dt = datetime.today()+timedelta(days=4)))
a = PlnParse(f)

#def bin(i):
#	return "".join(str((i >> y) & 1) for y in range(16-1, -1, -1))
#print a.timetable_info
from pprint import pprint
for conn in a.connections:
	pprint(conn)
#for conn in a.connections:
#	print "\t".join([conn["freq"][0], bin(conn["freq"][1]), bin(conn["freq"][2]), bin(conn["freq"][3])])
#for conn in a.connections:
#	print conn["freq"], conn["trains"][0]["dep_station"]["L"], conn["trains"][0]["train"], conn["trains"][0]["dep_time"]
