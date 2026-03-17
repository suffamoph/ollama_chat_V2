"""
Ollama API 调用脚本
支持列出模型、生成文本和聊天功能
"""

import requests
import json
import sys

# Ollama API 基础地址
BASE_URL = "http://localhost:11434"


def list_models():
    """列出所有可用的 Ollama 模型"""
    try:
        response = requests.get(f"{BASE_URL}/api/tags")
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        if models:
            print("可用的模型:")
            for model in models:
                name = model.get("name", "未知")
                size = model.get("size", 0)
                size_gb = size / (1024 ** 3) if size else 0
                print(f"  - {name} ({size_gb:.2f} GB)")
        else:
            print("未找到可用的模型")
        return models
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到 Ollama，请确保 Ollama 服务正在运行")
        return []
    except Exception as e:
        print(f"错误：{e}")
        return []


def generate_response(prompt, model="gemma3", stream=False):
    """生成文本响应"""
    url = f"{BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    
    try:
        response = requests.post(url, json=payload, stream=stream)
        response.raise_for_status()
        
        if stream:
            print(f"使用模型 '{model}' 生成响应:")
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    text = data.get("response", "")
                    print(text, end="", flush=True)
            print()
        else:
            data = response.json()
            return data.get("response", "")
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到 Ollama，请确保 Ollama 服务正在运行")
    except Exception as e:
        print(f"错误：{e}")
    
    return None


def chat(messages, model="gemma3", stream=False):
    """使用聊天 API"""
    url = f"{BASE_URL}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    
    try:
        response = requests.post(url, json=payload, stream=stream)
        response.raise_for_status()
        
        if stream:
            print(f"使用模型 '{model}' 聊天:")
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = message.get("content", "")
                    print(content, end="", flush=True)
            print()
        else:
            data = response.json()
            message = data.get("message", {})
            return message.get("content", "")
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到 Ollama，请确保 Ollama 服务正在运行")
    except Exception as e:
        print(f"错误：{e}")
    
    return None


def main():
    """主函数 - 交互式命令行"""
    print("=" * 50)
    print("Ollama 命令行工具")
    print("=" * 50)
    
    # 列出可用模型
    models = list_models()
    if not models:
        print("\n请先安装 Ollama 并拉取一个模型，例如:")
        print("  ollama pull llama2")
        return
    
    # 选择模型
    print()
    model_name = input(f"输入模型名称 (默认：gemma3): ").strip()
    if not model_name:
        model_name = "gemma3"
    
    print(f"\n使用模型：{model_name}")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'list' 重新列出模型")
    print("-" * 50)
    
    # 聊天历史
    messages = []
    
    while True:
        try:
            user_input = input("\n您： ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见!")
                break
            
            if user_input.lower() == 'list':
                list_models()
                continue
            
            if not user_input:
                continue
            
            # 添加到聊天历史
            messages.append({"role": "user", "content": user_input})
            
            # 使用聊天 API
            response = chat(messages, model=model_name)
            
            if response:
                # 添加助手回复到历史
                messages.append({"role": "assistant", "content": response})
                
                # 限制历史记录长度
                if len(messages) > 20:
                    messages = messages[-20:]
        
        except KeyboardInterrupt:
            print("\n\n程序中断")
            break
        except Exception as e:
            print(f"错误：{e}")


if __name__ == "__main__":
    main()