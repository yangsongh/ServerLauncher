# -*- coding: utf-8 -*-
# @Author : yangsongh
# @File : whitelist_manager.py

import ipaddress
import fnmatch
from .utils_lib import LoggerManager
from urllib.parse import urlparse
from typing import List, Optional, Union

class WhitelistManager:
    """白名单管理器，支持IP白名单和域名白名单"""
    
    def __init__(self, logger: LoggerManager):
        self.logger = logger
        self.enable_ip_whitelist = False
        self.enable_domain_whitelist = False
        self.ip_whitelist: List[str] = []
        self.domain_whitelist: List[str] = []
        
        # 缓存的IP网络对象，支持IPv4和IPv6
        self._ip_networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        # 缓存的域名模式列表
        self._domain_patterns: List[str] = []
    
    def update_config(self, config_manager):
        """从配置管理器更新白名单设置"""
        self.enable_ip_whitelist = config_manager.cfgs.get('enable_ip_whitelist', False)
        self.enable_domain_whitelist = config_manager.cfgs.get('enable_domain_whitelist', False)
        
        # 更新IP白名单
        if self.enable_ip_whitelist:
            self.ip_whitelist = config_manager.cfgs.get('ip_whitelist', [])
            self._compile_ip_whitelist()
            self.logger.debug(f"IP白名单已启用，共 {len(self.ip_whitelist)} 条规则")
        else:
            self.logger.debug("IP白名单未启用")
        
        # 更新域名白名单
        if self.enable_domain_whitelist:
            self.domain_whitelist = config_manager.cfgs.get('domain_whitelist', [])
            self._compile_domain_whitelist()
            self.logger.debug(f"域名白名单已启用，共 {len(self.domain_whitelist)} 条规则")
        else:
            self.logger.debug("域名白名单未启用")
    
    def _compile_ip_whitelist(self):
        """编译IP白名单，支持CIDR格式"""
        self._ip_networks = []
        for ip_rule in self.ip_whitelist:
            try:
                # 尝试解析为CIDR网络
                if '/' in ip_rule:
                    network = ipaddress.ip_network(ip_rule, strict=False)
                    self._ip_networks.append(network)
                else:
                    # 单个IP地址
                    network = ipaddress.ip_network(f"{ip_rule}/32", strict=False)
                    self._ip_networks.append(network)
            except ValueError as e:
                self.logger.warning(f"无效的IP规则 '{ip_rule}': {e}")
    
    def _compile_domain_whitelist(self):
        """编译域名白名单，将通配符转换为fnmatch模式"""
        self._domain_patterns = []
        for domain_rule in self.domain_whitelist:
            # 将*通配符转换为fnmatch可以识别的模式
            pattern = domain_rule.replace('*', '*')
            self._domain_patterns.append(pattern)
    
    def is_client_ip_allowed(self, client_ip: str) -> bool:
        """检查客户端IP是否允许访问"""
        if not self.enable_ip_whitelist:
            return True
        
        if not client_ip:
            self.logger.warning("无法获取客户端IP，拒绝访问")
            return False
        
        try:
            # 解析客户端IP
            client_ip_obj = ipaddress.ip_address(client_ip)
            
            # 检查是否匹配任何规则
            for network in self._ip_networks:
                if client_ip_obj in network:
                    self.logger.debug(f"IP {client_ip} 匹配白名单规则 {network}")
                    return True
            
            self.logger.debug(f"IP {client_ip} 不在白名单中，拒绝访问")
            return False
            
        except ValueError as e:
            self.logger.error(f"解析客户端IP失败 {client_ip}: {e}")
            return False
    
    def is_domain_allowed(self, hostname: str) -> bool:
        """检查域名是否允许访问"""
        if not self.enable_domain_whitelist:
            return True
        
        if not hostname:
            return False
        
        # 移除端口号
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        
        # 转换为小写以进行不区分大小写的匹配
        hostname_lower = hostname.lower()
        
        for pattern in self._domain_patterns:
            # 使用fnmatch进行通配符匹配
            if fnmatch.fnmatch(hostname_lower, pattern.lower()):
                self.logger.debug(f"域名 {hostname} 匹配白名单规则 {pattern}")
                return True
        
        self.logger.debug(f"域名 {hostname} 不在白名单中，拒绝访问")
        return False
    
    def extract_hostname_from_url(self, url: str, method: str = "GET") -> Optional[str]:
        """从URL中提取主机名（主要用于HTTP代理）"""
        try:
            if method == "CONNECT":
                # HTTPS CONNECT请求格式: host:port
                if ':' in url:
                    return url.split(':')[0]
                return url
            else:
                # HTTP请求
                parsed = urlparse(url)
                hostname = parsed.hostname
                if hostname:
                    return hostname
                return None
        except Exception as e:
            self.logger.error(f"从URL提取主机名失败: {e}")
            return None
    
    def get_ip_whitelist_stats(self) -> dict:
        """获取IP白名单统计信息"""
        return {
            "enabled": self.enable_ip_whitelist,
            "rule_count": len(self.ip_whitelist),
            "rules": self.ip_whitelist if self.logger.logger.level <= 10 else []  # debug级别才显示详细规则
        }
    
    def get_domain_whitelist_stats(self) -> dict:
        """获取域名白名单统计信息"""
        return {
            "enabled": self.enable_domain_whitelist,
            "rule_count": len(self.domain_whitelist),
            "rules": self.domain_whitelist if self.logger.logger.level <= 10 else []
        }
    
    def reload_config(self, config_manager):
        """重新加载配置"""
        self.logger.info("重新加载白名单配置...")
        self.update_config(config_manager)
        