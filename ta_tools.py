import requests
import xml.etree.ElementTree as ET

app_id = "WYAJR5-633LT5JGG4"

def query(question):
    query_url = f"http://api.wolframalpha.com/v2/query?appid={app_id}&input={question}&podstate=Step-by-step%20solution&output=json"
    r = requests.get(query_url).json()
    return(r['queryresult']['pods'][0]['subpods'][0]['img']['alt'])