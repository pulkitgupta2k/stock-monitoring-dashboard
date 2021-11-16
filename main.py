from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
from gspread.models import Worksheet
import time
from random import randrange
import grequests
import gspread
import json
from bs4 import BeautifulSoup
from pprint import pprint 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from creds import API_KEY


gc = gspread.service_account("key.json")
sh = gc.open("Stock Monitoring v1.0")

def open_tickers():
    with open("tickers.json") as f:
        tickers = json.load(f)
    return tickers

def divide(num, den):
    if den == 0:
        return 0
    return num/den

def get_jsons(urls, headers = {"User-Agent": "PostmanRuntime/7.26.8"}):
    MAX_CONNECTIONS = 100
    requests = []
    for x in range(0, len(urls), MAX_CONNECTIONS):
        rs = (grequests.get(u, stream=False, headers = headers)
              for u in urls[x:x+MAX_CONNECTIONS])
        response = grequests.map(rs)
        if response[0].status_code >= 300 and response[1].status_code >= 300:
            # print(response[0].status_code, response[1].status_code)
            #time.sleep(5)
            rs = (grequests.get(u, stream=False, headers = {"User-Agent": "PostmanRuntime/7.26.8"})
              for u in urls[x:x+MAX_CONNECTIONS])
            response = grequests.map(rs)
        requests.extend(response)
        # print("json")
        # print(response)
    responses = []
    for request in requests:
        try:
            js = request.json()
            responses.append(js)
        except:
            responses.append({})
            pass
    return responses

def get_soups(urls):
    MAX_CONNECTIONS = 100
    requests = []
    for x in range(0, len(urls), MAX_CONNECTIONS):
        rs = (grequests.get(u, stream=False, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"})
              for u in urls[x:x+MAX_CONNECTIONS])
        response = grequests.map(rs)
        if response[0].status_code >= 300 and response[1].status_code >= 300:
            # print(response[0].status_code, response[1].status_code)
            time.sleep(100)
            rs = (grequests.get(u, stream=False, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"})
              for u in urls[x:x+MAX_CONNECTIONS])
            response = grequests.map(rs)
        requests.extend(response)
        # print("soup")
        # print(response)
    soups = []
    for request in requests:
        try:
            html = request.content
            soup = BeautifulSoup(html, "html.parser")
            soups.append(soup)
        except:
            soups.append(None)
            pass
    return soups

def get_tickers_done():
    worksheet = sh.get_worksheet(0)
    tickers = worksheet.col_values(1)
    if len(tickers)>1:
        return set(tickers[1:])
    return set()


def get_companies():
    global API_KEY
    url = "https://public-api.quickfs.net/v1/companies/US"
    return get_jsons([url], {"X-QFS-API-Key": API_KEY})

def get_all_tickers():
    data = {}
    companies =  get_companies()[0]
    for tick in companies["data"]:
        data[tick.split(':')[0]] = []
    
    with open("tickers.json", "w") as f:
        json.dump(data, f)


def get_insider_json():
    global sh
    worksheet = sh.get_worksheet(1)
    tickers = worksheet.col_values(4)[1:]
    tickers_date = worksheet.col_values(3)[1:]
    tickers_type = worksheet.col_values(7)[1:]
    prices = worksheet.col_values(12)[1:]
    today = datetime.today()
    
    data = {}

    for i in range(len(tickers)):
        try:
            ticker = tickers[i]
            ticker_type = tickers_type[i]
            price = prices[i]
            ticker_date = datetime.strptime(tickers_date[i], "%Y-%m-%d")
            if ticker_type[0] != 'P':
                continue
            if ticker not in data.keys():
                data[ticker] = [0, 0, 0, 0, 0, 0, 0]
            days_delta = (today-ticker_date).days
            
            if days_delta < 365:
                data[ticker][0] += 1
                data[ticker][1] += float(price[2:].replace(",",""))
            if days_delta < 182:
                data[ticker][2] += 1
                data[ticker][3] += float(price[2:].replace(",",""))
            if days_delta < 91:
                data[ticker][4] += float(price[2:].replace(",",""))
            if days_delta < 30:
                data[ticker][5] += float(price[2:].replace(",",""))
            if days_delta < 7:
                data[ticker][6] += float(price[2:].replace(",",""))
        except:
            pass
    return data

def get_tickers_data(choice):
    l = []
    with open("tickers.json") as f:
        tickers = json.load(f)
    insider_json = get_insider_json()
    if choice == 3:
        done = get_tickers_done()
    elif choice == 4:
        clean_dashboard()
        done = set()
    options = Options()
    ser = Service("./chromedriver")
    options.headless = True
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(service=ser, options=options)
    for key in tickers.keys():
        if key in done:
            continue
        l.append(key)
        if len(l) >= 50:
            get_tickers_data_100(l, driver, insider_json)
            l = []
    get_tickers_data_100(l, driver, insider_json)
        
def get_tickers_data_100(tickers, driver, insider_json):
    data = {}
    quickfs_links = []
    yahoo_links = []

    for ticker in tickers:
        quickfs_links.append(f"https://api.quickfs.net/stocks/{ticker}:US/ovr/Annual/")
        yahoo_links.append(f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}")

    quickfs_response = get_jsons(quickfs_links)
    i = 0
    for response in quickfs_response:
        try:
            try:
                gic = int(response["datasets"]["metadata"]["gics"])
            except:
                gic = ""
            data[tickers[i]] = {
                "description" : response["datasets"]["metadata"]["description"],
                "exchange": response["datasets"]["metadata"]["exchange"],
                "sector": response["datasets"]["metadata"]["sector"],
                "subindustry": response["datasets"]["metadata"]["subindustry"],
                "industry": response["datasets"]["metadata"]["industry"],
                "gics": gic
            }
        except:
            data[tickers[i]] = {
                "description" : "",
                "exchange" : "",
                "sector" : "",
                "subindustry" : "",
                "industry" : "",
                "gics" : ""
            }
            pass
        i += 1
    i = 0
    for link in yahoo_links:
        try:
            driver.get(link)
            soup = driver.page_source
            while soup.count("Please try reloading the page.") > 1:
                print("sleeping")
                time.sleep(180)
                driver.get(link)
                soup = driver.page_source
            soup = BeautifulSoup(soup, "html.parser")
            yahoo_json = get_yahoo_data(soup)
            data[tickers[i]].update(yahoo_json)
        except:
            # print(tickers[i])
            pass
        i += 1
    print("WRITING 50 TICKERS...")
    write_dashboard(data, insider_json)

def clean_dashboard():
    global sh
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    worksheet.append_row([
        "Ticker",
        "Exchange",
        "Name",
        "Chart",
        "Owner",
        "SEC",
        "Seeking Alpha",
        "Press release",
        "Company Description",
        "Sector",
        "Industry Group",
        "Industry",
        "Sub industry",
        "marketcap",
        "Price",
        "Price change (%)",
        "12m Ins",
        "12m Ins Val",
        "6m Ins",
        "6m Ins Val",
        "3m Ins Val",
        "1m Ins Val",
        "1w Ins Val",
        "Insider Own %",
        "Institution Own %",
        "Short %",
        "Short interest ratio",
        "Blended Price",
        "high52",
        "low52",
        "% to blended",
        "% to high52",
        "% from low52",
        "Earning Per Share",
        "PE (trailing)",
        "PE (forward)",
        "Revenue",
        "Price/Sales (ttm)",
        "Enterprise Value/EBITDA",
        "Price/Book (mrq)",
        "Operating Cash Flow",
        "Free Cash Flow",
        "Net Cash Flow / Price",
        "foward dividend yield",
        "trailing dividend yield",
        "5 year avg dividend yield",
        "Payout Ratio",
        "cash",
        "net cash / price",
        "Net-Net Working Capital to Price",
        "Asset / price",
        "Retain earnings / market cap",
        "Total Debt/Equity (mrq)",
        "Total debt",
        "Revenue / long term debt",
        "Enterprise value",
        "z score",
        "GIC"
    ])

def write_dashboard(data, insider_json):
    global sh
    worksheet = sh.get_worksheet(0)
    rows = []
    for key, value in data.items():
        try:
            insider_row = [0, 0, 0, 0, 0, 0, 0]
            if key in insider_json.keys():
                insider_row = insider_json[key]
            row = [
                key,
                value["exchange"],
                value["name"],
                f"http://stockcharts.com/h-sc/ui?s={key}",
                f"http://whalewisdom.com/stock/{key}",
                f"http://sec.gov/edgar/search/?r=el#/entityName={key}",
                f"http://seekingalpha.com/symbol/{key}",
                f"http://google.com/search?q={key}+investor+relations+press+release",
                value["description"],
                "",
                "",
                "",
                "",
                value["mkt_cap"],
                value["price"],
                value["price_change"],
                insider_row[0],
                insider_row[1],
                insider_row[2],
                insider_row[3],
                insider_row[4],
                insider_row[5],
                insider_row[6],
                value["insider_own"],
                value["institution_own"],
                value["short"],
                value["short_int_ratio"],
                "",
                value["high_52"],
                value["low_52"],
                "",
                "",
                "",
                value["earning_per_share"],
                value["trailing_pe"],
                value["forward_pe"],
                value["revenue"],
                value["price_sales"],
                value["ent_val_ebitda"],
                value["price_book"],
                value["op_cash_flow"],
                value["free_cash_flow"],
                "",
                value["forward_dividend"],
                value["trailing_dividend"],
                value["5Y_dividend"],
                value["payout_ratio"],
                value["cash"],
                "",
                "",
                "",
                "",
                value["debt_equity"],
                value["debt"],
                "",
                value["enterprise_value"],
                "",
                value["gics"]
            ]
            rows.append(row)
        except:
            pass
    worksheet.append_rows(rows)

def get_yahoo_data(soup):
    data = {}
    for script in soup.findAll("script"):
        if "root.App.main" in str(script):
            str_data = str(script).split("root.App.main = ")[1][:-21]
            json_data = json.loads(str_data)
            # with open("json_data.json", "w") as f:
            #     json.dump(json_data, f)
            
            try:
                data["name"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["quoteType"]["shortName"]
            except:
                data["name"] = ""
            try:
                data["ticker"] = json_data["context"]["dispatcher"]["stores"]["PageStore"]["pageData"]["symbol"]
            except:
                data["ticker"] = ""
            try:
                data["mkt_cap"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingMarketCap"][-1]["reportedValue"]["raw"]
            except:
                data["mkt_cap"] = 0
            try:
                data["insider_own"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["heldPercentInsiders"]["raw"]
            except:
                data["insider_own"] = 0
            try:
                data["institution_own"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["heldPercentInstitutions"]["raw"]
            except:
                data["institution_own"] = 0
            try:
                data["short"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["shortPercentOfFloat"]["raw"]
            except:
                data["short"] = 0
            try:
                data["short_int_ratio"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["shortRatio"]["raw"]
            except:
                data["short_int_ratio"] = 0
            try:
                data["low_52"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["fiftyTwoWeekLow"]["raw"]
            except:
                data["low_52"] = 0
            try:
                data["high_52"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["fiftyTwoWeekHigh"]["raw"]
            except:
                data["high_52"] = 0
            try:
                data["earning_per_share"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["trailingEps"]["raw"]
            except:
                data["earning_per_share"] = 0
            try:
                data["trailing_pe"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingPeRatio"][-1]["reportedValue"]["raw"]
            except:
                data["trailing_pe"] = 0
            try:
                data["forward_pe"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingForwardPeRatio"][-1]["reportedValue"]["raw"]
            except:
                data["forward_pe"] = 0
            try:
                data["revenue"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalRevenue"]["raw"]
            except:
                data["revenue"] = 0
            try:
                data["op_cash_flow"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["operatingCashflow"]["raw"]
            except:
                data["op_cash_flow"] = 0
            try:
                data["free_cash_flow"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["freeCashflow"]["raw"]
            except:
                data["free_cash_flow"] = 0
            try:
                data["price"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["currentPrice"]["raw"]
            except:
                data["price"] = 0
            try:
                data["price_change"] = 100*json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["price"]["regularMarketChangePercent"]["raw"]
            except:
                data["price_change"] = 0
            try:
                data["price_sales"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingPsRatio"][-1]["reportedValue"]["raw"]
            except:
                data["price_sales"] = 0
            try:
                data["cash"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalCash"]["raw"]
            except:
                data["cash"] = 0
            try:
                data["debt"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["totalDebt"]["raw"]
            except:
                data["debt"] = 0
            try:
                data["payout_ratio"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["payoutRatio"]["raw"]
            except:
                data["payout_ratio"] = 0
            try:
                data["enterprise_value"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingEnterpriseValue"][-1]["reportedValue"]["raw"]
            except:
                data["enterprise_value"] = 0
            try:
                data["debt_equity"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["debtToEquity"]["raw"]
            except:
                data["debt_equity"] = 0
            try:
                data["ent_val_ebitda"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingEnterprisesValueEBITDARatio"][-1]["reportedValue"]["raw"]
            except:
                data["ent_val_ebitda"] = 0
            try:
                data["price_book"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingPbRatio"][-1]["reportedValue"]["raw"]
            except:
                data["price_book"] = 0
            try:
                data["forward_dividend"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["dividendYield"]["raw"]
            except:
                data["forward_dividend"] = 0
            try:
                data["trailing_dividend"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["trailingAnnualDividendYield"]["raw"]
            except:
                data["trailing_dividend"] = 0
            try:
                data["5Y_dividend"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["fiveYearAvgDividendYield"]["raw"]
            except:
                data["5Y_dividend"] = 0
    return data



def get_insider():
    clean_insider()
    tickers = open_tickers()
    links = []
    for t in tickers:
        links.append(f"http://openinsider.com/screener?s={t}")
        if len(links) >= 1000:
            get_insider_100(links)
            links = []
    get_insider_100(links)

def get_insider_100(links):
    soups = get_soups(links)
    insider_data = {}

    i = 0
    for soup in soups:
        try:
            ticker = links[i].split("=")[1].split("&")[0]
            table = soup.find("table", {"class": "tinytable"}).find("tbody")
            insider_data[ticker]  = []
            for tr in table.findAll("tr"):
                row = [x.text.strip() for x in tr.findAll("td")]
                insider_data[ticker].append(row)
        except:
            pass
        i+=1

    write_insider(insider_data)

def clean_insider():
    global sh
    worksheet = sh.get_worksheet(1)
    worksheet.clear()
    worksheet.append_row(["X", "Filing Date", "Trade Date", "Ticker", "Insider Name", "Title", "Trade Type", "Price", "Qty", "Owned", "^ Own", "Value", "1d", "1w", "1m", "6m"])

def write_insider(insider_data):
    global sh
    worksheet = sh.get_worksheet(1)
    rows = []
    for key, value in insider_data.items():
        rows.extend(value)
    worksheet.append_rows(rows)



if __name__ == "__main__":
    choice = int(input("Enter choice: \n1)Get all tickers \n2)Get insider information \n3)Resume dashboard \n4)Refresh dashboard\n"))

    if choice == 1:
        get_all_tickers()
    elif choice == 2:
        get_insider()
    elif choice == 3:
        get_tickers_data(choice)
    elif choice == 4:
        get_tickers_data(choice)
