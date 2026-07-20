import scratchattach as sa
import anthropic
import os
import time

SCRATCH_USERNAME  = os.environ["SCRATCH_USERNAME"]
SCRATCH_PASSWORD  = os.environ["SCRATCH_PASSWORD"]
PROJECT_ID        = os.environ["PROJECT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
history = []
last_input = ""

print(f"起動中... project={PROJECT_ID}")
session = sa.login(SCRATCH_USERNAME, SCRATCH_PASSWORD)
cloud = session.connect_cloud(PROJECT_ID)
print("接続完了！監視開始...")

# scratchattachは☁マークなし、スペースなしで変数名を扱う
while True:
    try:
        trigger = str(cloud.get_var("input_trigger") or "")

        if trigger and trigger != last_input:
            last_input = trigger
            print(f"質問: {trigger}")

            history.append({"role": "user", "content": trigger})

            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system="You are ENI, a friendly AI assistant. Reply in the same language as the user. Keep replies short and under 100 characters.",
                messages=history
            )

            reply = resp.content[0].text
            history.append({"role": "assistant", "content": reply})
            print(f"返答: {reply}")

            cloud.set_var("ai_reply", reply)
            time.sleep(0.5)
            cloud.set_var("input_trigger", "")

    except Exception as e:
        print(f"エラー: {e}")

    time.sleep(0.5)
