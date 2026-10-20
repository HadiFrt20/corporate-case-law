"""Foundation Model API calls on the personal fe-vm (Databricks-hosted Claude / GPT)."""
import json, re, time
from dbsql import W
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

WRITER, JUDGE = "databricks-claude-sonnet-5-5", "databricks-gpt-5-5"


def chat(prompt, model=WRITER, system=None, max_tokens=1500, retries=3):
    msgs = ([ChatMessage(role=ChatMessageRole.SYSTEM, content=system)] if system else []) + [ChatMessage(role=ChatMessageRole.USER, content=prompt)]
    for i in range(retries):
        try:
            r = W.serving_endpoints.query(name=model, messages=msgs, max_tokens=max_tokens)
            c = r.choices[0].message.content
            if isinstance(c, list):  # some endpoints return content blocks
                c = "".join(b.get("text", "") if isinstance(b, dict) else getattr(b, "text", str(b)) for b in c)
            return c
        except Exception as e:
            if i == retries - 1: raise
            time.sleep(3 * (i + 1))


RAW = []  # every raw reply, for the run log


def chat_json(prompt, expect=None, **kw):
    """parse the first JSON value in the reply (object or array); expect=dict|list coerces the common mismatches"""
    txt = chat(prompt, **kw); RAW.append(txt)
    starts = [i for i in (txt.find("{"), txt.find("[")) if i >= 0]
    val = None
    for st in sorted(starts):
        try: val, _ = json.JSONDecoder().raw_decode(txt[st:]); break
        except json.JSONDecodeError: continue
    if expect is dict and isinstance(val, list): val = next((v for v in val if isinstance(v, dict)), None)
    if expect is list and isinstance(val, dict): val = next((v for v in val.values() if isinstance(v, list)), [val])
    return val
