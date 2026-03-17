"""
Flask 服务 - Ollama 聊天助手后端
提供 API 接口与 Ollama 交互
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Ollama API 基础地址
OLLAMA_BASE_URL = "http://localhost:11434"


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('.', 'index.html')


@app.route('/api/models', methods=['GET'])
def list_models():
    """列出所有可用的 Ollama 模型"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        return jsonify({"models": models})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "无法连接到 Ollama，请确保 Ollama 服务正在运行"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_response():
    """生成文本响应"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', 'gemma3')
        stream = data.get('stream', False)
        
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        response = requests.post(url, json=payload, stream=stream)
        response.raise_for_status()
        
        if stream:
            # 流式响应
            def generate():
                for line in response.iter_lines():
                    if line:
                        yield line.decode('utf-8') + '\n'
            from flask import Response
            return Response(generate(), content_type='text/event-stream')
        else:
            # 非流式响应
            result_data = response.json()
            return jsonify({"response": result_data.get("response", "")})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "无法连接到 Ollama，请确保 Ollama 服务正在运行"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ps', methods=['GET'])
def ps():
    """Get running model processes (VRAM usage)"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=3)
        response.raise_for_status()
        return jsonify(response.json())
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # Return empty list if Ollama not available or timeout
        return jsonify([])
    except Exception as e:
        return jsonify([])


@app.route('/api/chat', methods=['POST'])
def chat():
    """使用聊天 API"""
    try:
        data = request.json
        messages = data.get('messages', [])
        model = data.get('model', 'gemma3')
        stream = data.get('stream', False)
        think = data.get('think', False)
        options = data.get('options', {})
        
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Forward think parameter if present
        if think:
            payload["think"] = think
        if options:
            payload["options"] = options
        
        response = requests.post(url, json=payload, stream=stream)
        response.raise_for_status()
        
        if stream:
            # 流式响应 - 有状态过滤 <think>...</think> 块
            def generate():
                in_think = [False]  # 用列表实现闭包内可变状态
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if not think and isinstance(chunk.get('message'), dict):
                                msg = chunk['message']
                                msg.pop('thinking', None)
                                msg.pop('reasoning', None)
                                if isinstance(msg.get('content'), str):
                                    content = msg['content']
                                    filtered = ''
                                    i = 0
                                    while i < len(content):
                                        if in_think[0]:
                                            end = content.find('</think>', i)
                                            if end == -1:
                                                i = len(content)  # 跳过剩余
                                            else:
                                                in_think[0] = False
                                                i = end + 8
                                        else:
                                            start = content.find('<think>', i)
                                            if start == -1:
                                                filtered += content[i:]
                                                i = len(content)
                                            else:
                                                filtered += content[i:start]
                                                in_think[0] = True
                                                i = start + 7
                                    msg['content'] = filtered
                            yield json.dumps(chunk) + '\n'
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            yield line.decode('utf-8') + '\n'
            from flask import Response
            return Response(generate(), content_type='text/event-stream')
        else:
            # 非流式响应
            result_data = response.json()
            message = result_data.get("message", {})
            return jsonify({"content": message.get("content", "")})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "无法连接到 Ollama，请确保 Ollama 服务正在运行"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("启动 Flask 服务...")
    print("访问 http://localhost:5000 使用聊天界面")
    app.run(host='0.0.0.0', port=5000, debug=True)
