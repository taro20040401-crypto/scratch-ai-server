import scratchattach as sa
import anthropic
import os
import time

SCRATCH_USERNAME  = os.environ["SCRATCH_USERNAME"]
SCRATCH_PASSWORD  = os.environ["SCRATCH_PASSWORD"]
PROJECT_ID        = os.environ["PROJECT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# 参考プロジェクトのalphabetリストと完全一致
ALPHABET = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.?!,\' " ')

def num_to_text(num_str):
    """Scratchの暗号化数値→テキスト変換"""
    s = str(int(float(num_str)))
    result = ""
    i = 0
    while i < len(s):
        code = int(s[i:i+2])
        if 1 <= code <= len(ALPHABET):
            result += ALPHABET[code - 1]
        i += 2
    return result

def text_to_num(text):
    """テキスト→Scratchの暗号化数値変換"""
    result = ""
    for ch in text:
        if ch in ALPHABET:
            idx = ALPHABET.index(ch) + 1
            result += str(idx).zfill(2)
        else:
            result += "67"  # スペースとして扱う
    return result if result else "0"

print(f"起動中... project={PROJECT_ID}")
session = sa.login(SCRATCH_USERNAME, SCRATCH_PASSWORD)
cloud   = session.connect_cloud(PROJECT_ID)
client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

history = []
last_trigger = None

print("監視開始！Scratchに話しかけてください。")

while True:
    try:
        trigger = str(cloud.get_var("☁ trigger1"))

        if trigger != "0" and trigger != "9" and trigger != last_trigger:
            last_trigger = trigger
            print(f"トリガー検知: {trigger}")

            # 質問を数値→テキスト変換
            question = num_to_text(trigger)
            print(f"質問: {question}")

            # Claude API呼び出し
            history.append({"role": "user", "content": question})
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                system="あなたは親切なAIアシスタントです。短く日本語で答えてください。70文字以内で。英数字と記号のみ使用可能。",
                messages=history
            )
            ai_reply = resp.content[0].text
            history.append({"role": "assistant", "content": ai_reply})
            print(f"返答: {ai_reply}")

            # 返答をテキスト→数値変換してセット
            reply_num = text_to_num(ai_reply)
            cloud.set_var("☁ text_from_python1", reply_num)
            time.sleep(0.5)
            # trigger1を9にして完了通知
            cloud.set_var("☁ trigger1", "9")
            print("返答送信完了！")

    except Exception as e:
        print(f"エラー: {e}")

    time.sleep(0.3)
