import requests
import time

FLASK_URL = 'http://localhost:5000'

def stream_chat(think=False):
    url = FLASK_URL + '/api/chat'
    payload = {
        'model': 'gemma3:latest',
        'messages': [{'role':'user','content':'hello'}],
        'stream': True,
        'think': think,
        'options': {'think': think}
    }
    print('\n--- Request with think=%s ---' % think)
    with requests.post(url, json=payload, stream=True) as r:
        try:
            r.raise_for_status()
        except Exception as e:
            print('Request failed:', e)
            print('Response text:', r.text[:1000])
            return
        for chunk in r.iter_lines(decode_unicode=True):
            if chunk:
                print('LINE:', chunk)

if __name__ == '__main__':
    print('Waiting 0.5s for servers...')
    time.sleep(0.5)
    stream_chat(think=False)
    time.sleep(0.3)
    stream_chat(think=True)
