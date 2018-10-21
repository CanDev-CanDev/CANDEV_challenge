"""
Used to scrape team FDA warnings
"""

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import pandas as pd
import re

url_key = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
           'X', 'Y', 'Z', '0-9']


def get_url(url):
    """
    Get the url
    :param url: given url
    :return: raw html
    """
    response = requests.Session()
    retries = Retry(total=10, backoff_factor=.1)
    response.mount('http://', HTTPAdapter(max_retries=retries))

    try:
        response = response.get(url, timeout=5)
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
        return None

    return response


def scrape_data(key):
    """
    Parses html from the FDA website to compile a list of companies who have had an FDA warning issued against them
    :return: an array of company and warning info
    """

    # obtain the full html text
    try:
        html = get_url('https://www.accessdata.fda.gov/scripts/warningletters/wlSearchResult.cfm?firstChar={}'.format(key))
        time.sleep(1)
    except Exception as e:
        raise Exception

    soup = BeautifulSoup(html.content, 'html.parser')
    table = soup.find_all('td')

    arr = [x.get_text() for x in table]

    # the below code is used to strip unnecessary html tags
    arr = [re.split('\xa0', i) for i in arr]
    for i, j in reversed(list(enumerate(arr))):
        for k, l in reversed(list(enumerate(arr[i]))):
            arr[i][k] = arr[i][k].replace('\t', '')
            arr[i][k] = arr[i][k].replace('\r\n', ' ')
            arr[i][k] = arr[i][k].strip()
            if arr[i][k] == '':
                arr[i].pop(k)

    # remove headers and footer
    del arr[0:14]
    del arr[-1]

    # split by row
    arr = [arr[i:i + 6] for i in range(0, len(arr), 6)]

    for i, j in reversed(list(enumerate(arr))):
        for k, l in reversed(list(enumerate(arr[i]))):
            if k == 3:
                arr[i][k] = [" - ".join(arr[i][k])]

    # add the warning report urls
    soup = BeautifulSoup(html.content, 'html.parser')
    table = soup.find_all('a', href=True)

    warnings = []
    for x in table:
        warnings.append(str(x).replace("&amp;", "&"))
    for i, j in enumerate(list(warnings)):
        warnings[i] = warnings[i].split("title=")

    ind = warnings.index(['<a href="wlAdvancedSearch.cfm" ', '"Advanced Search">Advanced Search</a>']) + 1
    for i, j in enumerate(list(arr)):
        arr[i].append([warnings[ind][0][9:warnings[ind][0].rindex('"')]])

        '''
        # extract contact info from warning reports
        try:
            html = get_url(warnings[ind][0][9:warnings[ind][0].rindex('"')])
            time.sleep(1)
        except Exception as e:
            raise Exception

        soup = BeautifulSoup(html.content, 'html.parser')
        table = soup.findAll("div")

        arr = [x.get_text(separator='div') for x in table]
        arr = [re.split('\xa0|\n|div', i) for i in arr]

        for m, n in reversed(list(enumerate(arr))):
            for o, p in reversed(list(enumerate(arr[m]))):
                arr[m][o] = arr[m][o].strip()
                if arr[m][o] == '' or arr[m][o] == ' ':
                    arr[m].pop(o)

        contact = ""
        ind2 = arr[1].index('WARNING LETTER') + 2
        print(arr)
        while len(arr[1][ind2]) < 4 or arr[1][ind2][0:4] != 'Dear':
            contact += arr[1][ind2] + " "
            ind2 += 1

        # contact_list = []
        # i = re.search('\d', contact)
        # contact_list.append(contact[0:i.start()].strip())
        # contact_list.append(contact[i.start():len(contact) + 1].strip())

        arr[i].append([contact])
        '''

        ind += 1

    return arr


def parse_data():
    """
    create dataframe with all warnings issued by the FDA that are on record, along with associated company info
    :return: dataframe with all records
    """
    arr = []
    for key in url_key:
        page = scrape_data(key)
        for i in page:
            arr.append(i)

    headers = ['LEGAL_NAME', 'WARNING_ISSUED_DATE', 'ISSUING_OFFICE', 'DETAILS', 'RESPONSE_LETTER_POSTED',
               'CLOSEOUT DATE', 'WARNING_LETTER']
    df = pd.DataFrame(arr, columns=headers)
    # covert data from list to str for formatting
    for header in headers:
        df[header] = df[header].str[0]
    df.to_excel("FDA_warnings.xlsx", index=False)

    return df

print(parse_data())
