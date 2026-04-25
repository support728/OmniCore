import subprocess, sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath("."))
code = "from app.services.intent_router import chat, ChatRequest; import sys; print(chat(ChatRequest(message=sys.argv[1])).get('reply',''))"
for m in ['search latest Microsoft AI news', 'What is the capital of Japan?']:
    print(f'MSG: {m}')
    try:
        r = subprocess.run(
            [sys.executable, '-c', code, m],
            capture_output=True,
            text=True,
            timeout=45,
            cwd="."
        )
        out = (r.stdout or r.stderr).strip()

        import ast

        # Extract only the dictionary part (starts at first "{")
        dict_start = out.find("{")

        clean_out = out[dict_start:] if dict_start != -1 else out

        final_output = clean_out

        try:
            parsed = ast.literal_eval(clean_out)
            if isinstance(parsed, dict) and "reply" in parsed:
                final_output = parsed["reply"]
        except Exception:
            pass

        print("REPLY:")
        print(final_output)
    except subprocess.TimeoutExpired:
        print('REPLY: TIMEOUT')
    print()
