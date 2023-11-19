Get-ChildItem -Path . -Filter "*.mov" | ForEach-Object {
	$dt = ffprobe -i $_ -v 0 -show_entries format_tags=com.apple.quicktime.creationdate -of default=nw=1:nk=1
	$dt2=$dt -replace ".{5}$" -replace ":",""  -replace ":","" -replace "T","_" -replace "-",""

	#$qq = [datetime]::parseexact($dt, 'yyyy-MM-ddTHH:mm:sszz00', $null).ToString('yyyyMMdd_HHmmss')
	$NewFilename = $dt2 + "_" + $_.BaseName + $_.Extension
	#$NewFilename
	Rename-Item $_.FullName $NewFilename
}
