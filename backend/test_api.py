# -*- coding: utf-8 -*-
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = 'http://127.0.0.1:5000'

def check_server():
    """检查服务器是否在运行"""
    try:
        response = requests.get(f'{BASE_URL}/')
        return response.status_code < 500
    except requests.exceptions.ConnectionError:
        return False

def test_events():
    # 检查服务器是否在运行
    if not check_server():
        print("错误: 无法连接到服务器")
        print("请确保 Flask 应用正在运行，并且监听在 http://127.0.0.1:5000")
        print("运行命令: python app.py")
        return

    try:
        # 1. 尝试注册管理员用户
        register_data = {
            "username": "admin2",
            "password": "adminpass",
            "name": "管理员2",
            "student_id": "2024002",
            "college": "计算机学院",
            "role": "admin"
        }
        print("\n1. 尝试注册管理员用户...")
        response = requests.post(f'{BASE_URL}/register', json=register_data)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        
        # 2. 登录获取token
        login_data = {
            "username": "admin2",
            "password": "adminpass"
        }
        print("\n2. 尝试登录...")
        response = requests.post(f'{BASE_URL}/login', json=login_data)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        
        # 检查登录响应
        if response.status_code == 200:
            try:
                token = response.json()['access_token']
                print("登录成功，获取到token")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"解析token失败: {e}")
                return
        else:
            print("登录失败，请检查用户名和密码")
            return
            
        headers = {'Authorization': f'Bearer {token}'}
        
        # 3. 创建活动
        event_data = {
            "name": "升旗仪式",
            "time": (datetime.now() + timedelta(days=1)).isoformat(),
            "uniform_required": "着正装"
        }
        print("\n3. 创建活动...")
        response = requests.post(f'{BASE_URL}/api/events', json=event_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            try:
                event_id = response.json()['event_id']
                
                # 4. 获取活动列表
                print("\n4. 获取活动列表...")
                response = requests.get(f'{BASE_URL}/api/events', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
                
                # 5. 获取特定活动详情
                print("\n5. 获取活动详情...")
                response = requests.get(f'{BASE_URL}/api/events/{event_id}', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
            except json.JSONDecodeError as e:
                print(f"解析响应失败: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"创建活动失败，状态码: {response.status_code}")

        # 6. 创建升降旗记录
        flag_data = {
            "date": datetime.now().date().isoformat(),
            "type": "raise",
            "photo_url": "http://example.com/photo.jpg"
        }
        print("\n6. 创建升降旗记录...")
        response = requests.post(f'{BASE_URL}/api/records', json=flag_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            try:
                record_id = response.json()['record_id']
                
                # 7. 获取待审核的升降旗记录
                print("\n7. 获取待审核的升降旗记录...")
                response = requests.get(f'{BASE_URL}/api/records/pending', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
                
                # 8. 审核升降旗记录
                print("\n8. 审核升降旗记录...")
                review_data = {
                    "action": "approve"
                }
                response = requests.put(f'{BASE_URL}/api/records/{record_id}/review', json=review_data, headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
            except json.JSONDecodeError as e:
                print(f"解析响应失败: {e}")
                print(f"原始响应: {response.text}")

        # 9. 创建训练
        training_data = {
            "name": "基础训练",
            "type": "basic",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
            "points": 5
        }
        print("\n9. 创建训练...")
        response = requests.post(f'{BASE_URL}/api/trainings', json=training_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            try:
                training_id = response.json()['training_id']
                
                # 10. 获取训练列表
                print("\n10. 获取训练列表...")
                response = requests.get(f'{BASE_URL}/api/trainings', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
                
                # 11. 获取训练详情
                print("\n11. 获取训练详情...")
                response = requests.get(f'{BASE_URL}/api/trainings/{training_id}', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
                
                # 12. 注册参加训练
                print("\n12. 注册参加训练...")
                response = requests.post(f'{BASE_URL}/api/trainings/{training_id}/register', headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
                if response.status_code == 201:
                    try:
                        registration_id = response.json()['registration_id']
                        
                        # 13. 确认训练参与
                        print("\n13. 确认训练参与...")
                        response = requests.put(f'{BASE_URL}/api/registrations/{registration_id}/confirm', headers=headers)
                        print(f"状态码: {response.status_code}")
                        print(f"响应内容: {response.text}")
                    except json.JSONDecodeError as e:
                        print(f"解析响应失败: {e}")
                        print(f"原始响应: {response.text}")
                else:
                    print("训练注册失败，跳过确认步骤")
            except json.JSONDecodeError as e:
                print(f"解析响应失败: {e}")
                print(f"原始响应: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("响应内容:", response.text)
    except Exception as e:
        print(f"其他错误: {e}")

if __name__ == '__main__':
    test_events() 