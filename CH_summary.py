from flask import Flask, request, jsonify
import requests
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CHANNELTALK_API_KEY = os.getenv("CHANNELTALK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

GROUP_ID = "184251"
CHANNELTALK_BASE_URL = f"https://api.channel.io/open/v5/groups/{GROUP_ID}/messages"

# 채팅 요약 함수
def summarize_chat_with_template(chat_history):
    chat_text = "\n".join(chat_history)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant who summarizes conversations in the following template:\n1. 장소:\n2. 목적: 술집 or 맛집 or 스터디카페 (select one based on the context)\n3. 대화내용 요약:"},
                {"role": "user", "content": f"Summarize the following conversation:\n{chat_text}"}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error summarizing chat: {e}"

# 채널톡 API로 채팅 가져오기
def get_channel_talk_messages():
    headers = {
        "Authorization": f"Bearer {CHANNELTALK_API_KEY}"
    }
    response = requests.get(CHANNELTALK_BASE_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch messages: {response.status_code} {response.text}")

# 채널톡으로 메시지 전송
def send_channel_talk_message(conversation_id, message):
    url = f"https://api.channel.io/open/v5/conversations/{conversation_id}/messages"
    headers = {
        "Authorization": f"Bearer {CHANNELTALK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "text",
        "message": message
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to send message: {response.status_code} {response.text}")

@app.route('/summary', methods=['POST'])
def process_summary():
    try:
        # 채널톡에서 채팅 데이터 가져오기
        messages_data = get_channel_talk_messages()

        # 채팅 데이터 정리
        messages = [msg['content'] for msg in messages_data['messages']]
        conversation_id = messages_data['conversationId']

        # 템플릿을 사용한 요약 생성
        summary = summarize_chat_with_template(messages)

        # 채널톡으로 요약 메시지 전송
        send_channel_talk_message(conversation_id, summary)

        return jsonify({"status": "success", "summary": summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001)
