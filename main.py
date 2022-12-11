import csv
import io
import os
import re
import shutil
import sys
import time
from datetime import datetime
from json import dumps

import pyautogui
from fuzzywuzzy import fuzz, process
from PIL import Image
from pytesseract import pytesseract

categories = {
    'Boende & Hushall': ['Lan & Skatter', 'Drift', 'Forsakring', 'Media & Tele', 'Tjanster & Avgifter', 'Underhall & Renovering', 'Ovrigt'],
    'Fritid & Noje': ['Sport & Fritid', 'Semester & Resor', 'Kultur & Musik', 'Ovrigt'],
    'Shopping': ['Sport & Fritid', 'Ovrigt', 'Klader & Accessoarer', 'Tradgard & Blommor', 'Mobler & Inredning', 'Media & Bocker', 'Presenter', 'Skonhet', 'Hemelektronik'],
    'Mat & Dryck': ['Livsmedel', 'Alkohol', 'Café & Kiosk', 'Restaurang & Bar', 'Ovrigt'],
    'Ovrigt': ['Kontantuttag', 'Barn', 'Valgorenhet', 'Apotek & Vard', 'Okategoriserat', 'Ovrigt'],
    'Transport': ['Bil & Bransle', 'Kollektivt', 'Tag & Buss', 'Taxi', 'Ovrigt']
}

#Define path to tessaract.exe
path_to_tesseract = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
#Define path to image
path_to_image = 'screenshot.png'
#Point tessaract_cmd to tessaract.exe
pytesseract.tesseract_cmd = path_to_tesseract

fields = ['year', 'month', 'domain', 'category', 'value']

def parse_screenshot():
    pyautogui.screenshot(path_to_image, region=(50,0, 1100, 1800))
    #Open image with PIL
    img = Image.open(path_to_image)
    #Extract text from image
    return pytesseract.image_to_string(img)


def get_domain(clean_lines):
    for cl in clean_lines:
        for k in categories.keys():
            if fuzz.partial_ratio(k,cl) > 90:
                if k == 'Ovrigt':
                    contains_number = any(char.isdigit() for char in cl)
                    if cl.startswith('<') or not contains_number:
                        return k
                else:
                    return k


def get_date(clean_lines):
    for cl in clean_lines:
        if re.search(r'\w{3} 20\d{2}', cl):
            m = re.search(r'(\w{3}) (20\d{2})', cl)
            year = m.group(2)
            month = m.group(1)
            return year, month
    

def parse_text(text):
    lines = text.splitlines()
    clean_lines = [i for i in lines if i and len(i.strip()) > 2]
    retval = []
    
    domain = get_domain(clean_lines)
    year, month = get_date(clean_lines)
    assert domain is not None
    assert year is not None
    assert month is not None
    
    for cl in clean_lines:
        for category in categories[domain]:
            #print(category + " -> " + cl + ": " + str(fuzz.partial_ratio(category, cl)))
            if fuzz.partial_ratio(category, cl) > 80 and re.search(r' \d[ \d]+ kr', cl):
                retval.append({
                    'domain': domain,
                    'year': year,
                    'month': month,
                    'category': category,
                    'value': re.search(r' \d[ \d]+ kr', cl).group().strip().replace(' kr', '').replace(' ', '')
                })
                break
    return retval


def get_output(folder):
    now = datetime.now()
    date_time = now.strftime("%Y%m%d-%H%M%S")
    return os.path.join(folder, 'budget_' + date_time + '.csv')


def store_csv(input, output_path):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, delimiter=';')
    writer.writeheader()
    writer.writerows(input)
    with open(output_path, 'w') as fd:
        output.seek(0)
        shutil.copyfileobj(output, fd)


results = []
command = 'n'
while command == 'n':
    text = parse_screenshot()
    print(text)
    parsed_text = parse_text(text)
    print('Parsed ' + str(len(parsed_text)) + ' entries')
    results.extend(parsed_text)
    command = input('Waiting for next command [n/q]: ')

os.remove(path_to_image)
store_csv(results, get_output(sys.argv[1]))
