"""
原子化处理器
"""

import json
import re
from typing import List
import sys
from pathlib import Path
import hashlib

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Utterance, Atom
from utils import ClaudeClient, setup_logger

logger = setup_logger(__name__)


class Atomizer:
    """原子化处理器"""

    def __init__(self, api_key: str, batch_size: int = 50, prompt_version: str = 'v1', use_cache: bool = True, checkpoint_id: str = None):
        self.client = ClaudeClient(api_key)
        self.batch_size = batch_size
        self.total_atoms = 0
        self.prompt_version = prompt_version
        self.use_cache = use_cache
        self.checkpoint_id = checkpoint_id

        # 加载提示词
        prompt_path = Path(__file__).parent.parent / 'prompts' / f'atomize_{prompt_version}.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

        # 缓存目录
        self.cache_dir = Path(__file__).parent.parent / 'data' / 'cache'
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 断点目录
        self.checkpoint_dir = Path(__file__).parent.parent / 'data' / 'checkpoints'
        if self.checkpoint_id:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _load_checkpoint(self) -> dict | None:
        """加载断点数据"""
        if not self.checkpoint_id:
            return None

        checkpoint_file = self.checkpoint_dir / f"{self.checkpoint_id}.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    logger.info(f"加载断点: 已完成 {checkpoint['completed_batches']}/{checkpoint['total_batches']} 批次")
                    return checkpoint
            except Exception as e:
                logger.warning(f"断点加载失败: {e}")
                return None
        return None

    def _save_checkpoint(self, completed_batches: int, total_batches: int, atoms: List[Atom]):
        """保存断点数据"""
        if not self.checkpoint_id:
            return

        checkpoint_file = self.checkpoint_dir / f"{self.checkpoint_id}.json"
        try:
            checkpoint_data = {
                'checkpoint_id': self.checkpoint_id,
                'completed_batches': completed_batches,
                'total_batches': total_batches,
                'atoms_count': len(atoms),
                'atoms': [atom.to_dict() for atom in atoms]
            }
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"断点保存失败: {e}")

    def _clear_checkpoint(self):
        """清除断点文件（处理完成后）"""
        if not self.checkpoint_id:
            return

        checkpoint_file = self.checkpoint_dir / f"{self.checkpoint_id}.json"
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                logger.info("断点已清除（处理完成）")
            except Exception as e:
                logger.warning(f"断点清除失败: {e}")

    def atomize(
        self,
        utterances: List[Utterance],
        start_atom_id: int = 1
    ) -> List[Atom]:
        """
        原子化处理

        Args:
            utterances: 字幕列表
            start_atom_id: 起始原子ID

        Returns:
            原子列表
        """
        atoms = []
        total_batches = (len(utterances) + self.batch_size - 1) // self.batch_size
        atom_counter = start_atom_id
        start_batch = 0

        # 尝试加载断点
        checkpoint = self._load_checkpoint()
        if checkpoint:
            # 从断点恢复
            start_batch = checkpoint['completed_batches']
            atoms = [Atom(**atom_dict) for atom_dict in checkpoint['atoms']]
            atom_counter = start_atom_id + len(atoms)
            logger.info(f"从断点恢复，继续处理批次 {start_batch + 1}/{total_batches}")
        else:
            logger.info(f"开始原子化，共{len(utterances)}条字幕，分{total_batches}批处理")

        for i in range(start_batch * self.batch_size, len(utterances), self.batch_size):
            batch = utterances[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            logger.info(f"处理批次 {batch_num}/{total_batches}...")

            try:
                batch_atoms = self._process_batch(batch, atom_counter)
                atoms.extend(batch_atoms)
                atom_counter += len(batch_atoms)

                logger.info(f"  生成{len(batch_atoms)}个原子")

                # 保存断点
                self._save_checkpoint(batch_num, total_batches, atoms)

            except Exception as e:
                logger.error(f"  批次{batch_num}处理失败: {e}")
                # 保存当前进度作为断点
                self._save_checkpoint(batch_num - 1, total_batches, atoms)
                logger.error(f"已保存断点，可使用相同checkpoint_id重新运行从批次{batch_num}继续")
                raise  # 重新抛出异常，让调用者知道失败了

        self.total_atoms = len(atoms)
        logger.info(f"原子化完成，共生成{self.total_atoms}个原子")

        # 清除断点（成功完成）
        self._clear_checkpoint()

        return atoms

    def _get_batch_cache_key(self, batch: List[Utterance]) -> str:
        """生成batch的缓存key（基于内容hash）"""
        # 使用batch的内容生成hash
        content = ""
        for utt in batch:
            content += f"{utt.start_ms}|{utt.end_ms}|{utt.text}|"
        # 加入prompt版本，确保不同版本不会混用缓存
        content += f"|prompt={self.prompt_version}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _load_from_cache(self, cache_key: str) -> dict | None:
        """从缓存加载"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"  缓存读取失败: {e}")
                return None
        return None

    def _save_to_cache(self, cache_key: str, response: str, atoms_data: List[dict]):
        """保存到缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_data = {
                'response': response,
                'atoms_data': atoms_data
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"  缓存保存失败: {e}")

    def _process_batch(
        self,
        batch: List[Utterance],
        start_atom_id: int
    ) -> List[Atom]:
        """处理一个批次"""
        # 构建输入文本
        input_lines = []
        for utt in batch:
            input_lines.append(f"[{utt.start_time}] {utt.text}")
        input_text = "\n".join(input_lines)

        # 检查缓存
        cache_key = self._get_batch_cache_key(batch)
        cached = None
        if self.use_cache:
            cached = self._load_from_cache(cache_key)

        if cached:
            logger.info(f"  [缓存命中] 跳过API调用")
            atoms_data = cached['atoms_data']
            # 重新修正atom_id（因为start_atom_id可能变化）
            for i, atom in enumerate(atoms_data):
                atom['atom_id'] = f"A{start_atom_id + i:03d}"
        else:
            # 构建完整提示词
            prompt = self.prompt_template + "\n\n【输入】\n" + input_text + "\n\n【输出】"

            # 调用API
            response = self.client.call(prompt, max_tokens=4000)

            # 解析JSON
            atoms_data = self._parse_response(response, start_atom_id)

            # 保存到缓存
            if self.use_cache:
                self._save_to_cache(cache_key, response, atoms_data)

        # 转换为Atom对象
        atoms = []
        for data in atoms_data:
            try:
                atom = Atom(**data)
                atoms.append(atom)
            except Exception as e:
                logger.warning(f"  原子解析失败: {e}")
                continue

        return atoms

    def _parse_response(self, response: str, start_atom_id: int) -> List[dict]:
        """
        解析API响应

        尝试提取JSON数组，并修正atom_id
        """
        # 提取JSON（寻找第一个[和最后一个]）
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            raise ValueError("无法从响应中提取JSON")

        json_str = json_match.group(0)
        atoms_data = json.loads(json_str)

        # 修正atom_id（确保连续）
        for i, atom in enumerate(atoms_data):
            atom['atom_id'] = f"A{start_atom_id + i:03d}"

        return atoms_data
