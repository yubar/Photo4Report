chcp 65001
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -o "r:\photo\20190721 ВАХ\4mpl" -a cleangeo --top 100
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -d -468 -z 8 -y 3 -a rename updatetime
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -o "r:\photo\20190721 ВАХ\4mpl"  -t "VAH_my.gpx" -z 8 -y 3 -a updategeo --onlygeo

rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_t" -o "r:\photo\20190721 ВАХ\4mpl_t2" -d 436 -z 8 -y 2 -a rename updatetime



rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_t2" -o "r:\photo\20190721 ВАХ\4mpl_t" -a cleangeo

rem phototools.py -i "r:\photo\20200727 Приполярный\Export_mpl" -o "r:\photo\20200727 Приполярный\tst"  -t "ppu.gpx" -z 3 -y 3 -d 69 -a updatetime updategeo --onlygeo --threshold 30
phototools.py -i "r:\photo\20200727 Приполярный\pano" -o "r:\photo\20200727 Приполярный\tst2"  -t "ppu.gpx" -z 3 -y 3 -d 69 -a updatetime updategeo --onlygeo --threshold 30
rem phototools.py -i "r:\photo\20200727 Приполярный\Export" -o "r:\photo\20200727 Приполярный\tst"  -t "ppu.gpx" -z 3 -y 3 -d 69 -a updatetime cleangeo --top 15