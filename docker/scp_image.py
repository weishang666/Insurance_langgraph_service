import paramiko
from scp import SCPClient

def upload_file():
    # 配置参数
    local_file_path = "insurance-qa-v1.tar"  # 本地文件路径，替换为实际路径
    remote_host = "10.176.27.166"                       # 远程服务器IP
    remote_port = 22                                    # SSH端口
    remote_username = "tenant"                          # 用户名
    remote_password = "Root@10086"                      # 密码
    remote_directory = "/home/tenant/docker/insurance_qa/"                  # 远程目录

    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        # 自动接受未知的主机密钥
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接远程服务器
        print(f"连接到 {remote_username}@{remote_host}:{remote_port}...")
        ssh.connect(
            hostname=remote_host,
            port=remote_port,
            username=remote_username,
            password=remote_password
        )
        
        # 使用SCPClient上传文件
        with SCPClient(ssh.get_transport()) as scp:
            print(f"开始上传文件: {local_file_path}")
            # 上传文件，remote_path指定远程目录，preserve_times保持文件时间戳
            scp.put(local_file_path, remote_path=remote_directory, preserve_times=True)
            print(f"文件已成功上传到 {remote_directory}")

    except FileNotFoundError:
        print(f"错误: 本地文件不存在 - {local_file_path}")
        return False
    except paramiko.AuthenticationException:
        print("错误: 认证失败，请检查用户名和密码")
        return False
    except Exception as e:
        print(f"上传过程中发生错误: {str(e)}")
        return False
    finally:
        # 确保连接关闭
        if ssh.get_transport().is_active():
            ssh.close()
            print("已关闭与服务器的连接")

    return True

if __name__ == "__main__":
    upload_file()
