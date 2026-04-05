from datetime import datetime

def run_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
