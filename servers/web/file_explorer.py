import errno
import os
import shutil
import chardet

from datetime import datetime
from assets.config_server import FILE_EXPLORER_ALLOWED_IPS, FILE_EXPLORER_ALLOWED_WEEKDAYS, FILE_EXPLORER_NEWS_DIR_BASENAME, UPLOAD_FILE_MIN_FREE_SPACE
from werkzeug.security import safe_join
from flask import Blueprint, make_response, send_file, current_app, request, jsonify
from utils.utils_lib import LoggerManager

file_explorer = Blueprint(
    'file_explorer', __name__, url_prefix='/'
)
logger:LoggerManager = LoggerManager()

def get_base_directory() -> str:
    """从配置中获取基础目录"""
    return current_app.config.get('BASE_DIRECTORY', '')

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除或替换不安全的字符"""
    # 移除Windows文件名中不允许的字符
    illegal_chars = r'<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '')
    # 替换空格为下划线
    # filename = filename.replace(' ', '_')
    return filename

@file_explorer.route('/')
def index():
    """主页路由"""
    client_ip = request.remote_addr
    logger.info(f'IP {client_ip} 尝试访问文件浏览器')
    
    if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
        logger.warning(f'IP {client_ip} 对文件浏览器的访问被禁止：不在白名单')
        return "禁止访问：IP不在白名单", 403
    weekday_num = datetime.now().isoweekday()
    if weekday_num not in FILE_EXPLORER_ALLOWED_WEEKDAYS:
        logger.warning(f'IP {client_ip} 对文件浏览器的访问被禁止：网站当前未开放')
        return f"本网站仅在星期{FILE_EXPLORER_ALLOWED_WEEKDAYS}开放。", 400

    html_file = os.path.abspath('file_explorer.html')
    if os.path.exists(html_file):
        return send_file(html_file)
    else:
        logger.warning("文件浏览器页面未找到")
        return "文件浏览器页面未找到，请联系管理员", 404

@file_explorer.route('/news')
def news_page():
    """新闻页路由"""
    client_ip = request.remote_addr
    logger.info(f'IP {client_ip} 尝试访问新闻播放页')
    
    if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
        logger.warning(f'IP {client_ip} 对新闻播放页的访问被禁止：不在白名单')
        return "禁止访问：IP不在白名单", 403

    html_file = os.path.abspath('file_explorer.html')
    if os.path.exists(html_file):
        return send_file(html_file)
    else:
        logger.warning("文件浏览器页面未找到")
        return "文件浏览器页面未找到，请联系管理员", 404

@file_explorer.route('/api/list')
@file_explorer.route('/api/list/<path:dirpath>')
def list_directory(dirpath=''):
    """获取目录内容（JSON格式）"""
    client_ip = request.remote_addr
    logger.info(f'IP {client_ip} 尝试获取 {"根" if not dirpath else dirpath} 目录内容')

    # 始终允许访问新闻播放页
    if FILE_EXPLORER_NEWS_DIR_BASENAME not in dirpath:
        if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
            logger.warning(f'IP {client_ip} 获取目录内容被禁止：不在白名单')
            return jsonify({'success': False, 'error': '禁止访问：IP不在白名单'}), 403
        weekday_num = datetime.now().isoweekday()
        if weekday_num not in FILE_EXPLORER_ALLOWED_WEEKDAYS:
            logger.warning(f'IP {client_ip} 获取目录内容被禁止：网站当前未开放')
            return jsonify({'success': False, 'error': f'本网站仅在星期{FILE_EXPLORER_ALLOWED_WEEKDAYS}开放。'}), 400

    # 获取完整路径并校验
    full_path = safe_join(get_base_directory(), dirpath)
    if full_path is None:
        return jsonify({'success': False, 'error': '路径为空'}), 400
    elif not os.path.exists(full_path):
        return jsonify({'success': False, 'error': '路径不存在'}), 400
    elif not os.path.isdir(full_path):
        return jsonify({'success': False, 'error': '路径非文件夹'}), 400

    items = []
    try:
        # 遍历文件夹，获取目录内容
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            item_info = {
                'name': item,
                'type': 'dir' if os.path.isdir(item_path) else 'file',
                'size': None if os.path.isdir(item_path) else os.path.getsize(item_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            items.append(item_info)

        # 排序：文件夹在前，文件在后，按名称排序
        items.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))

        return jsonify({
            'success': True,
            'items': items
        })
    except PermissionError:
        return jsonify({'success': False, 'error': '无权限访问该目录'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': f'读取目录失败: {str(e)}'}), 500


@file_explorer.route('/api/mkdir', methods=['POST'])
@file_explorer.route('/api/mkdir/<path:dirpath>', methods=['POST'])
def mkdir(dirpath=''):
    """处理新建文件夹请求"""
    client_ip = request.remote_addr

    if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
        logger.warning(f'IP {client_ip} 新建文件夹被禁止：不在白名单')
        return jsonify({'success': False, 'error': '禁止访问：IP不在白名单'}), 403
    weekday_num = datetime.now().isoweekday()
    if weekday_num not in FILE_EXPLORER_ALLOWED_WEEKDAYS:
        logger.warning(f'IP {client_ip} 新建文件夹被禁止：网站当前未开放')
        return jsonify({'success': False, 'error': f'本网站仅在星期{FILE_EXPLORER_ALLOWED_WEEKDAYS}开放。'}), 400

    # 获取要新建的文件夹名称
    data = request.get_json()
    folder_name = data.get('folder_name', '').strip() if data else ''
    if not folder_name:
        return jsonify({'success': False, 'error': '文件夹名称不能为空'}), 400
    folder_name = sanitize_filename(folder_name)
    logger.info(f'IP {client_ip} 尝试在 {"根" if not dirpath else dirpath} 下新建文件夹: {folder_name}')

    # 获取带文件夹名称的完整路径并校验
    full_path = safe_join(get_base_directory(), dirpath, folder_name)
    if full_path is None:
        return jsonify({'success': False, 'error': '非法路径，请检查文件名中是否有特殊字符'}), 400
    elif os.path.exists(full_path):
        return jsonify({'success': False, 'error': '文件夹已存在'}), 400

    # 尝试新建文件夹
    try:
        os.makedirs(full_path)
        logger.info(f'IP {client_ip} 成功新建文件夹：{full_path}')
        return jsonify({'success': True, 'message': '创建成功'}), 200
    except PermissionError:
        logger.warning(f'IP {client_ip} 新建文件夹 {full_path} 失败：权限不足，无法新建文件夹')
        return jsonify({'success': False, 'error': '权限不足，无法创建文件夹'}), 403
    except Exception as e:
        logger.warning(f'IP {client_ip} 新建文件夹 {full_path} 失败：{str(e)}')
        return jsonify({'success': False, 'error': f'创建失败: {str(e)}'}), 500

@file_explorer.route('/api/file')
@file_explorer.route('/api/file/<path:filepath>')
def serve_file(filepath=''):
    """提供文件服务：浏览器支持预览的文件会内联显示，否则下载"""
    client_ip = request.remote_addr
    logger.info(f'IP {client_ip} 尝试获取文件: {filepath}')


    # 始终允许访问新闻播放页
    if FILE_EXPLORER_NEWS_DIR_BASENAME not in filepath:
        if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
            logger.warning(f'IP {client_ip} 获取文件被禁止：不在白名单')
            return jsonify({'success': False, 'error': '禁止访问：IP不在白名单'}), 403
        weekday_num = datetime.now().isoweekday()
        if weekday_num not in FILE_EXPLORER_ALLOWED_WEEKDAYS:
            logger.warning(f'IP {client_ip} 获取文件被禁止：网站当前未开放')
            return jsonify({'success': False, 'error': f'本网站仅在星期{FILE_EXPLORER_ALLOWED_WEEKDAYS}开放。'}), 400

    # 获取完整路径并校验
    full_path = safe_join(get_base_directory(), filepath)
    if full_path is None:
        return jsonify({'success': False, 'error': '文件路径为空'}), 400
    elif os.path.isdir(full_path):
        return jsonify({'success': False, 'error': '不支持文件夹'}), 400
    elif not os.path.exists(full_path):
        return jsonify({'success': False, 'error': '文件不存在'}), 400

    # 对于文本文件，检测编码并转换（修复非utf-8编码乱码）
    if is_text_file(full_path):
        return convert_and_send_text_file(full_path)
    else:
        return send_file(full_path)

def is_text_file(filepath):
    """判断是否为文本文件"""
    text_extensions = {'.txt', '.log', '.ini', '.cfg', '.conf', '.csv', '.md', '.xml', '.json', '.yaml', '.yml', '.html', '.htm', '.css', '.js', '.py', '.java', '.c', '.cpp', '.h', '.sql', '.bat', '.sh', '.rtf', '.inf', '.reg', '.nfo', '.ps1', '.vbs', '.lua', '.r', '.jl', '.scala', '.kt', '.groovy', '.dart', '.fs', '.clj', '.hs', '.erl', '.ex', '.cr', '.nim', '.zig'}
    ext = os.path.splitext(filepath)[1].lower()
    return ext in text_extensions

def convert_and_send_text_file(filepath):
    """检测编码并转换为UTF-8后发送"""
    # 读取原始内容
    with open(filepath, 'rb') as f:
        raw_data = f.read()
    
    # 检测编码
    detected = chardet.detect(raw_data)
    encoding = str(detected.get('encoding', 'utf-8'))
    
    # 解码并重新编码为UTF-8
    text_content = raw_data.decode(encoding, errors='replace')
    utf8_content = text_content.encode('utf-8')
    
    # 创建响应
    response = make_response(utf8_content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@file_explorer.route('/api/upload', methods=['POST'])
@file_explorer.route('/api/upload/<path:dirpath>', methods=['POST'])
def upload(dirpath=''):
    """处理文件上传请求"""
    client_ip = request.remote_addr
    
    if client_ip not in FILE_EXPLORER_ALLOWED_IPS:
        logger.warning(f'IP {client_ip} 上传文件被禁止：不在白名单')
        return jsonify({'success': False, 'error': '禁止访问：IP不在白名单'}), 403
    weekday_num = datetime.now().isoweekday()
    if weekday_num not in FILE_EXPLORER_ALLOWED_WEEKDAYS:
        logger.warning(f'IP {client_ip} 上传文件被禁止：网站当前未开放')
        return jsonify({'success': False, 'error': f'本网站仅在星期{FILE_EXPLORER_ALLOWED_WEEKDAYS}开放。'}), 400

    # 获取上传的文件
    file = request.files.get('file')
    if file is None or not file.filename:
        return jsonify({'success': False, 'error': '未上传文件'}), 400
    logger.info(f'IP {client_ip} 尝试在 {"根" if not dirpath else dirpath} 下上传文件: {file.filename}')

    # 获取完整路径并校验
    filename = sanitize_filename(file.filename)
    full_path = safe_join(get_base_directory(), dirpath, filename)
    if full_path is None:
        return jsonify({'success': False, 'error': '非法路径，请检查文件名中是否有特殊字符'}), 400
    elif os.path.exists(full_path):
        return jsonify({'success': False, 'error': '文件已存在'}), 400

    # 获取上传的文件大小
    target_dir = os.path.dirname(full_path)
    free_bytes = shutil.disk_usage(target_dir).free
    free_mb = round(free_bytes / 1024 / 1024, 2)

    # 服务器剩余空间检测
    if free_bytes < UPLOAD_FILE_MIN_FREE_SPACE:
        free_mb = round(free_bytes / 1024 / 1024, 2)
        logger.warning(f"IP {client_ip} 上传文件失败：服务器存储空间不足，当前剩余 {free_mb}MB")
        return jsonify({
            'success': False,
            'error': f'服务器存储空间不足（剩余{free_mb}MB），请联系管理员'
        }), 500

    # 上传后剩余空间不足，拒绝上传
    file_size = request.content_length or 0
    if file_size <= 0:
        return jsonify({'success': False, 'error': '文件大小无效'}), 400
    after_upload_free = max(free_bytes - file_size, 0)
    if after_upload_free < UPLOAD_FILE_MIN_FREE_SPACE:
        after_mb = round(after_upload_free / 1024 / 1024, 2)
        logger.warning(f"IP {client_ip} 上传文件被拒绝：上传后服务器剩余空间仅 {after_mb}MB，低于安全阈值")
        return jsonify({
            'success': False,
            'error': f'拒绝上传：上传后服务器剩余空间仅 {after_mb}MB，低于安全阈值'
        }), 500

    try:
        file.save(full_path)
        logger.info(f'IP {client_ip} 成功上传文件：{full_path}')
        return jsonify({'success': True, 'message': '上传成功', 'filename': filename}), 200
    except PermissionError:
        logger.warning(f'IP {client_ip} 上传文件 {full_path} 失败：服务器错误，权限不足，无法保存文件')
        return jsonify({'success': False, 'error': '服务器错误：权限不足，无法保存文件'}), 500
    except OSError as e:
        if e.errno == errno.ENOSPC: # 磁盘空间不足
            logger.warning(f'IP {client_ip} 上传文件 {full_path} 失败：服务器存储空间不足')
            return jsonify({'success': False, 'error': '服务器存储空间不足'}), 500
        else:
            raise  # 其他系统错误继续抛出
    except Exception as e:
        logger.warning(f'IP {client_ip} 上传文件 {full_path} 失败：{str(e)}')
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500
    