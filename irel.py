#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Sean Takats
# Note: no longer requires ImageMagick with JP2 (jpeg 2000) support
# DZI / OpenSeadragon logic based on https://github.com/lovasoa/dezoomify

import os, math, argparse, backoff, requests, re, ast, json, shlex, warnings
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from bs4.builder import XMLParsedAsHTMLWarning
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

parser = argparse.ArgumentParser()
parser.add_argument("arkid", help='an id from the Archives nationales d\'Outre mer, e.g. ark:/61561/zn401lfekemv')
parser.add_argument("-f", dest='format', choices=['jpg', 'pdf'], default='pdf', help='save individual page images or a single PDF (default: pdf)')
parser.add_argument("-d", dest='directory', default=os.getcwd(), help='path to the resulting output (default: current directory)')
args = parser.parse_args()

arkid = args.arkid
outputformat = args.format
directory = args.directory
os.chdir(directory)

@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_tries=8)
def get_url(url):
    return requests.get(url)

baseurl = 'https://web.archive.org/web/20200806133054/http://anom.archivesnationales.culture.gouv.fr'

url = baseurl + '/' + arkid
soup = BeautifulSoup(get_url(url).text, "lxml")
contentlink = soup.find('a', href=re.compile(r'/web/\d+/http://.*?/osd/\?dossier='))

dossier = contentlink.get('href')

print ('Loading ' + arkid)
print ('Output will be '+outputformat)
newurl = re.sub(r'^/web/\d+/', '', dossier)
soup = BeautifulSoup(get_url(newurl).text, "lxml")

pattern = re.compile(r'initViewer')
script_tag = soup.find('script', string=pattern)

dzilist = script_tag.contents[0]
dzilist = dzilist.replace('\\/', '/')
dzilist = dzilist.split('[', 1)[1].split(']')[0]
dzilist = "["+dzilist+"]"

dzilist = ast.literal_eval(dzilist)

totalimages = len(dzilist)
print ('Dossier contains ' + str(totalimages) + ' pages')

# get all the image pages
pdfcommand = r'magick \('
pdfname = url.split('ark:/61561/')[1] + ".pdf"

i = 0
tempjpgs = ""

oldbaseurl = 'http://anom.archivesnationales.culture.gouv.fr'

for image in dzilist: # pull each image page

    temptiles = ""

    image = '"'+image+'"'
    image = json.loads(image)
    xmlrequest = oldbaseurl + image
    path = urlparse(xmlrequest).path
    path = os.path.dirname(path)
    soup = BeautifulSoup (get_url(xmlrequest).text, "lxml")

    i += 1
    print ('Grabbing image ' + str(i) + ' of ' + str(totalimages))

    tileimg = soup.image
    imgsize = tileimg.size
    imgformat = str(tileimg.get('format'))
    imgwidth = int(imgsize.get('width'))
    imgheight = int(imgsize.get('height'))
    tilesize = int(tileimg.get('tilesize'))
    overlap = int(tileimg.get('overlap'))
    tileswide = math.ceil(imgwidth/tilesize)
    tileshigh = math.ceil(imgheight/tilesize)
    zoom = math.ceil(math.log2(max(imgwidth, imgheight)))

    # replace .dzi extension with _files/
    tilebase = xmlrequest.rsplit( '.', 1 )[ 0 ] + '_files/'

    filename = urlparse(xmlrequest).path
    filename = filename.rsplit( '.', 1 )[ 0 ]+'.'+imgformat
    filename = os.path.basename(filename)
    filename = os.path.join(directory, filename)

    jpgcommand = r"magick "

    for x in range (tileswide): # download each tile image and build imagemagick command
        jpgcommand += r" \( "
        for y in range (tileshigh):
            
            imgURL = tilebase + str(zoom) + '/' + str(x) + '_' + str(y) + '.' + imgformat
            # file to be written to
            file = urlparse(imgURL).path
            file = os.path.basename(file)
            file = os.path.join(directory, file)

            jpgcommand += r" \( " + "'" + file + "'" + " -strip -shave "+str(overlap)+"x"+str(overlap)+r" \)"

            response = get_url(imgURL)

            f = open(file, 'wb')
            f.write(response.content)
            f.close()

            temptiles = temptiles + shlex.quote(file) + " "

        jpgcommand += r" -append \)"

    print ("Combining tiles and saving as a temporary JPG")
    jpgcommand += " +append " + "'" + os.path.join(directory, filename) + "'"
    pdfcommand += " "  + "'" + os.path.join(directory, filename) + "'"
    os.system(jpgcommand) # pasting the tiles together and saving as a jpg
    print ('Cleaning up tiles')
    os.system('rm ' + temptiles) # removing temporary tile images
    tempjpgs = tempjpgs + shlex.quote(filename) + " "

pdfcommand += r" \) " + "'" + pdfname + "'"

if (outputformat=='pdf'):
	print ('Saving images in a single PDF')
	os.system(pdfcommand) # embedding all jpgs into a single pdf
	os.system('rm ' + tempjpgs) # deleting the temporary jpgs
	print ('Cleaning up JPGs')
