"""
邮件警报发送模块

功能：
- 通过SMTP发送警报邮件
- 支持附加警报帧图片
- 支持多收件人
- 异步发送避免阻塞主线程
"""

import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""
    
    def __init__(self, config: Dict):
        """
        初始化邮件发送器
        
        Args:
            config: 邮件配置字典，包含以下字段：
                - enabled: 是否启用邮件警报
                - smtp_server: SMTP服务器地址
                - smtp_port: SMTP端口（默认465使用SSL，587使用TLS）
                - sender_email: 发件人邮箱
                - sender_password: 发件人邮箱密码/授权码
                - recipients: 收件人邮箱列表
                - use_ssl: 是否使用SSL（默认True）
                - subject_prefix: 邮件主题前缀
        """
        self.enabled = config.get('enabled', False)
        
        if not self.enabled:
            logger.info("📧 邮件警报功能未启用")
            return
        
        # SMTP配置
        self.smtp_server = config.get('smtp_server', 'smtp.qq.com')
        self.smtp_port = config.get('smtp_port', 465)
        self.sender_email = config.get('sender_email', '')
        self.sender_password = config.get('sender_password', '')
        self.use_ssl = config.get('use_ssl', True)
        
        # 收件人（支持单个或列表）
        recipients = config.get('recipients', [])
        if isinstance(recipients, str):
            self.recipients = [recipients]
        else:
            self.recipients = list(recipients)
        
        # 邮件设置
        self.subject_prefix = config.get('subject_prefix', '[DLC警报]')
        
        # 验证配置
        if self._validate_config():
            logger.info(f"📧 邮件警报已启用")
            logger.info(f"   SMTP: {self.smtp_server}:{self.smtp_port}")
            logger.info(f"   发件人: {self.sender_email}")
            logger.info(f"   收件人: {', '.join(self.recipients)}")
        else:
            self.enabled = False
            logger.warning("⚠️  邮件配置不完整，邮件警报已禁用")
    
    def _validate_config(self) -> bool:
        """验证配置是否完整"""
        if not self.smtp_server:
            logger.warning("未配置SMTP服务器")
            return False
        if not self.sender_email:
            logger.warning("未配置发件人邮箱")
            return False
        if not self.sender_password:
            logger.warning("未配置发件人密码/授权码")
            return False
        if not self.recipients:
            logger.warning("未配置收件人")
            return False
        return True
    
    def send_alert(self, alert_info: Dict, frame: Optional[np.ndarray] = None):
        """
        发送警报邮件（异步）
        
        Args:
            alert_info: 警报信息字典
            frame: 警报帧图像（RGB格式，可选）
        """
        if not self.enabled:
            return
        
        # 使用线程异步发送，避免阻塞主线程
        thread = threading.Thread(
            target=self._send_alert_async,
            args=(alert_info, frame),
            daemon=True
        )
        thread.start()
    
    def _send_alert_async(self, alert_info: Dict, frame: Optional[np.ndarray]):
        """异步发送邮件的实际逻辑"""
        try:
            # 构建邮件
            msg = self._build_email(alert_info, frame)
            
            # 发送邮件
            if self.use_ssl:
                # SSL连接（端口465）
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(
                        self.sender_email,
                        self.recipients,
                        msg.as_string()
                    )
            else:
                # TLS连接（端口587）
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(
                        self.sender_email,
                        self.recipients,
                        msg.as_string()
                    )
            
            logger.info(f"📧 警报邮件已发送至: {', '.join(self.recipients)}")
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ 邮件发送失败：SMTP认证错误，请检查邮箱和授权码")
        except smtplib.SMTPConnectError:
            logger.error(f"❌ 邮件发送失败：无法连接到SMTP服务器 {self.smtp_server}:{self.smtp_port}")
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
    
    def _build_email(self, alert_info: Dict, frame: Optional[np.ndarray]) -> MIMEMultipart:
        """构建邮件内容"""
        msg = MIMEMultipart('related')
        
        # 邮件头
        timestamp = alert_info.get('timestamp', datetime.now())
        scenario_name = alert_info.get('scenario_name', '未知场景')
        confidence = alert_info.get('confidence', 0)
        alert_level = alert_info.get('alert_level', 'high')
        
        msg['Subject'] = f"{self.subject_prefix} {scenario_name} - 置信度{confidence:.1%}"
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(self.recipients)
        msg['Date'] = formatdate(localtime=True)
        
        # 邮件正文（HTML格式）
        level_color = {
            'high': '#dc3545',    # 红色
            'medium': '#fd7e14',  # 橙色
            'low': '#ffc107'      # 黄色
        }.get(alert_level, '#dc3545')
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: {level_color}; color: white; padding: 15px; border-radius: 5px;">
                <h1 style="margin: 0;">⚠️ DLC智能养老摄像头警报</h1>
            </div>
            
            <div style="padding: 20px; border: 1px solid #ddd; margin-top: 10px; border-radius: 5px;">
                <h2 style="color: {level_color};">检测到异常情况</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>场景类型:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{scenario_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>置信度:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{confidence:.1%}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>警报级别:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{alert_level.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>触发时间:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                
                {"<h3>警报帧截图:</h3><img src='cid:alert_frame' style='max-width: 100%; border: 1px solid #ddd; border-radius: 5px;'>" if frame is not None else ""}
            </div>
            
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                此邮件由DLC智能养老摄像头系统自动发送，请及时查看并处理。
            </p>
        </body>
        </html>
        """
        
        # 添加HTML正文
        msg_html = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(msg_html)
        
        # 添加图片附件
        if frame is not None:
            try:
                # RGB转BGR，编码为JPEG
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                _, img_encoded = cv2.imencode('.jpg', frame_bgr)
                img_data = img_encoded.tobytes()
                
                # 创建图片附件
                img_mime = MIMEImage(img_data, _subtype='jpeg')
                img_mime.add_header('Content-ID', '<alert_frame>')
                img_mime.add_header('Content-Disposition', 'inline', 
                                   filename=f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg")
                msg.attach(img_mime)
                
            except Exception as e:
                logger.warning(f"警报帧附加失败: {e}")
        
        return msg
    
    def test_connection(self) -> bool:
        """
        测试SMTP连接
        
        Returns:
            连接是否成功
        """
        if not self.enabled:
            return False
        
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.sender_email, self.sender_password)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
            
            logger.info("✅ SMTP连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP连接测试失败: {e}")
            return False
