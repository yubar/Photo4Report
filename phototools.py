import os, glob
import piexif
from PIL import Image
from datetime import datetime, timedelta
import logging
from xml.etree import ElementTree
from bisect import bisect_left, bisect_right

def parseTrack(filename):
	tree = ElementTree.parse(filename)  
	ns = {"x":"http://www.topografix.com/GPX/1/1"}
	pts = tree.findall("x:trk[1]/x:trkseg[1]/x:trkpt", ns)
	points = [(
		datetime.strptime(pt.find('x:time', ns).text, "%Y-%m-%dT%H:%M:%SZ")
		, float(pt.attrib["lat"])
		, float(pt.attrib["lon"])
		, float(pt.find('x:ele', ns).text))
		for pt in pts]
	dates = [x[0] for x in points]
	return points, dates
	
def getCoords(dt, points, dates, threshold = timedelta(seconds = 15)):
	i = bisect_left(dates, dt)
	coords = None
	if i == 0:
		if dates[i] - dt <= threshold: coords = points[i]
	elif i == len(points):
		if dt - dates[i-1] <= threshold: coords = points[i-1]
	else:
		if dates[i] - dt <= threshold and dates[i] - dt <= dt - dates[i-1]: coords = points[i]
		elif dt - dates[i-1] <= threshold: coords = points[i-1]
		
	return coords

def setExifGps(exif, coords):

	def dd2dms(deg):
		d = int(deg)
		md = abs(deg - d) * 60
		m = int(md)
		sd = int((md - m) * 60 * 10000)
		return ((d, 1), (m, 1), (sd, 10000))
	
	if coords == None: return exif
	#print(coords)
	GpsData = dict()
	
	GpsData[1] = ("N" if coords[1]>=0 else "S").encode("ASCII")
	GpsData[2] = dd2dms(coords[1])
	GpsData[3] = ("E" if coords[2]>=0 else "W").encode("ASCII")
	GpsData[4] = dd2dms(coords[2])
	GpsData[6] = (int(coords[3] * 1000), 1000)
	
	#print(GpsData)
	exif["GPS"] = GpsData
	
	#print(exif)
	return exif

def setExifDateTime(exif, newDate):
	dtsupd = newDate.strftime("%Y:%m:%d %H:%M:%S").encode("ASCII")		
	exif["Exif"][ExifDateTimeOriginal] = dtsupd
	exif["Exif"][ExifDateTimeDigitized] = dtsupd
	return exif

def main():
	path = u"r:\\photo\\20190824 Камча 4\\Export_"
	#path = u"r:\\photo\\20190824 Камча 4\\Export_\\pano"
	#path = u"r:\\photo\\20190824 Камча 4\\_mi" 
	outpath = u"r:\\photo\\20190824 Камча 4\\fnl"
	ext = u"jpg"
	global ExifDateTimeOriginal
	global ExifDateTimeDigitized
	ExifDateTimeOriginal = 36867
	ExifDateTimeDigitized = 36868
	
	trackFileName = u'r:\\Projects\\Phototools\\Fact_raw.gpx'
	
	#delta = timedelta(seconds=0)
	#tzGMT = -timedelta(hours=12)
	#tzLocal = timedelta(hours=0)
	
	delta = -timedelta(minutes=7, seconds=18)
	tzGMT = -timedelta(hours=3)
	tzLocal = timedelta(hours=9)
	
	logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")
	
	points, dates = parseTrack(trackFileName)
	
	os.chdir(path)
	i = 0
	for file in glob.glob("*." + ext):
		i = i + 1
		#if i > 10: break
		
		exif_dict = piexif.load(file)
		dts = exif_dict["Exif"][ExifDateTimeOriginal].decode("ASCII")
		d = datetime.strptime(dts,"%Y:%m:%d %H:%M:%S")
				
		coords = getCoords(d + delta + tzGMT, points, dates)
		if coords is not None and not (2 in exif_dict["GPS"]): exif_dict = setExifGps(exif_dict, coords)
		
		dtupd = d+delta+tzLocal
		exif_dict = setExifDateTime(exif_dict, dtupd)
		outname = dtupd.strftime("%Y%m%d_%H%M%S_") + file
		logging.info(file + ' ' + str(d) + ' ' + str(d+delta+tzGMT) + ' ' + str(d+delta+tzLocal) + ' ' + str(coords))
		
		exif_bytes = piexif.dump(exif_dict)
		im = Image.open(file)
		im.save(os.path.join(outpath, outname), exif=exif_bytes)
		
if __name__ == "__main__":
	main()