import time
import os
import telepot
from base64 import b64encode
from os import makedirs
from os.path import join, basename
import json
import requests
from googletrans import Translator
import goslate
import argparse
import io
from google.cloud import vision
from google.cloud.vision import types
from google.cloud import translate


import subprocess
from telepot.delegate import per_chat_id, create_open, pave_event_space
from telepot.loop import MessageLoop

ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
RESULTS_DIR = 'jsons'
makedirs(RESULTS_DIR, exist_ok=True)
API_KEY= '<GOOGLE API KEY HERE>'
rawtext=''
translatedtext = ''
translate_client = translate.Client()


def make_image_data_list(image_filenames):
    """
    image_filenames is a list of filename strings
    Returns a list of dicts formatted as the Vision API
        needs them to be
    """
    img_requests = []
    #for imgname in image_filenames:
    with open(image_filenames, 'rb') as f:
        ctxt = b64encode(f.read()).decode()
        img_requests.append({
            'image': {'content': ctxt}, 'features': [{'type': 'TEXT_DETECTION', 'maxResults': 1}] })
    return img_requests

def make_image_data(image_filenames):
    """Returns the image data lists as bytes"""
    imgdict = make_image_data_list(image_filenames)
    return json.dumps({"requests": imgdict }).encode()

def request_ocr(api_key, image_filenames):
    response = requests.post(ENDPOINT_URL,
                             data=make_image_data(image_filenames),
                             params={'key': api_key},
                             headers={'Content-Type': 'application/json'})
    return response

def translate_text(text, language):
    try:
        translated= gs.translate(text, language)
        # translated = translator.translate(text)
        #print(" Source Language:" + translated.src)
        #print(" Translated string:" + translated.text)
        return translated
    finally:
        print("Complete")

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type in ['photo']:
        content = msg[content_type]  #if content_type == 'photo' else msg[content_type][-1]
        print("Got content ->: %s" % content)
        downloads_dir = 'downloaded_images'
        os.makedirs(downloads_dir, exist_ok=True)
        temp_path = os.path.join(downloads_dir,
                                 'chat_%d_id_%d_temp.jpeg' % (chat_id, msg['message_id']))

        filename = content[len(content)-1]['file_id']
        bot.download_file(filename, temp_path)
        time.sleep(2)
        print("File has been saved under : %s" % downloads_dir)
        print("%s" % temp_path)

        response = request_ocr(API_KEY, temp_path)
        if response.status_code != 200 or response.json().get('error'):
            print(response.text)
        else:
            for idx, resp in enumerate(response.json()['responses']):
                # save to JSON file
                jpath = join(RESULTS_DIR, basename(filename) + '.json')
                print("%s" % jpath)
                with open(jpath, 'w') as f:
                    datatxt = json.dumps(resp, indent=2)
                    print("Wrote", len(datatxt), "bytes to", jpath)
                    f.write(datatxt)

                # print the plaintext to screen for convenience
                print("---------------------------------------------")
                t = resp['textAnnotations'][0]
                print("    Text:")
                rawtext = t['description']
        print(rawtext)

        translatedtext = translate_client.translate(rawtext, 'en')
        bot.sendMessage(chat_id, translatedtext['translatedText'])

    elif content_type in ['text']:
        content = msg[content_type]
        testdata= 'Hi There'
        #print("Got content ->: %s" % translate_text(testdata.strip()))
        bot.sendMessage(chat_id, translate_text(testdata.strip()))
    else:
        print("Sorry wrong request")


bot = telepot.Bot('<TELEGRAM BOT TOKEN HERE>')

bot.message_loop(handle)
print ("I am listening ...")
while 1:
    time.sleep(10)
