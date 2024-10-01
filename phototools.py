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
	start = datetime.now()
	print("Parsing gpx... ", end="")
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
	print("Completed in " + str(datetime.now()-start))
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
	#print('setExifGps coords:', coords)
	GpsData = dict()
	
	GpsData[1] = ("N" if coords[1]>=0 else "S").encode("ASCII")
	GpsData[2] = dd2dms(coords[1])
	GpsData[3] = ("E" if coords[2]>=0 else "W").encode("ASCII")
	GpsData[4] = dd2dms(coords[2])
	GpsData[6] = (int((coords[3] if coords[3]>0 else 0) * 1000), 1000)
	#GpsData[16] = "T".encode("ASCII")
	#GpsData[17] = (int(coords[4] * 1000), 1000)
	
	exif["GPS"] = GpsData
	
	#print('setExifGps exif["GPS"]:', exif["GPS"])
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

def processImages(args, files, num):
	
	delta = timedelta(seconds=args.delta)
	tzPhotoFromGMT = timedelta(hours=args.tzPhoto)
	tzTargetFromGMT = timedelta(hours=args.tzTarget)
	
	if ('updategeo' in args.actions):
		points, dates = parseTrack(args.track)
	
	os.chdir(args.input)
	
	i = 0
	duplicateCount = 0
	prevGpsData = None
	
	start = datetime.now()
	
	dayno = 0
	prevdate = start
	
	for file in files:
		i = i + 1
		if args.top > 0 and i > args.top: break
		
		if i%10 == 0: print("\rProcessing files: " + str(i) + " of " + str(num) + '...', end='')
		
		exif_dict = piexif.load(file)
		del exif_dict["thumbnail"]
		
		dts = exif_dict["Exif"][ExifDateTimeOriginal].decode("ASCII")
		d = datetime.strptime(dts,"%Y:%m:%d %H:%M:%S")
		dtupd = d - tzPhotoFromGMT + delta + tzTargetFromGMT
		
		if dayno == 0:
			dayno = 1
			prevdate = dtupd.date()
		elif (dtupd.date()-prevdate).days > 0:
			dayno = dayno + (dtupd.date()-prevdate).days
			prevdate = dtupd.date()
		logstr = file + ' ' + str(d)
		
		if 'updatetime' in args.actions:
			exif_dict = setExifDateTime(exif_dict, dtupd)
			logstr = logstr + ' ' + str(dtupd)
		
		if 'updategeo' in args.actions:
			GpsData = exif_dict["GPS"]
			if not (2 in exif_dict["GPS"]):
				coords = getCoords(dtupd - tzTargetFromGMT, points, dates, timedelta(seconds = args.threshold))
				if coords is not None: exif_dict = setExifGps(exif_dict, coords)
				GpsData = exif_dict["GPS"]
				exif_dict["GPS"], duplicateCount = setExifGpsAngle(GpsData, prevGpsData, duplicateCount)
				logstr = logstr + ' ' + str(duplicateCount) + ' ' + str(coords)
			logstr = logstr + ' ' + str(exif_dict["GPS"])
		
		if 'cleangeo' in args.actions:
			exif_dict["GPS"] = {}
			logstr = logstr + ' geodata erased' 
		
		outname = file
		
		if 'rename' in args.actions:
			outname = dtupd.strftime("%Y%m%d_%H%M%S_") + file
		
		if 'updategeo' in args.actions or 'cleangeo' in args.actions or 'updatetime' in args.actions:

			if not args.onlygeo or exif_dict["GPS"]:
				exif_bytes = piexif.dump(exif_dict)
				im = Image.open(file)
				im.save(os.path.join(args.output, outname), exif=exif_bytes, subsampling=args.subsampling, quality=args.quality)

			if 'updategeo' in args.actions: 
				prevGpsData = GpsData
				
		elif 'rename' in args.actions:
			#outname = f'{dayno:02d}' + '_' + outname
			#logstr = logstr + ' ' + outname
			#print('copying ' + file + ' to ' + os.path.join(args.output, outname))
			copyfile(file, os.path.join(args.output, outname ))
			
		logging.info(logstr)
		
	print("\rProcessing files: " + str(i) + " of " + str(num) + '... Completed in ' + str(datetime.now()-start))

def panosort(args, files, num):
	
	panocount = 0
	i = 0
	prevExif = None
	exif_dict = None
	params = {}
	prevParams = {}
	isPano = False
	
	for file in files:
		i = i + 1
		if args.top > 0 and i > args.top: break
		if i%10 == 0: print("\rProcessing files: " + str(i) + " of " + str(num) + '...', end='')
		
		logstr = ''
		
		prevParams = params.copy()
		prevExif = exif_dict
		exif_dict = piexif.load(file)
		
		params["file"] = file
		params["date"] = datetime.strptime(
			exif_dict["Exif"][ExifDateTimeOriginal].decode("ASCII")
			,"%Y:%m:%d %H:%M:%S"
		)
		params["focalLength"] = exif_dict["Exif"][ExifFocalLength]
		
		with Image.open(file) as image:
			width, height = image.size
			params["orientation"] = "Landscape" if width >= height else "Portrait"
		
		logstr = logstr + ' ' + str(params)
		
		if i == 1: 
			logging.info(logstr)
			continue
		else:
			if (
				((params["date"] - prevParams["date"]).seconds <= args.diff)
				and (params["orientation"] == prevParams["orientation"])
				and (params["focalLength"] == prevParams["focalLength"])
			):
				if not isPano:
					isPano = True
					panocount = panocount + 1
					targetPath = os.path.join(args.output, str(panocount).zfill(3))
					if not os.path.exists(targetPath): os.makedirs(targetPath)
					copyfile(prevParams["file"], os.path.join(targetPath, prevParams["file"]))
				
				copyfile(params["file"], os.path.join(targetPath, params["file"]))
			else: 
				isPano = False
				
			logstr = logstr + ' ' + str(isPano) + ' ' + str(panocount).zfill(3)
			
		logging.info(logstr)

def main():

	#https://exiftool.org/TagNames/EXIF.html
	global ExifDateTimeOriginal
	global ExifDateTimeDigitized
	global ExifFocalLength
	global Orientation
	ExifDateTimeOriginal = 0x9003
	ExifDateTimeDigitized = 0x9004
	ExifFocalLength = 0x920a
	Orientation = 0x0112
	
	logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")
	logging.getLogger('PIL').setLevel(logging.WARNING)
	
	parser = argparse.ArgumentParser(description='Make some operations on photos')
	parser.add_argument('-i', '--input', dest='input', help='input folder', default='')
	parser.add_argument('-o', '--output', dest='output', help='output folder', default='')
	parser.add_argument('-e', '--ext', dest='ext', help='file extension', default='jpg')
	parser.add_argument('-t', '--track', dest='track', help='path and filename of GPX track', default='track.gpx')
	parser.add_argument('-d', '--delta', dest='delta', help='time difference between GPX and photo timestamps in seconds, ignoring timezone', default=0, type=int)
	parser.add_argument('-z', '--tzTarget', dest='tzTarget', help='target timezone, hours from UTC', default=0, type=int)
	parser.add_argument('-y', '--tzPhoto', dest='tzPhoto', help='photos timestamp timezone, hours from UTC', default=0, type=int)
	parser.add_argument('-a', '--action', dest='actions', nargs='+', help='Actions: updatetime rename updategeo panosort')
	parser.add_argument('--top', dest='top', help='Only process first [top] files', default=0, type=int)
	parser.add_argument('--threshold', dest='threshold', help='Max difference between shooting time and gpx point to assign coords, seconds', default=15, type=int)
	parser.add_argument('--subsampling', dest='subsampling', help='JPEG chroma subsampling', default=0, type=int)
	parser.add_argument('--quality', dest='quality', help='JPEG quality', default=85, type=int)
	parser.add_argument('--onlygeo', dest='onlygeo', help='Copy only geotagged files to output folder', default=False, action='store_true')
	parser.add_argument('--diff', dest='diff', help='Max time difference between photos to consider them a pano, seconds', default=7, type=int)
	
	args = parser.parse_args()
	
	os.chdir(args.input)
	files = glob.glob("*." + args.ext)
	num = len(files) if args.top == 0 else min(args.top, len(files))
	
	print(str(len(files)) + ' files found')
	
	if 'panosort' in args.actions:
		panosort(args, files, num)
	else:
		processImages(args, files, num)
	
if __name__ == "__main__":
	main()