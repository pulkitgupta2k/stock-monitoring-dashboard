from bs4.element import Script
from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
import time
from random import randrange
import grequests
import gspread
import json
from bs4 import BeautifulSoup
from pprint import pprint 

API_KEY = "c5eba080e8777f7afd5d623dd237d8e501a456f8"
gc = gspread.service_account("key.json")
sh = gc.open("Copy of v.03 stock monitoring dashboard")

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
            print(response[0].status_code, response[1].status_code)
            time.sleep(180)
            rs = (grequests.get(u, stream=False, headers = {"User-Agent": "PostmanRuntime/7.26.8"})
              for u in urls[x:x+MAX_CONNECTIONS])
            response = grequests.map(rs)
        requests.extend(response)
        print("json")
        print(response)
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
            print(response[0].status_code, response[1].status_code)
            time.sleep(180)
            rs = (grequests.get(u, stream=False, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"})
              for u in urls[x:x+MAX_CONNECTIONS])
            response = grequests.map(rs)
        requests.extend(response)
        print("soup")
        print(response)
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



def get_tickers_data():
    l = []
    with open("tickers.json") as f:
        tickers = json.load(f)
    clean_dashboard()
    for key in tickers.keys():
        l.append(key)
        if len(l) >= 100:
            time.sleep(randrange(1, 5))
            get_tickers_data_100(l)
            l = []

def get_tickers_data_100(tickers):
    data = {}
    quickfs_links = []
    yahoo_links = []

    for ticker in tickers:
        quickfs_links.append(f"https://api.quickfs.net/stocks/{ticker}:US/ovr/Annual/")
        yahoo_links.append(f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}")

    quickfs_response = get_jsons(quickfs_links)
    yahoo_soups = get_soups(yahoo_links)
    i = 0
    for response in quickfs_response:
        try:
            data[tickers[i]] = {
                "description" : response["datasets"]["metadata"]["description"],
                "exchange": response["datasets"]["metadata"]["exchange"],
                "sector": response["datasets"]["metadata"]["sector"],
                "subindustry": response["datasets"]["metadata"]["subindustry"],
                "industry": response["datasets"]["metadata"]["industry"],
                "gics": response["datasets"]["metadata"]["gics"]
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
    for soup in yahoo_soups:
        try:
            yahoo_json = get_yahoo_data(soup)
            data[tickers[i]].update(yahoo_json)
        except:
            print(tickers[i])
            pass
        i += 1

    # with open("temp1.json", "w") as f:
    #     json.dump(data, f) 
    write_dashboard(data)

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
        "marketcap(million)",
        "Price",
        "Price change",
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
        "Revenue(Million)",
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

def write_dashboard(data):
    global sh
    worksheet = sh.get_worksheet(0)
    rows = []
    for key, value in data.items():
        try:
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
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
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
                value["forward_dividend"],
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

def get_yahoo_data(json_data):
    pprint(json_data)
    data = {}
    for script in soup.findAll("script"):
        if "root.App.main" in str(script):
            str_data = str(script).split("root.App.main = ")[1][:-21]
            json_data = json.loads(str_data)
            with open("json_data.json", "w") as f:
                json.dump(json_data, f)
            
            try:
                data["name"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["quoteType"]["shortName"]
            except:
                data["name"] = ""
            try:
                data["ticker"] = json_data["context"]["dispatcher"]["stores"]["PageStore"]["pageData"]["symbol"]
            except:
                data["ticker"] = ""
            try:
                data["mkt_cap"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["marketCap"]["raw"]
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
                data["trailing_pe"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["trailingPE"]["raw"]
            except:
                data["trailing_pe"] = 0
            try:
                data["forward_pe"] =json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["summaryDetail"]["forwardPE"]["raw"]
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
                data["price_sales"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["enterpriseToRevenue"]["raw"]
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
                data["enterprise_value"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["defaultKeyStatistics"]["enterpriseValue"]["raw"]
            except:
                data["enterprise_value"] = 0
            try:
                data["debt_equity"] = json_data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]["financialData"]["debtToEquity"]["raw"]
            except:
                data["debt_equity"] = 0
            try:
                data["ent_val_ebitda"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingEnterprisesValueEBITDARatio"][0]["reportedValue"]["raw"]
            except:
                data["ent_val_ebitda"] = 0
            try:
                data["price_book"] = json_data["context"]["dispatcher"]["stores"]["QuoteTimeSeriesStore"]["timeSeries"]["trailingPbRatio"][0]["reportedValue"]["raw"]
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
    pprint(data)
    a = input()
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
    worksheet = sh.get_worksheet(2)
    worksheet.clear()
    worksheet.append_row(["X", "Filing Date", "Trade Date", "Ticker", "Insider Name", "Title", "Trade Type", "Price", "Qty", "Owned", "^ Own", "Value", "1d", "1w", "1m", "6m"])

def write_insider(insider_data):
    global sh
    worksheet = sh.get_worksheet(2)
    rows = []
    for key, value in insider_data.items():
        rows.extend(value)
    worksheet.append_rows(rows)



if __name__ == "__main__":
    # get_all_tickers()
    # get_insider()
    # get_tickers_data()
    a = get_yahoo_data(get_jsons(["https://query2.finance.yahoo.com/v10/finance/quoteSummary/PFE?modules=assetProfile%2CsummaryProfile%2CsummaryDetail%2CesgScores%2Cprice%2CincomeStatementHistory%2CincomeStatementHistoryQuarterly%2CbalanceSheetHistory%2CbalanceSheetHistoryQuarterly%2CcashflowStatementHistory%2CcashflowStatementHistoryQuarterly%2CdefaultKeyStatistics%2CfinancialData%2CcalendarEvents%2CsecFilings%2CrecommendationTrend%2CupgradeDowngradeHistory%2CinstitutionOwnership%2CfundOwnership%2CmajorDirectHolders%2CmajorHoldersBreakdown%2CinsiderTransactions%2CinsiderHolders%2CnetSharePurchaseActivity%2Cearnings%2CearningsHistory%2CearningsTrend%2CindustryTrend%2CindexTrend%2CsectorTrend"])[0])
    # get_yahoo_data(get_soups(["https://finance.yahoo.com/quote/AAPL/key-statistics?p=AAPL"])[0])