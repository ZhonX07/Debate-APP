#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, Any, Optional, List

class ConfigValidationError(Exception):
    """配置验证错误"""
    pass

class DebateConfig:
    """辩论赛配置管理类"""
    
    @classmethod
    def from_file(cls, file_path):
        """从文件加载配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            DebateConfig: 配置对象
            
        Raises:
            ConfigValidationError: 配置验证失败
        """
        # 每次加载配置都会新建 DebateConfig 实例，不会残留旧数据
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = cls(data)
                config.validate()
                return config
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"JSON解析错误: {e}")
        except Exception as e:
            raise ConfigValidationError(f"配置文件解析失败: {e}")

    def __init__(self, data):
        """初始化配置
        
        Args:
            data: 配置数据字典
        """
        self.data = data
        
    def validate(self):
        """验证配置有效性
        
        Raises:
            ConfigValidationError: 配置验证失败
        """
        # 验证必要的顶级字段
        required_fields = ['topic', 'affirmative', 'negative', 'rounds']
        for field in required_fields:
            if field not in self.data:
                raise ConfigValidationError(f"缺少必要的配置字段: {field}")
                
        # 验证辩方配置
        for side in ['affirmative', 'negative']:
            if not isinstance(self.data[side], dict):
                raise ConfigValidationError(f"{side} 字段必须是对象")
                
            # 验证辩方必要字段
            side_required = ['school', 'viewpoint']
            for field in side_required:
                if field not in self.data[side]:
                    raise ConfigValidationError(f"{side} 缺少必要字段: {field}")
        
        # 验证回合配置
        if not isinstance(self.data['rounds'], list):
            raise ConfigValidationError("rounds 字段必须是数组")
            
        for i, round_data in enumerate(self.data['rounds']):
            if not isinstance(round_data, dict):
                raise ConfigValidationError(f"第 {i+1} 个回合配置必须是对象")
                
            # 验证回合必要字段
            round_required = ['side', 'speaker', 'type', 'time']
            for field in round_required:
                if field not in round_data:
                    raise ConfigValidationError(f"第 {i+1} 个回合缺少必要字段: {field}")
                    
            # 验证side字段值
            if round_data['side'] not in ['affirmative', 'negative']:
                if round_data['type'] != '自由辩论':
                    raise ConfigValidationError(
                        f"第 {i+1} 个回合的 side 字段必须是 'affirmative' 或 'negative'"
                    )
            
            # 验证时间字段
            if not isinstance(round_data['time'], int) or round_data['time'] <= 0:
                raise ConfigValidationError(
                    f"第 {i+1} 个回合的 time 字段必须是正整数"
                )
        
        # 验证辩手角色字段
        if 'debater_roles' in self.data:
            if not isinstance(self.data['debater_roles'], dict):
                raise ConfigValidationError("debater_roles 字段必须是对象")
                
            # 检查是否包含必要的辩手角色
            recommended_roles = [
                'affirmative_first', 'affirmative_second', 'affirmative_third', 'affirmative_fourth',
                'negative_first', 'negative_second', 'negative_third', 'negative_fourth'
            ]
            
            missing_roles = [role for role in recommended_roles if role not in self.data['debater_roles']]
            if missing_roles:
                # 不抛出错误，但记录警告
                import logging
                logging.getLogger('debate_app').warning(f"配置中缺少推荐的辩手角色: {', '.join(missing_roles)}")
            
    def to_dict(self) -> Dict[str, Any]:
        """返回配置数据字典
        
        Returns:
            Dict: 配置数据
        """
        return self.data
    
    def save(self, file_path: str) -> None:
        """保存配置到文件
        
        Args:
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
            
    def get_rounds(self) -> List[Dict[str, Any]]:
        """获取所有回合配置
        
        Returns:
            List[Dict]: 回合配置列表
        """
        return self.data.get('rounds', [])
    
    def get_debater_roles(self) -> Dict[str, str]:
        """获取辩手角色映射
        
        Returns:
            Dict: 角色到姓名的映射
        """
        roles = self.data.get('debater_roles', {})
        # 处理旧版格式（如果存在）
        if not roles and 'affirmative' in self.data and 'negative' in self.data:
            # 尝试从旧结构中提取辩手信息
            aff_debaters = self.data['affirmative'].get('debaters', {})
            neg_debaters = self.data['negative'].get('debaters', {})
            
            # 生成新格式
            roles = {
                'affirmative_first': aff_debaters.get('first', ''),
                'affirmative_second': aff_debaters.get('second', ''),
                'affirmative_third': aff_debaters.get('third', ''),
                'affirmative_fourth': aff_debaters.get('fourth', ''),
                'negative_first': neg_debaters.get('first', ''),
                'negative_second': neg_debaters.get('second', ''),
                'negative_third': neg_debaters.get('third', ''),
                'negative_fourth': neg_debaters.get('fourth', '')
            }
        
        return roles
