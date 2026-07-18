import scratchattach as sa
import anthropic
import os
import time

# 環境変数から取得
SCRATCH_USERNAME = os.environ.get("SCRATCH_USERNAME")
SCRATCH_PASSWORD = os.environ.get("SCRATCH_PASSWORD")
PROJECT_ID       = os.environ.get("PROJECT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

print(f"接続中... project={PROJECT_ID}, user={SCRATCH_USERNAME}")

# Scratchにログイン
session = sa.login(SCRATCH_USERNAME, SCRATCH_PASSWORD)
project = session.connect_cloud(PROJECT_ID)
client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 会話履歴
history = []

class CloudHandler(sa.events.CloudEvents):
    def on_set(self, event):
        if event.name == "☁ STATUS" and event.value == "1":
            print("入力検出！")
            try:
                user_input = project.get_var("☁ INPUT")
                print(f"入力: {user_input}")

                # 会話履歴に追加
                history.append({"role": "user", "content": user_input})

                # Claude APIを呼ぶ
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=300,
                    system="あなたは親切なAIアシスタントです。Scratchユーザー向けに短く日本語で答えてください。150文字以内で答えてください。",
                    messages=history
                )
                ai_reply = resp.content[0].text
                print(f"返答: {ai_reply}")

                # 会話履歴に追加
                history.append({"role": "assistant", "content": ai_reply})

                # 返答をクラウド変数にセット
                project.set_var("☁ RESPONSE", ai_reply)
                time.sleep(0.5)
                project.set_var("☁ STATUS", "2")

            except Exception as e:
                print(f"エラー: {e}")
                project.set_var("☁ RESPONSE", f"エラーが発生しました: {str(e)[:50]}")
                time.sleep(0.5)
                project.set_var("☁ STATUS", "2")

events = project.connect_cloud_events()
events.event(CloudHandler)
print("監視開始！Scratchプロジェクトに話しかけてください")
events.start(thread=False)
