import urllib2

def geo(zipcode):
    content = urllib2.urlopen("http://codigospostales.dices.net/mapacodigopostal.php?codigopostal=%s" % zipcode).read()
    print content.split('Esta es tu localizacion:<br><br>Latitud: ')[1].split("'")[0]

print geo(48993)
