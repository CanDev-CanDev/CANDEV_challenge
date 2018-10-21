"""
Used to scrape together a list of FDA warnings issued over the previous 6 years
The purpose is to flag food exporters to Canada if they have previously been deemed violators in other jurisdictions
e.g. https://www.accessdata.fda.gov/scripts/warningletters/wlSearchResult.cfm?firstChar=A
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


def main():
    parse_data()
    return


def get_url(url):
    """
    Get the html for a given url
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
    :param: alphabetical key for the desired search page url
    :return: a list of all warnings issued by the fda for companies starting with the given alphabetical key
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

    # the below code is used to strip any remaining html tags
    arr = [re.split('\xa0', i) for i in arr]
    for i, j in reversed(list(enumerate(arr))):
        for k, l in reversed(list(enumerate(arr[i]))):
            arr[i][k] = arr[i][k].replace('\t', '')
            arr[i][k] = arr[i][k].replace('\r\n', ' ')
            arr[i][k] = arr[i][k].strip()
            if arr[i][k] == '':
                arr[i].pop(k)

    # remove headers and footer for convenience
    del arr[0:14]
    del arr[-1]

    # split by row
    arr = [arr[i:i + 6] for i in range(0, len(arr), 6)]

    # join the subject array into one string
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

        # failed attempt to extract contact info from warning reports
        '''
        try:
            html = get_url(warnings[ind][0][9:warnings[ind][0].rindex('"')])
            time.sleep(1)
        except Exception as e:
            raise Exception

        soup = BeautifulSoup(html.content, 'html.parser')
        table = soup.findAll("div")

        arr2 = [x.get_text(separator='div') for x in table]
        arr2 = [re.split('\xa0|div', i) for i in arr2]

        for m, n in reversed(list(enumerate(arr2))):
            for o, p in reversed(list(enumerate(arr2[m]))):
                arr2[m][o] = arr2[m][o].replace('\t', '')
                arr2[m][o] = arr2[m][o].replace('\r\n', ' ')
                arr2[m][o] = arr2[m][o].strip()
                if arr2[m][o] == '' or arr2[m][o] == ' ':
                    arr2[m].pop(o)

        contact = ""
        address = ""

        try:
            marker = arr2[1].index(arr[i][0])
            while re.search('\d', arr2[1][marker - 1]) is None:
                contact += arr2[1][marker - 1] + " "
                marker -= 1
            contact = contact.strip()

            marker = arr2[1].index(arr[i][0])
            while re.search(r'.*(\d{5}(\-\d{4})?)$', arr2[1][marker + 1]) is None:
                address += arr2[1][marker + 1] + " "
                marker += 1
            address += arr2[1][marker + 1]
            address = address.strip()
            arr[i].append([contact])
            arr[i].append([address])
        except Exception as e:
            print("not able to parse contact/address info for {}".format(warnings[ind][0][9:warnings[ind][0].rindex('"')]))
            arr[i].append([""])
            arr[i].append([""])
            pass
        '''

        ind += 1

    return arr


def parse_data():
    """
    create dataframe with all warnings issued by the FDA that are on record, along with associated company info
    :return: dataframe with all records
    """

    # loop through the full alphabetical index to compile a list of all warnings
    arr = []
    for key in url_key:
        page = scrape_data(key)
        for i in page:
            arr.append(i)

    # create the dataframe
    headers = ['LEGAL_NAME', 'WARNING_ISSUED_DATE', 'ISSUING_OFFICE', 'DETAILS', 'RESPONSE_LETTER_POSTED',
               'CLOSEOUT DATE', 'WARNING_LETTER']
    df = pd.DataFrame(arr, columns=headers)
    # convert data from list to str for formatting purposes
    for header in headers:
        df[header] = df[header].str[0]
    df.to_excel("FDA_warnings.xlsx", index=False)

    return df

if __name__ == '__main__':
    main()
