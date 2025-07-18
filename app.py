from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_TEAM_ID = os.getenv("FIGMA_TEAM_ID")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_tenant_access_token():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    ).json()
    return resp.get("tenant_access_token")

def send_text(chat_id, text):
    token = get_tenant_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "receive_id_type": "chat_id",
        "receive_id": chat_id,
        "msg_type": "text",
        "content": {"text": text}
    }
    requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers=headers, json=data
    )

def search_figma(keyword):
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    r = requests.get(
        f"https://api.figma.com/v1/files/team/{FIGMA_TEAM_ID}/projects",
        headers=headers
    ).json()
    results = []
    for proj in r.get("projects", []):
        pid = proj["id"]
        r2 = requests.get(
            f"https://api.figma.com/v1/projects/{pid}/files",
            headers=headers
        ).json()
        for f in r2.get("files", []):
            name = f["name"]
            if keyword.lower() in name.lower():
                link = f"https://www.figma.com/file/{f['key']}"
                results.append(f"{name} → {link}")
    return results

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    evt = data.get("event", {})
    if data.get("type") == "event_callback" and evt.get("type") == "im.message.receive_v1":
        chat_id = evt["open_chat_id"]
        text = evt["text"]
        if "搜索" in text:
            kw = text.split("搜索",1)[1].strip()
            res = search_figma(kw)
            if res:
                msg = "🔍 搜索结果：\n" + "\n".join(res)
            else:
                msg = "❌ 未找到相关 Figma 文件"
            send_text(chat_id, msg)
    return jsonify({"code":0})

if __name__ == "__main__":
    app.run()
