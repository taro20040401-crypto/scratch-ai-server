import scratchattach as sa
import anthropic
import os

SCRATCH_USERNAME  = os.environ["SCRATCH_USERNAME"]
SCRATCH_PASSWORD  = os.environ["SCRATCH_PASSWORD"]
PROJECT_ID        = os.environ["PROJECT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
history = []

print(f"起動中... project={PROJECT_ID}")
session = sa.login(SCRATCH_USERNAME, SCRATCH_PASSWORD)
cloud = session.connect_cloud(PROJECT_ID)

events = cloud.events()

@events.event
def on_set(event):
    print(f"変数変化: {event.name} = {event.value}")
    if event.name == "☁ input_trigger" and event.value and event.value != "":
        question = str(event.value)
        print(f"質問: {question}")

        history.append({"role": "user", "content": question})

        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system="You are ENI, a friendly AI assistant. Reply in the same language as the user. Keep replies short.",
                messages=history
            )
            reply = resp.content[0].text
            history.append({"role": "assistant", "content": reply})
            print(f"返答: {reply}")
            cloud.set_var("ai_reply", reply)
            cloud.set_var("input_trigger", "")
        except Exception as e:
            print(f"APIエラー: {e}")
            cloud.set_var("ai_reply", "Error occurred")
            cloud.set_var("input_trigger", "")

print("イベント監視開始！")
events.start()
