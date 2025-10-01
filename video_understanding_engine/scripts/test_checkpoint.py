"""
测试断点续传功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import SRTParser, Cleaner
from atomizers import Atomizer
from config import CLAUDE_API_KEY
import time

def test_checkpoint():
    """测试断点续传"""
    print("\n" + "="*60)
    print("测试断点续传功能")
    print("="*60)

    if not CLAUDE_API_KEY:
        print("ERROR: 未配置CLAUDE_API_KEY")
        return

    # Step 1: 解析字幕
    print("\n[1/3] 解析SRT文件...")
    parser = SRTParser()
    utterances = parser.parse("data/raw/test.srt")
    print(f"  解析完成：{len(utterances)}条字幕")

    # Step 2: 清洗
    print("\n[2/3] 清洗字幕...")
    cleaner = Cleaner()
    utterances_clean = cleaner.clean(utterances)

    # 只取前5分钟测试（约163条）
    utterances_5min = [u for u in utterances_clean if u.start_ms < 300000]
    print(f"  测试数据：前5分钟，{len(utterances_5min)}条")

    # Step 3: 测试断点续传
    print("\n[3/3] 测试断点续传...")
    checkpoint_id = "test_checkpoint_demo"

    print("\n--- 第1次运行：处理3个batch后模拟中断 ---")
    atomizer1 = Atomizer(CLAUDE_API_KEY, batch_size=50, checkpoint_id=checkpoint_id)

    # 手动处理前3个batch，然后模拟中断
    try:
        total_batches = (len(utterances_5min) + 49) // 50
        atoms = []
        atom_counter = 1

        for i in range(0, min(150, len(utterances_5min)), 50):  # 只处理前3批
            batch = utterances_5min[i:i + 50]
            batch_num = i // 50 + 1

            print(f"处理批次 {batch_num}/{total_batches}...")
            batch_atoms = atomizer1._process_batch(batch, atom_counter)
            atoms.extend(batch_atoms)
            atom_counter += len(batch_atoms)
            print(f"  生成{len(batch_atoms)}个原子")

            # 保存断点
            atomizer1._save_checkpoint(batch_num, total_batches, atoms)

        print(f"\n模拟中断：已处理3批，共{len(atoms)}个原子")

    except Exception as e:
        print(f"处理失败: {e}")

    # 模拟一段时间后重新运行
    print("\n--- 第2次运行：从断点恢复 ---")
    time.sleep(1)

    atomizer2 = Atomizer(CLAUDE_API_KEY, batch_size=50, checkpoint_id=checkpoint_id)
    atoms_final = atomizer2.atomize(utterances_5min)

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print(f"最终原子数: {len(atoms_final)}个")
    print(f"断点文件已自动清除")
    print("="*60)

if __name__ == "__main__":
    test_checkpoint()
