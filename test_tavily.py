from tavily import TavilyClient
import os

print("TAVILY KEY:", os.getenv("TAVILY_API_KEY"))

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

try:
    res = client.search(query="latest ai tools", max_results=2)
    print("SUCCESS:", res)
except Exception as e:
    print("ERROR:", e)