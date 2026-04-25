import re


COMPANY_MAP = {
    "nvidia": {"name": "Nvidia", "ticker": "NVDA", "theme": "AI infrastructure demand"},
    "nvda": {"name": "Nvidia", "ticker": "NVDA", "theme": "AI infrastructure demand"},
    "amd": {"name": "AMD", "ticker": "AMD", "theme": "AI chip competition"},
    "microsoft": {"name": "Microsoft", "ticker": "MSFT", "theme": "enterprise AI platform adoption"},
    "msft": {"name": "Microsoft", "ticker": "MSFT", "theme": "enterprise AI platform adoption"},
    "apple": {"name": "Apple", "ticker": "AAPL", "theme": "consumer device monetization"},
    "aapl": {"name": "Apple", "ticker": "AAPL", "theme": "consumer device monetization"},
    "tesla": {"name": "Tesla", "ticker": "TSLA", "theme": "autonomy and EV execution"},
    "tsla": {"name": "Tesla", "ticker": "TSLA", "theme": "autonomy and EV execution"},
    "amazon": {"name": "Amazon", "ticker": "AMZN", "theme": "cloud and AI operating leverage"},
    "amzn": {"name": "Amazon", "ticker": "AMZN", "theme": "cloud and AI operating leverage"},
    "meta": {"name": "Meta", "ticker": "META", "theme": "ad monetization and AI spend"},
    "alphabet": {"name": "Alphabet", "ticker": "GOOGL", "theme": "search and model competition"},
    "google": {"name": "Alphabet", "ticker": "GOOGL", "theme": "search and model competition"},
}

KNOWN_TICKERS = {company["ticker"] for company in COMPANY_MAP.values() if company.get("ticker")}


def has_finance_entity(query: str) -> bool:
    query_lower = query.lower()

    if any(key in query_lower for key in COMPANY_MAP):
        return True

    ticker_match = re.search(r"\$?([A-Z]{2,5})\b", query)
    if not ticker_match:
        return False

    return ticker_match.group(1) in KNOWN_TICKERS


def _extract_company(query: str):
    query_lower = query.lower()

    for key, company in COMPANY_MAP.items():
        if key in query_lower:
            return company

    ticker_match = re.search(r"\b[A-Z]{2,5}\b", query)
    if ticker_match:
        ticker = ticker_match.group(0)
        return {
            "name": ticker,
            "ticker": ticker,
            "theme": "market sentiment and execution",
        }

    return {
        "name": "the company",
        "ticker": None,
        "theme": "market positioning",
    }


def get_finance_reply(query: str):
    company = _extract_company(query)
    name = company["name"]
    ticker = company["ticker"]
    theme = company["theme"]

    if name == "Nvidia":
        summary = "Nvidia stock shows strong recent momentum."
        insight = (
            "Growth is being driven by sustained AI demand, but the valuation remains rich versus historical norms, "
            "so execution risk matters more than usual."
        )
        actions = [
            "Monitor earnings reports for data center growth",
            "Compare positioning with AMD and hyperscaler capex trends",
            "Avoid chasing new highs without a clearer entry level",
        ]
        confidence = "medium"
    elif ticker:
        summary = f"{name} ({ticker}) looks investable only if the current trend is supported by fundamentals."
        insight = (
            f"The key issue for {name} is {theme}; that can support upside, but sentiment can reverse quickly if growth expectations run ahead of delivery."
        )
        actions = [
            f"Review the next earnings release for {name}",
            f"Compare {name} against its closest competitors",
            "Wait for confirmation instead of buying on narrative alone",
        ]
        confidence = "medium"
    else:
        summary = "The finance tool can frame the investment case, but the company is still ambiguous."
        insight = (
            "There is enough intent to discuss investing, but not enough entity detail yet to produce a sharper financial view."
        )
        actions = [
            "Specify the company or ticker",
            "Ask for a bull-vs-bear breakdown",
            "Compare valuation, growth, and risk before acting",
        ]
        confidence = "low"

    return {
        "type": "analysis",
        "tool": "finance",
        "content": {
            "summary": summary,
            "insight": insight,
            "actions": actions,
            "confidence": confidence,
        },
    }