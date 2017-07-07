#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Sean Takats
# Note: requires ImageMagick with JP2 (jpeg 2000) support
# e.g. with homebrew on the mac, 'brew install imagemagick --with-jp2'
# this might be included by default now...

import os, math, binascii, argparse, backoff, requests
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("arkid", default='test')
parser.add_argument("directory", nargs='?', default=os.getcwd())
args = parser.parse_args()

arkid = args.arkid
directory = args.directory
os.chdir(directory)

# each ANOM dossier has a unique ID, e.g. ark:/61561/up424fz222yu

# use backoff and requests to handle timeouts and retry gracefully

@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_tries=8)
def get_url(url):
    return requests.get(url)

baseurl = 'http://anom.archivesnationales.culture.gouv.fr/'

url = baseurl + arkid
soup = BeautifulSoup(get_url(url).text, "lxml")

contentlink = soup.find('a', attrs={'target':'pix2web'})
dossier = contentlink.get('href')
dossier = (quote(dossier, '+?=&/'))

print ('Loading ' + arkid)

newurl = baseurl+dossier

soup = BeautifulSoup(get_url(newurl).text, "lxml")

docURL = soup.find('param', attrs={'name':'docUrl'}).get('value')
dossierURL = soup.find('param', attrs={'name':'from'}).get('value')
firstimage = int(soup.find('param', attrs={'name':'min'}).get('value'))
lastimage = int(soup.find('param', attrs={'name':'max'}).get('value'))
digits = soup.find('param', attrs={'name':'nbnum'}).get('value')
padding = '%0'+digits+'d'

totalimages = lastimage + 1 - firstimage

print ('Dossier contains ' + str(totalimages) + ' pages')

# get all the image pages

pdfcommand = 'convert \('
pdfname = url.split('ark:/61561/')[1] + ".pdf"
i = 0

for image in range (firstimage, lastimage+1): # pull each image page
    
    xmlrequest = baseurl+docURL+dossierURL+padding % image+'_img.xml'
    
    path = urlparse(xmlrequest).path
    path = os.path.dirname(path)
    
    soup = BeautifulSoup (get_url(xmlrequest).text, "lxml")

    i += 1
    print ('Grabbing image ' + str(i) + ' of ' + str(totalimages))

    imgurltemplate = soup.atiledimage['tilestreamspectemplate']
    
    imgsize = soup.layers.apyramidlayer.size
    tilesize = soup.layers.apyramidlayer.tilesize

    imgwidth = int(imgsize.get('width'))
    imgheight = int(imgsize.get('height'))
    tilewidth = int(tilesize.get('width'))
    tileheight = int(tilesize.get('height'))

    tileswide = math.ceil(imgwidth/tilewidth)
    tileshigh = math.ceil(imgheight/tileheight)

    filename = dossierURL.split('/')[1] + str(image) + ".jpg"

    jpgcommand = "convert -strip -interlace Plane -quality 85%"

    for x in range (tileswide): # download each tile image and build imagemagick command
        jpgcommand += " \( "
        for y in range (tileshigh):
            
            imgURL = baseurl + path + '/' + imgurltemplate % (y, x)
            
            # file to be written to
            file = urlparse(imgURL).path
            file = os.path.basename(file)
            file = os.path.join(directory, file)

            jpgcommand += " " + "'" + file + "'" 
 
            response = get_url(imgURL)
            hexcontent = binascii.hexlify(response.content)
            hexcontent = hexcontent[hexcontent.find(b'ff4fff51'):] # strip headers before jpeg2000 codestream

            content = binascii.unhexlify(hexcontent)
            f = open(file, 'wb')
            f.write(content)
            f.close()

        jpgcommand += " -append \)"

    jpgcommand += " +append " + "'" + os.path.join(directory, filename) + "'"
    pdfcommand += " "  + "'" + os.path.join(directory, filename) + "'"
    print ("Combining tiles and saving as a temporary JPEG")
    os.system(jpgcommand) # pasting the tiles together and saving as a jpg
    os.system('rm *TILE*') # removing temporary tile images

pdfcommand += " \) " + "'" + pdfname + "'"
print ('Saving images in a single PDF')
os.system(pdfcommand) # embedding all jpgs into a single pdf
print ('Cleaning up')
os.system('rm *.jpg') # deleting the temporary jpgs
                        
