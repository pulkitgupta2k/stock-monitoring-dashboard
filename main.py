from bs4.element import Script
from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)

import grequests
import gspread
import json
from bs4 import BeautifulSoup

API_KEYS = [""]
gc = gspread.service_account("key.json")
sh = gc.open("Copy of v.03 stock monitoring dashboard")
data = {}
API_KEY = API_KEYS[0]
HEADER = {"X-QFS-API-Key": API_KEY}

def get_jsons(urls):
    MAX_CONNECTIONS = 100
    requests = []
    for x in range(0, len(urls), MAX_CONNECTIONS):
        rs = (grequests.get(u, stream=False, headers = {"User-Agent": "PostmanRuntime/7.26.8"})
              for u in urls[x:x+MAX_CONNECTIONS])
        response = grequests.map(rs)
        requests.extend(response)
        print(response)
    responses = []
    for request in requests:
        try:
            js = request.json()
            responses.append(js)
        except:
            pass
    return responses

def get_soups(urls):
    MAX_CONNECTIONS = 100
    requests = []
    for x in range(0, len(urls), MAX_CONNECTIONS):
        rs = (grequests.get(u, stream=False, headers = {"User-Agent": "PostmanRuntime/7.26.8"})
              for u in urls[x:x+MAX_CONNECTIONS])
        response = grequests.map(rs)
        requests.extend(response)
        print(response)
    soups = []
    for request in requests:
        try:
            html = request.content
            soup = BeautifulSoup(html, "html.parser")
            soups.append(soup)
        except:
            pass
    return soups


# def get_companies():
#     global HEADER
#     url = "https://public-api.quickfs.net/v1/companies/US"
#     return requests.get(url, headers=HEADER).json()

# def get_all_tickers():
#     global data
    
#     for tick in get_companies()["data"]:
#         data[tick.split(':')[0]] = []
    
#     with open("data.json", "w") as f:
#         json.dump(data, f)


def get_tickers_data():
    l = []
    with open("data.json") as f:
        data = json.load(f)
    for key in data.keys():
        l.append(key)
        if len(l) >= 100:
            get_tickers_data_100(l)
            l = []

def get_tickers_data_100(tickers):
    data = {}
    quickfs_links = []
    yahoo_links = []

    for ticker in tickers:
        quickfs_links.append(f"https://api.quickfs.net/stocks/{ticker}:US/ovr/Annual/")
        yahoo_links.append(f"https://finance.yahoo.com/quote/{ticker}")

    quickfs_response = get_jsons(quickfs_links)
    yahoo_response = get_soups(yahoo_links)

    for response in quickfs_response:
        try:
            data[response["qfs_symbol_v2"]] = {
                "description" : response["datasets"]["metadata"]["description"],
                "exchange": response["datasets"]["metadata"]["exchange"],
                "sector": response["datasets"]["metadata"]["sector"],
                "subindustry": response["datasets"]["metadata"]["subindustry"],
                "industry": response["datasets"]["metadata"]["industry"],
                "market_cap" : response["datasets"]["metadata"]["mkt_cap"],
                "price" : response["datasets"]["metadata"]["price"],
                "pe": response["datasets"]["metadata"]["pe"],
                "ev_ebitda": response["datasets"]["metadata"]["ev_ebitda"],
                "gics": response["datasets"]["metadata"]["gics"]
            }
        except:
            pass

    with open("temp.json", "w") as f:
        json.dump(data, f) 
    return data

def get_yahoo_data(soup):
    data = {}
    for script in soup.findAll("script"):
        if "root.App.main" in str(script):
            str_data = str(script).split("root.App.main = ")[1][:-21]
            json_data = json.loads(str_data)

            ticker = json_data["context"]["dispatcher"]["stores"]["PageStore"]["pageData"]["symbol"]
            low_52 = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["fiftyTwoWeekLow"]["raw"]
            high_52 = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["fiftyTwoWeekHigh"]["raw"]
            revenue = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalRevenue"]["raw"]
            price = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["currentPrice"]["raw"]
            cash = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalCash"]["raw"]
            debt = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalDebt"]["raw"]
            op_cash_flow = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["operatingCashflow"]["raw"]
            free_cash_flow = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["freeCashflow"]["raw"]
            enterprise_value = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["enterpriseValue"]["raw"]


if __name__ == "__main__":
    soup = get_soups(["https://finance.yahoo.com/quote/AAPL/key-statistics?p=AAPL"])[0]
    get_yahoo_data(soup)

    # with open("test.html", "w") as f:
    #     f.write(str(soup))

    # get_tickers_data()
    # get_all_tickers()
    # ws = sh.get_worksheet(1)
    # print(ws)