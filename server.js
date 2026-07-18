const http = require("http");
const https = require("https");

// Scratchクラウド変数プロトコル用WebSocketサーバー
// Renderで無料ホスティング可能

const PORT = process.env.PORT || 3000;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";

// CORS対応のシンプルHTTPサーバー（ScratchはWebSocketクラウド変数を使うため、
// ここではTurboWarp向けのHTTP APIエンドポイントを提供する）
const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(200);
    res.end();
    return;
  }

  // Health check
  if (req.url === "/" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Scratch AI Chat Server 動作中！");
    return;
  }

  // AI Chat endpoint: POST /chat
  if (req.url === "/chat" && req.method === "POST") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", async () => {
      try {
        const { message, history } = JSON.parse(body);
        if (!message) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: "message is required" }));
          return;
        }

        // Build messages array for Claude
        const messages = [];
        if (history && Array.isArray(history)) {
          for (const h of history) {
            messages.push({ role: h.role, content: h.content });
          }
        }
        messages.push({ role: "user", content: message });

        // Call Anthropic API
        const reply = await callClaude(messages);

        res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        res.end(JSON.stringify({ reply }));
      } catch (e) {
        console.error(e);
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end("Not found");
});

function callClaude(messages) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 512,
      system: "あなたは親切なAIアシスタントです。Scratchユーザー（子供も多い）向けに、わかりやすく短く日本語で答えてください。",
      messages,
    });

    const options = {
      hostname: "api.anthropic.com",
      path: "/v1/messages",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Length": Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.content && parsed.content[0]) {
            resolve(parsed.content[0].text);
          } else {
            reject(new Error("No content in response: " + data));
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

server.listen(PORT, () => {
  console.log(`サーバー起動中: http://localhost:${PORT}`);
});
