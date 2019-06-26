#import urllib
from lxml import etree
from pyppeteer import launch
from pyppeteer.errors import PageError
from sanic import response
from sanic.response import file_stream
from urllib.parse import unquote
import asyncio
import gzip
import os
import random
import sanic
from sanic.response import json
import shutil
import urllib.request
import zipfile
import pdb

app = sanic.Sanic()
app.config.RESPONSE_TIMEOUT = 6000

#
#
# @app.route('/screenshots/<data>')
# async def screenshots(request, data):
#   #make a folder to put the images in
#   elements = [ ['http://medialog.no', 'myimage.png'], ['http://plone.org', 'image2.png' ]]
#   print(data)
#   folder_id = "somefolder"
#   #image_name = "myimage.png"
#
#
#   if not os.path.exists(folder_id):
#     #maybe python3 mkdir-temporary
#     os.mkdir(folder_id)
#
#   for elem in elements:
#       await single_screenshot(elem[0], folder_id, elem[1])
#
#
#   return_text = 'rendering screensthots in folder {0} - come back later'.format(folder_id)
#   return response.text("http://localhost:5010/get_files/{0}".format(folder_id))

@app.route('/single_screenshot/<folder_name:string>/<image_name:string>/<mypath:path>', methods=['POST'])
async def single_screenshot(request, folder_name, image_name, mypath):
   #make a folder to save the images in
   if not os.path.exists(folder_name):
       os.mkdir(folder_name)

   path_name="{0}/{1}.png".format(folder_name, image_name)
   browser = await launch()
   page = await browser.newPage()
   await page.setViewport({'width': 1700, 'height': 1000})
   await page.goto(mypath)
   height = await page.evaluate("() => document.body.scrollHeight")
   await page.setViewport({'width': 1700, 'height': height})
   #wait for lazy loading images
   await asyncio.sleep(3)
   await page.screenshot({'path': path_name})
   await browser.close()
   return response.text(path_name)


@app.route('/sitemap/<mypath:path>', methods=['POST', 'GET'])
async def sitemap(request, mypath):
  #maybe add check for sitemap.xml
  sitemap = "{0}/sitemap.xml.gz".format(mypath)
  #get sitemap from Plone site
  sitemap = urllib.request.urlopen(sitemap)
  sitemap_data = gzip.decompress(sitemap.read())
  parser = etree.XMLParser(remove_blank_text=True)
  elem = etree.XML(sitemap_data, parser=parser)
  #make a folder to put the images in
  folder_id = "".join(mypath.split("."))
  folder_id = folder_id.replace("http://", "")
  folder_id = folder_id.replace("https/::", "-")
  random_n = str(random.random() * 100)
  folder_id =  '{0}-{1}'.format(folder_id, random_n)
  folder_id = folder_id.replace(".", "-")
  if not os.path.exists(folder_id):
    #maybe python3 mkdir-temporary
    os.mkdir(folder_id)

  no_screensthots = await screenshot_do(elem, folder_id)
  return_text = 'rendering screensthots in folder {0} - come back later'.format(folder_id)
  return response.text("http://localhost:5000/get_files/{0}".format(folder_id))


async def screenshot_do(elem, folder_id):
  shots = 0
  screenshots = []
  for element in elem:
    webpage = element[0].text
    pagename = webpage.replace("http://", "")
    pagename = pagename.replace(".", "-")
    pagename = pagename.replace("/", "-") + '.png'
    shots += 1
    screenshots.append(pagename)
    pathname = '{0}/{1}'.format(folder_id, pagename)
    exists = os.path.isfile(pathname)
    if exists:
        nothin = 0
    #print('done before: {0}'.format(pagename))
    else:
      # make preview with pyppeteer
      try:
          browser = await launch()
          page = await browser.newPage()
          await page.setViewport({'width': 1700, 'height': 3000})
          await page.goto(webpage)
          height = await page.evaluate("() => document.body.scrollHeight")
          await page.setViewport({'width': 1700, 'height': height})
          await page.screenshot({'path': pathname})
          await browser.close()
          #await print('saved screenshot: {0}'.format(pagename))
      except Exception:
         #need to do some checking here (?=)
         continue
      except PageError:
         #print('skipping link')
         continue
  return shots


async def screenshot(request, mypath):
  # make preview with pyppeteer
  try:
      browser = await launch()
      page = await browser.newPage()
      await page.setViewport({'width': 1700, 'height': 3000})
      await page.goto(mypath)
      height = await page.evaluate("() => document.body.scrollHeight")
      await page.setViewport({'width': 1700, 'height': height})
      await page.screenshot({'path': 'screenshot.png'})
      await browser.close()
      return await response.file('screenshot.png')

  except Exception:
      #need better checking
      pass

  except PageError:
      print('skipping link')
      pass

@app.route('/get_files/<name>', methods=['GET'])
def get_files(request, name):
   output_filename = name
   folder_id = name
   shutil.make_archive(output_filename, 'gztar', folder_id)
   return response.file('{0}.tar.gz'.format(output_filename))

@app.route('/get_file/<name>', methods=['GET'])
def get_file(request, name):
   return response.file('screenshots/{0}.png'.format(name))

#app.add_route(sitemap, '/sitemap/<mypath:path>')
#app.add_route(get_files, '/get_files/<name>')
#app.add_route(screenshot, '/screenshot/<mypath:path>')
#app.add_route(screenshot, '/screenshots/<list>')

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5010, workers=2)