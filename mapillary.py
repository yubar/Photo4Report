import os, glob
import json


def main():
	path = u"r:\\photo\\20190824 Камча 4\\fnl2map"
	os.chdir(path)
	i = 0
	SequenceUUID = None
	for file in glob.glob(".mapillary/**/sequence_process.json", recursive=True):
		i = i + 1
		with open(file, "r+") as hfile: 
			data = json.load(hfile)
			print(file + ' ' + str(data))
			
			if SequenceUUID is None: 
				SequenceUUID = data["MAPSequenceUUID"]
			else: 
				data["MAPSequenceUUID"] = SequenceUUID
			hfile.truncate(0)
			hfile.seek(0)
			json.dump(data, hfile, indent=4)

		#if i == 5: break

if __name__ == "__main__":
	main()