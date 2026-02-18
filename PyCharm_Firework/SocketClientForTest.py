"""
一个简单的客户端实现，用于服务器测试
注意server_ip改成自己电脑的ip，在cmd输入ipconfig找到IPV4地址那个就是本机IP
先运行服务器程序SocketServer.py点击进入按钮，然后运行本程序
如果客户端和服务器连接正常，可以看到运行服务器时自动打开的UI界面燃放一颗烟花
"""

import socket
import time


def test_connection():
    """测试服务器连接"""
    server_ip = '你的主机IP'#客户端IP地址
    server_port = 8888

    print("开始测试服务器连接...")

    try:
        # 创建socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)  # 设置3秒超时

        # 连接服务器
        print(f"正在连接 {server_ip}:{server_port}")
        client.connect((server_ip, server_port))
        print("连接成功！")

        # 发送测试消息
        test_messages = ["hello", "fire", "test"]

        for msg in test_messages:
            print(f"\n发送: {msg}")
            client.send(msg.encode('utf-8'))

            response = client.recv(1024).decode('utf-8')
            print(f"接收: {response}")

            time.sleep(0.5)

        # 关闭连接
        client.close()
        print("\n测试完成")

    except socket.timeout:
        print("连接超时，请检查服务器是否运行")
    except ConnectionRefusedError:
        print("连接被拒绝，请确保服务器已启动")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_connection()