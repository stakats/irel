# iREL eater
This code allows you to download digitized documents directly from the Archives nationales d'Outre-Mer's iREL service (instruments de recherche en ligne), bypassing the hosting site's Java-based viewer.

## Requirements
* Python 3
  * required packages: backoff, requests, bs4
* ImageMagick

Python 3 and ImageMagick can be installed via homebrew. Then use `pip3` to install the backoff, requests, and bs4 modules.

## From the command line ##
Documents are retrieved using their unique ark (archival resource key) ID. Each digitized document at ANOM has an ark ID associated with it, e.g. by navigating to http://anom.archivesnationales.culture.gouv.fr/ark:/61561/ou533mgofje we find `ark:/61561/ou533mgofje` listed on the page (and also in the URL).

`python3 ./irel.py ark:/61561/ou533mgofje`

By default the document will save to the location of the script, but you can also specify a different destination folder:
`python3 ./irel.py ark:/61561/ou533mgofje /Users/stakats/Desktop`

## From within Safari ##
Using Safari on macOS, you can download documents directly from the browser.

### Initial setup ###
This is a one-time setup that won't need to be done again.
1. Open `ANOM IREL.workflow` in Automator.app (installed by default in macOS Applications)
2. Under the `Get Specified Finder Items` step click `Add...` and navigate to the irel.py python script, and then do the same for the download folder you'd like to use for your retrieved documents. Then `Remove` the example items that were already in that step. Make sure that the `irel.py` item is listed above the download folder you selected. If they're inverted, you can drag them into the desired order.
3. Under `File -> Convert to...` select `Service` and click OK.

### Usage ###
1. Navigate to a ANOM IREL page, e.g. http://anom.archivesnationales.culture.gouv.fr/ark:/61561/ou533mgofje
2. Under the `Safari -> Services` menu, select `ANOM IREL` (you can also set a shortcut key).
