import re

import lxml
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

sec_url = 'https://www.sec.gov'

def get_request(url):
    'Returns result of a http request to url.'
    return requests.get(url)

def create_url(cik):
    'Returns url of SEC 13F filings given a CIK.'
    return f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&owner=exclude&count=40'

def get_user_input():
    'Prompts user to enter a CIK number.'
    cik = input('Enter 10-digit CIK number: ')
    return cik

# ask user for CIK number
requested_cik = get_user_input()

# find mutual fund by CIK number on EDGAR
response = get_request(create_url(requested_cik))
soup = BeautifulSoup(response.text, 'html.parser')

# get name of mutual fund 
company_name_text = soup.find('span', {'class': 'companyName'}).getText()
company_name = re.sub(' CIK#.*$', '', company_name_text)

# find all document tags; a document tag links to another 
# route containing the relevant filing docs
document_tags = soup.findAll('a', id="documentsbutton")

# for each document tag, try to find the latest primary_doc.xml file
# note that primary_doc.xml files only appear in NPORT-P entries; these 
# are easy to parse so I chose to search for these specifically; if a 
# mututal fund does not have an NPORT-P filing, then nothing is scraped 
for document_tag in document_tags:
    response = get_request(sec_url + document_tag['href'])
    soup = BeautifulSoup(response.text, "html.parser")

    # find file tag labeled primary_doc.xml; this is the 
    # standard filename for NPORT-P filings
    file_tag = soup.find(
        'a',
        text='primary_doc.xml',
        attrs={'href': re.compile('.*primary_doc.xml$')}
    )

    # if there is no primary_doc.xml skip this document page
    if file_tag is None:
        continue

    print(f'\nScraping Data from {company_name} (CIK: {requested_cik})...')
    print('--------------------------------------------------------------')
    print('Fetching xml file... ⌛')

    # scrape & parse the xml file
    xml_url = file_tag.get('href')
    response_xml = get_request(sec_url + xml_url)
    soup_xml = BeautifulSoup(response_xml.content, "lxml")

    print('Xml file fetched! 😊')
    print('\nParsing Progress:')

    holdings_data = []
    
    # find all holdings
    invstOrSecs = soup_xml.body.findAll(re.compile('invstorsec'))
    for invstOrSec in tqdm(invstOrSecs, bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}'):
        holding = {}

        # parse name
        name_text = invstOrSec.find('name').text
        holding['name'] = name_text if name_text != 'N/A' else None

    break