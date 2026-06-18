from pathlib import Path

# 系统监控频率
SYSTEM_MONITOR_FREQ = 60  # 定时输出系统信息 (单位: s)

# 上传文件后最小允许的磁盘空闲空间 (300MB)
# 文件上传后如果空间不足，直接拒绝上传
UPLOAD_FILE_MIN_FREE_SPACE = 300 * 1024 * 1024

# FTP服务器配置（主用户，服务器内部储存）
FTP_PORT = 2121  # 端口号
FTP_USERNAME = "admin"  # 用户名
FTP_PASSWORD = "230728"  # 密码
# FTP_DIRECTORY = "/storage/emulated/0" # 根目录
FTP_DIRECTORY = "/"  # 根目录

# FTP服务器配置（USB用户，访问U盘专用）
FTP_USB_USERNAME = "usb"  # 用户名
FTP_USB_PASSWORD = "230728"  # 密码
# FTP_USB_DIRECTORY = "/storage/emulated/0" # 根目录
FTP_USB_DIRECTORY = "/mnt/media_rw/sdcard0/"  # 根目录

# 网页服务器配置（网盘+网页控制台+LocalProxy服务端）
WEB_SERVER_THREADS = 5  # 线程数，越大访问网页速度越快，但也更占用CPU资源
WEB_SERVER_PORT = 8888  # 端口号

# 网页控制台配置
WEB_CONSOLE_USERNAME = ""  # 用户名
WEB_CONSOLE_PASSWORD = "230728"  # 密码
WEBSOCKET_PORT = 8889  # WebSocket后端端口号

# 网盘配置
# IP地址白名单
FILE_EXPLORER_ALLOWED_IPS = [
    '192.168.5.35',  # 本地开发: MAC
    '192.168.5.30',  # 本地开发（盒子本身）
    '127.0.0.1',  # 本地开发（盒子本身）
    '172.16.192.1',  # 盒子本身
    '172.16.194.37',  # 1
    '172.16.193.142',  # 2
    '172.16.196.182',  # 3
    '172.16.197.195',  # 4
    '172.16.193.136',  # 7
    '172.16.193.145',  # 8
    '172.16.192.151',  # 9
    '172.16.194.158',  # 10
    '172.16.195.9',  # 11
    '172.16.195.176',  # 12
    '172.16.194.149',  # 13
    '172.16.194.91',  # 13
    '172.16.194.254',  # 13
    "172.16.192.74",  # 14
    '172.16.114.21',  # 15
    '172.16.192.147',  # 18
    '172.16.114.73',  # 物理实验室1
    '172.16.114.30',  # 物理实验室2
    '172.16.194.97'  # 二楼走班
]
FILE_EXPLORER_ALLOWED_WEEKDAYS = [1, 2, 3, 4, 5, 6, 7]  # 网站开放星期数
FILE_EXPLORER_BASE_DIR = "../../服务器文件"  # 网盘根目录
# FILE_EXPLORER_BASE_DIR = "/mnt/media_rw/sdcard0/服务器文件" # 网盘根目录
FILE_EXPLORER_NEWS_DIR_BASENAME = "新闻"  # 新闻联播根目录，防止新闻页面被屏蔽

# 新闻联播下载器配置
NEWS_SAVE_DIR = Path("../../服务器文件/新闻")  # 新闻联播保存路径
# NEWS_SAVE_DIR = Path("/mnt/media_rw/sdcard0/服务器文件/新闻") # 新闻联播保存路径
NEWS_SPEED = 1.8  # 新闻播放速度
NEWS_SCHEDULE_TIME = "16:00:00"  # 新闻下载时间

# LocalProxy服务器配置
LOCALPROXY_USERNAME = ""  # 官网用户名
LOCALPROXY_PASSWORD = "yshnb666"  # 官网密码
