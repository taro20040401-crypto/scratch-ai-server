import scratchattach as sa
import anthropic
import requests
import os
import time

SCRATCH_USERNAME  = os.environ["SCRATCH_USERNAME"]
SCRATCH_PASSWORD  = os.environ["SCRATCH_PASSWORD"]
PROJECT_ID        = os.environ["PROJECT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

ALPHABET = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.?!, ')

def encode(text):
    result = ""
    for ch in text:
        if ch in ALPHABET:
            result += str(ALPHABET.index(ch) + 1).zfill(2)
        else:
            result += "65"
    return int(result) if result else 0

def get_latest_question():
    """clouddata APIから最新のquestion_textを取得"""
    try:
        url = f"https://clouddata.scratch.mit.edu/logs?projectid={PROJECT_ID}&limit=20&offset=0"
        r = requests.get(url, timeout=5)
        logs = r.json()
        for log in logs:
            name = log.get("name", "")
            value = log.get("value", "")
            # question_textはクラウド変数じゃないので直接は取れないが
            # input_triggerが1になる直前のai_replyの値が質問テキスト
            if "ai_reply" in name and value and value not in ["", "0"]:
                return value
    except Exception as e:
        print(f"API取得エラー: {e}")
    return None

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
history = []

print(f"起動中... project={PROJECT_ID}")
session = sa.login(SCRATCH_USERNAME, SCRATCH_PASSWORD)
cloud = session.connect_cloud(PROJECT_ID)
events = cloud.events()

@events.event
def on_set(event):
    print(f"変数変化: {event.name} = {repr(event.value)}")
    if "input_trigger" in event.name and str(event.value).strip() == "1":
        print("トリガー検知！APIから質問を取得...")
        time.sleep(0.5)
        question = get_latest_question()
        print(f"質問: {question}")
        if not question:
            print("質問取得失敗")
            cloud.set_var("input_trigger", 0)
            return

        history.append({"role": "user", "content": question})
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                system="You are ENI, a friendly AI. Reply in same language as user. Max 60 chars.",
                messages=history
            )
            reply = resp.content[0].text[:60]
            history.append({"role": "assistant", "content": reply})
            print(f"返答: {reply}")
            encoded = encode(reply)
            print(f"エンコード: {encoded}")
            cloud.set_var("ai_reply", encoded)
            time.sleep(0.3)
            cloud.set_var("input_trigger", 0)
        except Exception as e:
            print(f"APIエラー: {e}")
            cloud.set_var("input_trigger", 0)

print("監視開始！")
events.start()
