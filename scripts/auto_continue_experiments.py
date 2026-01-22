#!/usr/bin/env python
"""自动监控实验进度并在完成后继续运行后续实验"""
import subprocess
import time
import sys
from pathlib import Path

def check_experiment_running():
    """检查是否有Python训练进程在运行"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True,
            text=True,
            timeout=10
        )
        count = int(result.stdout.strip())
        return count > 0
    except:
        return False

def check_log_progress(log_file="experiments/logs/qmix.log"):
    """检查日志文件，判断实验是否完成"""
    log_path = Path(log_file)
    if not log_path.exists():
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return None
            
            # 检查最后几行
            last_lines = lines[-5:]
            for line in reversed(last_lines):
                if "Training finished" in line:
                    return "finished"
                if "Training QMIX on" in line:
                    return "running"
            return "running"
    except:
        return None

def run_next_experiments():
    """运行24×24地图的所有Stage 2实验"""
    venv_python = Path('.venv') / 'Scripts' / 'python.exe'
    if not venv_python.exists():
        print("Virtual environment python not found")
        return False
    
    # 24×24 地图 (map-indices 2), 4/6 UAVs (uav-indices 0 1), 障碍密度 0.05/0.10/0.20 (obstacle-indices 1 2 3)
    cmd = [
        str(venv_python),
        "scripts/run_experiments.py",
        "--maps", "grid_extended",
        "--map-indices", "2",
        "--uav-indices", "0", "1",
        "--algorithms", "qmix_obstacle",
        "--seed", "456",
        "--obstacle-indices", "1", "2", "3"
    ]
    
    print("=" * 60)
    print("开始运行 24×24 地图的 Stage 2 实验")
    print("=" * 60)
    print(f"命令: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    """主监控循环"""
    print("开始监控实验进度...")
    print("当前实验: 16×16, 4 UAVs, 障碍密度 0.05/0.10/0.20")
    print("后续实验: 24×24, 4/6 UAVs, 障碍密度 0.05/0.10/0.20")
    print("-" * 60)
    
    check_interval = 300  # 每5分钟检查一次
    consecutive_finished = 0
    required_finished = 3  # 需要连续3次检查都显示完成才确认
    
    while True:
        is_running = check_experiment_running()
        log_status = check_log_progress()
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 进程运行: {is_running}, 日志状态: {log_status}")
        
        if not is_running and log_status == "finished":
            consecutive_finished += 1
            print(f"检测到实验可能已完成 (连续 {consecutive_finished}/{required_finished} 次)")
            
            if consecutive_finished >= required_finished:
                print("\n" + "=" * 60)
                print("确认实验已完成，开始运行后续实验...")
                print("=" * 60)
                
                if run_next_experiments():
                    print("\n后续实验已启动")
                    break
                else:
                    print("\n后续实验启动失败")
                    break
        else:
            consecutive_finished = 0
        
        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n监控已停止")
        sys.exit(0)

