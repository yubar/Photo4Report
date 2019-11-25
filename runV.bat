chcp 65001
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -o "r:\photo\20190721 ВАХ\4mpl" -a cleangeo --top 100
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -d -468 -z 8 -y 3 -a rename updatetime
rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_my" -o "r:\photo\20190721 ВАХ\4mpl"  -t "VAH_my.gpx" -z 8 -y 3 -a updategeo --onlygeo

rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_t" -o "r:\photo\20190721 ВАХ\4mpl_t2" -d 436 -z 8 -y 2 -a rename updatetime



rem phototools.py -i "r:\photo\20190721 ВАХ\4mpl_t2" -o "r:\photo\20190721 ВАХ\4mpl_t" -a cleangeo

phototools.py -i "r:\photo\20190721 ВАХ\4mpl_t" -o "r:\photo\20190721 ВАХ\4mpl"  -t "VAH_a.gpx" -z 8 -a updategeo --onlygeo --threshold 30