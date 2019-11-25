import argparse
import os, glob
import piexif
from PIL import Image
from datetime import datetime, timedelta
import logging
from xml.etree import ElementTree
from bisect import bisect_left, bisect_right
from shutil import copyfile

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
	#GpsData[16] = "T".encode("ASCII")
	#GpsData[17] = (int(coords[4] * 1000), 1000)
	
	exif["GPS"] = GpsData
	
	#print(exif)
	return exif

def setExifDateTime(exif, newDate):
	dtsupd = newDate.strftime("%Y:%m:%d %H:%M:%S").encode("ASCII")		
	exif["Exif"][ExifDateTimeOriginal] = dtsupd
	exif["Exif"][ExifDateTimeDigitized] = dtsupd
	return exif

def setExifGpsAngle(GpsData, prevGpsData, duplicateCount):
	if GpsData:
		if prevGpsData and GpsData[2] == prevGpsData[2] and GpsData[4] == prevGpsData[4]:
			duplicateCount = duplicateCount + 1
		else:
			duplicateCount = 0
		
		GpsData[17] = (int(duplicateCount * 50 * 1000), 1000) #36 unique directions
		
	return GpsData, duplicateCount

def processImages(args):
	global ExifDateTimeOriginal
	global ExifDateTimeDigitized
	ExifDateTimeOriginal = 36867
	ExifDateTimeDigitized = 36868

	delta = timedelta(seconds=args.delta)
	tzGMT = timedelta(hours=args.tzPhoto)
	tzLocal = timedelta(hours=args.tzLocal)
	
	logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")
	
	if ('updategeo' in args.actions):
		points, dates = parseTrack(args.track)
	
	os.chdir(args.input)
	
	i = 0
	duplicateCount = 0
	prevGpsData = None
	
	for file in glob.glob("*." + args.ext):
		i = i + 1
		if args.top > 0 and i > args.top: break

		exif_dict = piexif.load(file)
		dts = exif_dict["Exif"][ExifDateTimeOriginal].decode("ASCII")
		d = datetime.strptime(dts,"%Y:%m:%d %H:%M:%S")
		dtupd = d

		logstr = file + ' ' + str(d)
		
		if 'updatetime' in args.actions:
			dtupd = d + delta + tzLocal - tzGMT
			exif_dict = setExifDateTime(exif_dict, dtupd)
			logstr = logstr + ' ' + str(dtupd)
			
		if 'updategeo' in args.actions:
			coords = getCoords(dtupd, points, dates)
			if coords is not None and not (2 in exif_dict["GPS"]): exif_dict = setExifGps(exif_dict, coords)
			GpsData = exif_dict["GPS"]
			exif_dict["GPS"], duplicateCount = setExifGpsAngle(GpsData, prevGpsData, duplicateCount)
			logstr = logstr + ' ' + str(duplicateCount) + ' ' + str(coords) + str(exif_dict["GPS"])
		
		outname = file
		if 'rename' in args.actions:
			outname = dtupd.strftime("%Y%m%d_%H%M%S_") + file

		if 'updategeo' in args.actions or 'updatetime' in args.actions:
			#print('copying ' + file + ' to ' + os.path.join(args.output, outname))
			exif_bytes = piexif.dump(exif_dict)
			im = Image.open(file)
			im.save(os.path.join(args.output, outname), exif=exif_bytes, subsampling=args.subsampling, quality=args.quality)
			if 'updategeo' in args.actions: 
				prevGpsData = GpsData
				
		elif 'rename' in args.actions:
			#print('copying ' + file + ' to ' + os.path.join(args.output, outname))
			copyfile(file, os.path.join(args.output, outname))
			
		logging.info(logstr)


def main():
	parser = argparse.ArgumentParser(description='Make some operations on photos')
	parser.add_argument('-i', '--input', dest='input', help='input folder', default='')
	parser.add_argument('-o', '--output', dest='output', help='output folder', default='')
	parser.add_argument('-e', '--ext', dest='ext', help='file extension', default='jpg')
	parser.add_argument('-t', '--track', dest='track', help='path and filename of GPX track', default='track.gpx')
	parser.add_argument('-d', '--delta', dest='delta', help='time difference between GPX and photo timestamps in seconds, ignoring timezone', default=0, type=int)
	parser.add_argument('-z', '--tzLocal', dest='tzLocal', help='local timezone, hours from UTC', default=0, type=int)
	parser.add_argument('-y', '--tzPhoto', dest='tzPhoto', help='photos timestamp timezone, hours from UTC', default=0, type=int)
	parser.add_argument('-a', '--action', dest='actions', nargs='+', help='Actions: updatetime rename updategeo ')
	parser.add_argument('--top', dest='top', help='Only process first [top] files', default=0, type=int)
	parser.add_argument('--subsampling', dest='subsampling', help='JPEG chroma subsampling', default=0, type=int)
	parser.add_argument('--quality', dest='quality', help='JPEG quality', default=85, type=int)
	
	args = parser.parse_args()

	processImages(args)
	
	
if __name__ == "__main__":
	main()