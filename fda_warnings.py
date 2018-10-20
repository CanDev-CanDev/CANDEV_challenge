"""
Used to scrape team FDA warnings
"""

from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np
import re
from helper import get_url

url_key = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
              'W', 'X', 'Y', 'Z', '0-9']


def scrape_data(key):
    """
    Scrapes the FDA website to compile a list of companies who have had a warning issued against them
    :return: an array of arrays from the given key page with all html tags stripped from the text
    """

    try:
        html = get_url('https://www.accessdata.fda.gov/scripts/warningletters/wlSearchResult.cfm?firstChar={}'.format(key))
        time.sleep(1)
    except Exception as e:
        raise Exception

    soup = BeautifulSoup(html.content, 'html.parser')
    table = soup.find_all('td')

    arr = [x.get_text() for x in table]

    # the below code is used to strip unnecessary html tags
    arr = [re.split('\xa0|\n', i) for i in arr]
    for i,j in reversed(list(enumerate(arr))):
        for k,l in reversed(list(enumerate(arr[i]))):
            arr[i][k] = arr[i][k].replace('\t', '')
            arr[i][k] = arr[i][k].replace('\r', '')
            if arr[i][k] == '':
                arr[i].pop(k)

    # remove headers and footer
    del arr[0:14]
    del arr[-1]

    # split by row
    arr = [arr[i:i + 6] for i in range(0, len(arr),6)]

    for i,j in reversed(list(enumerate(arr))):
        for k,l in reversed(list(enumerate(arr[i]))):
            if k == 3:
                arr[i][k] = [" - ".join(arr[i][k])]

    return arr


def parse_data():
    """
    create dataframe with all warnings issued by the FDA that are on record
    :return: dataframe with all records
    """
    arr = []
    for key in url_key:
        page = scrape_data(key)
        for i in page:
            arr.append(i)

    headers = ['LEGAL_NAME', 'WARNING_ISSUED_DATE', 'ISSUING_OFFICE', 'DETAILS', 'RESPONSE_LETTER_POSTED',
               'CLOSEOUT DATE']
    df = pd.DataFrame(arr, columns=headers)
    df['WARNING_LETTER'] = np.NaN
    # covert data from list to str for formatting
    for header in headers:
        df[header] = df[header].str[0]
    # df.to_excel("FDA_warnings.xlsx", index=False)

    return df

# print(parse_data())

try:
    html = get_url('https://www.accessdata.fda.gov/scripts/warningletters/wlSearchResult.cfm?firstChar={}'.format('A'))
    time.sleep(1)
except Exception as e:
    raise Exception

soup = BeautifulSoup(html.content, 'html.parser')
table = soup.find_all('a', href=True)

paragraphs = []
for x in table:
    paragraphs.append(str(x).replace("&amp;", "&"))
for i, j in enumerate(list(paragraphs)):
    paragraphs[i] = paragraphs[i].split("title=")

print(paragraphs)

df = parse_data()

for i in df['LEGAL_NAME'].values:
    for j in paragraphs:
        if len(j) > 1 and j[0][1:9] == 'a href="' and j[1][1:j[1].rindex('"')] == df.loc[[i]['LEGAL_NAME']]:
            df.loc[[i]['WARNING_LETTER']] = j[0][9:j[0].rindex('"')]

print(df)
