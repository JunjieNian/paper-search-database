import requests
import json
import os

algo_url = os.getenv("ALGO_URL", "http://localhost:8003").rstrip("/")

res = ''
end = False
with requests.post(f'{algo_url}/chat/stream/', json={
    'messages': [
        {
            'role': 'user',  # role: user表示是用户说的
            'content': '你好，我叫小明，你是谁？'
        },
        {
            'role': 'assistant',  # role: assistant表示是模型输出的
            'content': '你好，小明！我是Qwen，由阿里云开发的人工智能助手。很高兴认识你！有什么我可以帮助你的吗？'
        },
        {
            'role': 'user',
            'content': '我是谁？'
        }
    ],
}, stream=True) as resp:
    for line in resp.iter_lines():
        line = line.decode('utf-8').strip()
        if line == '':
            continue
        if line.startswith('data: '):
            line = line[len('data: '):]
            if line == '[DONE]':
                end = True
                break
        else:
            break
        line = json.loads(line)
        print(line)
        res += line['choices'][0]['delta']['content']
if end:
    print(res)
    print('OK')
else:
    print('FAILED')
