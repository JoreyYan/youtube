# -*- coding: utf-8 -*-
"""FastAPI Server - Backend API for Frontend"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import analysis services
from api.analysis_service import AnalysisService
# Force reload of incremental analysis service (2024-10-04 fix)
import importlib
import api.incremental_analysis_service
importlib.reload(api.incremental_analysis_service)
from api.incremental_analysis_service import IncrementalAnalysisService
from api.segment_manager import SegmentManager
from api.segment_detail_service import SegmentDetailService

app = FastAPI(title="Video Understanding API", version="1.0.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory path
DATA_DIR = Path(__file__).parent.parent / "data" / "output_pipeline_v3"

# Get API key from config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CLAUDE_API_KEY

# Initialize analysis services (singletons)
analysis_service = AnalysisService(DATA_DIR)
incremental_service = IncrementalAnalysisService(DATA_DIR, CLAUDE_API_KEY)
segment_manager = SegmentManager(DATA_DIR, segment_duration_minutes=20)
segment_detail_service = SegmentDetailService(DATA_DIR)

# Helper function to read JSON file
def read_json_file(filename: str):
    """Read JSON file from data directory"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper function to read JSONL file
def read_jsonl_file(filename: str):
    """Read JSONL file from data directory"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Video Understanding API",
        "version": "1.0.0",
        "endpoints": {
            "atoms": "/api/projects/{project_id}/atoms",
            "segments": "/api/projects/{project_id}/segments",
            "entities": "/api/projects/{project_id}/entities",
            "topics": "/api/projects/{project_id}/topics",
            "graph": "/api/projects/{project_id}/graph",
            "creative": "/api/projects/{project_id}/creative",
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "data_dir": str(DATA_DIR)}

# ==================== Data Endpoints ====================

@app.get("/api/projects/{project_id}/atoms")
async def get_atoms(project_id: str):
    """Get all atoms"""
    try:
        atoms = read_jsonl_file("atoms.jsonl")
        logger.info(f"Loaded {len(atoms)} atoms")
        return {"atoms": atoms, "count": len(atoms)}
    except Exception as e:
        logger.error(f"Error loading atoms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/segments")
async def get_segments(project_id: str):
    """Get all narrative segments"""
    try:
        segments = read_json_file("narrative_segments.json")
        # Handle both list and dict formats
        if isinstance(segments, list):
            segment_list = segments
        else:
            segment_list = segments.get('segments', [])

        logger.info(f"Loaded {len(segment_list)} segments")
        return {"segments": segment_list, "count": len(segment_list)}
    except Exception as e:
        logger.error(f"Error loading segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/entities")
async def get_entities(project_id: str):
    """Get all entities"""
    try:
        entities_data = read_json_file("entities.json")

        # Transform entities data for frontend
        entities_list = []
        for category, entities in entities_data.items():
            if isinstance(entities, list):
                for entity in entities:
                    # Use 'atoms' field from data, rename to 'atom_ids' for frontend
                    atom_ids = entity.get("atoms", entity.get("atom_ids", []))
                    entities_list.append({
                        "name": entity.get("name", ""),
                        "type": entity.get("type", category),
                        "category": category,
                        "count": entity.get("mentions", len(atom_ids)),
                        "importance": entity.get("importance", 0.5),
                        "atom_ids": atom_ids
                    })

        logger.info(f"Loaded {len(entities_list)} entities")
        return {"entities": entities_list, "count": len(entities_list)}
    except Exception as e:
        logger.error(f"Error loading entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/topics")
async def get_topics(project_id: str):
    """Get topic network"""
    try:
        topics = read_json_file("topics.json")
        logger.info(f"Loaded topics data")
        return topics
    except Exception as e:
        logger.error(f"Error loading topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/graph")
async def get_graph(project_id: str):
    """Get knowledge graph"""
    try:
        graph_path = DATA_DIR / "knowledge_graph.json"
        if not graph_path.exists():
            raise HTTPException(status_code=404, detail="Knowledge graph not found")

        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        # Graph data is already in D3.js format with nodes/edges
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        logger.info(f"Loaded graph: {len(nodes)} nodes, {len(edges)} edges")
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
    except Exception as e:
        logger.error(f"Error loading graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/creative")
async def get_creative(project_id: str):
    """Get creative angles and clip recommendations"""
    try:
        creative = read_json_file("creative_angles.json")
        logger.info(f"Loaded creative angles data")
        return creative
    except Exception as e:
        logger.error(f"Error loading creative angles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/overview")
async def get_overview(project_id: str):
    """Get project overview with all stats"""
    try:
        atoms = read_jsonl_file("atoms.jsonl")
        segments = read_json_file("narrative_segments.json")
        entities_data = read_json_file("entities.json")

        # Count entities
        entity_count = 0
        for category, entities in entities_data.items():
            if isinstance(entities, list):
                entity_count += len(entities)

        # Load graph stats
        graph_path = DATA_DIR / "knowledge_graph.json"
        edge_count = 0
        if graph_path.exists():
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
                edge_count = len(graph_data.get('edges', []))

        segment_list = segments if isinstance(segments, list) else segments.get('segments', [])

        return {
            "project_id": project_id,
            "stats": {
                "atoms": len(atoms),
                "segments": len(segment_list),
                "entities": entity_count,
                "relations": edge_count
            }
        }
    except Exception as e:
        logger.error(f"Error loading overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/report")
async def get_report(project_id: str):
    """Get video structure report (Markdown)"""
    try:
        report_path = DATA_DIR / "video_structure.md"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content)
    except Exception as e:
        logger.error(f"Error loading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analysis Endpoints ====================

@app.post("/api/projects/{project_id}/analyze/full")
async def start_full_analysis(project_id: str, chunk_size: int = 50):
    """Start full video analysis (legacy - use incremental instead)"""
    try:
        analysis_service.start_full_analysis(project_id, chunk_size)
        return {
            "status": "started",
            "message": "Full video analysis started",
            "project_id": project_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/analyze/status")
async def get_analysis_status(project_id: str):
    """Get analysis progress (legacy)"""
    try:
        progress = analysis_service.get_progress()
        return progress
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze/cancel")
async def cancel_analysis(project_id: str):
    """Cancel running analysis (legacy)"""
    try:
        analysis_service.cancel_analysis()
        return {
            "status": "cancelled",
            "message": "Analysis cancelled",
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error cancelling analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Incremental Analysis Endpoints ====================

@app.post("/api/projects/{project_id}/analyze/incremental/start")
async def start_incremental_analysis(project_id: str):
    """Start incremental segment-by-segment analysis"""
    try:
        incremental_service.start_incremental_analysis(project_id)
        return {
            "status": "started",
            "message": "Incremental analysis started",
            "project_id": project_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting incremental analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze/incremental/stop")
async def stop_incremental_analysis(project_id: str):
    """Stop incremental analysis"""
    try:
        incremental_service.stop_analysis()
        return {
            "status": "stopped",
            "message": "Incremental analysis stopped",
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error stopping incremental analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/analyze/incremental/progress")
async def get_incremental_progress(project_id: str):
    """Get incremental analysis progress with segment details"""
    try:
        progress = incremental_service.get_progress()
        return progress
    except Exception as e:
        logger.error(f"Error getting incremental progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/segments")
async def get_segments(project_id: str):
    """Get all time segments with their status"""
    try:
        segments = segment_manager.load_segments_state()
        return {
            "segments": [
                {
                    "segment_id": seg.segment_id,
                    "start_time": seg.start_time_str,
                    "end_time": seg.end_time_str,
                    "duration_ms": seg.duration_ms,
                    "atom_count": len(seg.atom_ids),
                    "status": seg.status,
                    "atomization_complete": seg.atomization_complete,
                    "analysis_complete": seg.analysis_complete,
                    "entity_count": seg.entity_count,
                    "error_message": seg.error_message
                }
                for seg in segments
            ],
            "total_segments": len(segments)
        }
    except Exception as e:
        logger.error(f"Error getting segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze/incremental/reset")
async def reset_incremental_analysis(project_id: str):
    """Reset analysis status (keep atomization)"""
    try:
        segment_manager.reset_analysis()
        return {
            "status": "reset",
            "message": "Analysis status reset, atomization preserved",
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error resetting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze/segment/{segment_id}")
async def analyze_single_segment(project_id: str, segment_id: str):
    """Analyze a single specific segment"""
    try:
        incremental_service.analyze_single_segment(project_id, segment_id)
        return {
            "status": "started",
            "message": f"Analysis started for segment {segment_id}",
            "project_id": project_id,
            "segment_id": segment_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/segments/recreate")
async def recreate_segments(project_id: str, segment_duration_minutes: int = 20):
    """Recreate segments with new duration"""
    try:
        segments = segment_manager.recreate_segments(segment_duration_minutes)
        return {
            "status": "recreated",
            "message": f"Segments recreated with {segment_duration_minutes} minute duration",
            "total_segments": len(segments),
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error recreating segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/segments/{segment_id}/reset")
async def reset_segment_analysis(project_id: str, segment_id: str):
    """Reset analysis status for a specific segment"""
    try:
        segment_manager.reset_segment_analysis(segment_id)
        return {
            "status": "reset",
            "message": f"Analysis reset for segment {segment_id}",
            "project_id": project_id,
            "segment_id": segment_id
        }
    except Exception as e:
        logger.error(f"Error resetting segment {segment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze/global")
async def start_global_analysis(project_id: str):
    """Start global analysis - analyze entire video without segmentation"""
    try:
        from pathlib import Path
        import json
        from tqdm import tqdm
        from video_understanding_engine.analyzers.entity_extractor import EntityExtractor
        from video_understanding_engine.analyzers.topic_network_builder import TopicNetworkBuilder
        from video_understanding_engine.analyzers.knowledge_graph_builder import KnowledgeGraphBuilder

        logger.info(f"Starting global analysis for project {project_id}")

        # Load all atoms
        atoms_path = Path("D:/code/youtube/video_understanding_engine/data/output/atoms_full.jsonl")
        if not atoms_path.exists():
            raise HTTPException(status_code=404, detail="Atoms file not found. Please run atomization first.")

        atoms = []
        with open(atoms_path, 'r', encoding='utf-8') as f:
            for line in f:
                atoms.append(json.loads(line.strip()))

        logger.info(f"Loaded {len(atoms)} atoms for global analysis")

        # Create mock segment for entity extraction
        def create_mock_segment(atoms_data, segment_id="GLOBAL"):
            class MockAtom:
                def __init__(self, data):
                    self.atom_id = data['atom_id']
                    self.merged_text = data['merged_text']
                    self.start_ms = data.get('start_ms', 0)
                    self.end_ms = data.get('end_ms', 0)

            class MockEntities:
                def __init__(self):
                    self.persons = []
                    self.countries = []
                    self.organizations = []
                    self.time_points = []
                    self.events = []
                    self.concepts = []

            class MockNarrative:
                def __init__(self):
                    self.primary_topic = "全局视频分析"
                    self.secondary_topics = []
                    self.tags = []

            class MockSegment:
                def __init__(self, atoms_data, seg_id):
                    self.segment_id = seg_id
                    self.atoms = [MockAtom(a) for a in atoms_data]
                    self.entities = MockEntities()
                    self.narrative_arc = MockNarrative()
                    self.full_text = " ".join([a['merged_text'] for a in atoms_data])

            return MockSegment(atoms_data, segment_id)

        # Process in chunks to avoid token limits
        chunk_size = 50
        segments = []

        for i in range(0, len(atoms), chunk_size):
            chunk = atoms[i:i+chunk_size]
            seg_id = f"GLOBAL_{i//chunk_size + 1:03d}"
            segments.append(create_mock_segment(chunk, seg_id))

        # Extract entities globally
        logger.info("Extracting entities globally...")
        extractor = EntityExtractor()

        all_entities = {
            'persons': {},
            'countries': {},
            'organizations': {},
            'time_points': {},
            'events': {},
            'concepts': {}
        }

        for seg in segments:
            result = extractor.extract([seg])

            # Merge results
            for entity_type in all_entities.keys():
                for entity in result.get(entity_type, []):
                    name = entity['name']
                    if name not in all_entities[entity_type]:
                        all_entities[entity_type][name] = entity
                    else:
                        # Merge atoms and segments
                        existing = all_entities[entity_type][name]
                        existing['mentions'] += entity.get('mentions', 1)
                        existing['atoms'] = list(set(existing.get('atoms', []) + entity.get('atoms', [])))
                        existing['segments'] = list(set(existing.get('segments', []) + entity.get('segments', [])))

        # Convert back to lists
        final_entities = {}
        for entity_type, entities_dict in all_entities.items():
            final_entities[entity_type] = list(entities_dict.values())

        # Calculate statistics
        final_entities['statistics'] = {
            'total_entities': sum(len(entities) for entities in final_entities.values() if isinstance(entities, list)),
            'by_type': {k: len(v) for k, v in final_entities.items() if isinstance(v, list)}
        }

        # Save entities
        output_dir = Path("D:/code/youtube/video_understanding_engine/data/output_pipeline_v3")
        output_dir.mkdir(parents=True, exist_ok=True)

        entities_file = output_dir / "entities.json"
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(final_entities, f, ensure_ascii=False, indent=2)

        # Update frontend data directories
        frontend_paths = [
            Path("D:/code/youtube/atom-viewer/public/data/output_pipeline_v3/overview.json"),
            Path("D:/code/youtube/atom-viewer/public/data/project_001/overview.json")
        ]

        # Create overview data
        overview_data = {
            "atoms": atoms,
            "total_atoms": len(atoms),
            "analysis_type": "global",
            "timestamp": str(datetime.now()),
            "project_id": project_id,
            "entities": final_entities
        }

        # Update both frontend directories
        for frontend_path in frontend_paths:
            frontend_path.parent.mkdir(parents=True, exist_ok=True)
            with open(frontend_path, 'w', encoding='utf-8') as f:
                json.dump(overview_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Global analysis completed with {len(atoms)} atoms and {final_entities['statistics']['total_entities']} entities")

        return {
            "status": "completed",
            "message": "Global analysis completed successfully",
            "project_id": project_id,
            "total_atoms": len(atoms),
            "total_entities": final_entities['statistics']['total_entities'],
            "analysis_type": "global"
        }

    except Exception as e:
        logger.error(f"Error in global analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Segment Detail Endpoints ====================

@app.get("/api/projects/{project_id}/segments/{segment_id}/detail")
async def get_segment_detail(project_id: str, segment_id: str):
    """
    Get detailed three-level analysis for a specific segment

    Returns:
    - atom_level: List of atoms with topics, entities, emotions, embedding status
    - segment_level: Aggregate statistics and distributions
    - narrative_level: Narrative context if applicable
    """
    try:
        detail = segment_detail_service.get_segment_detail(segment_id)

        if not detail:
            raise HTTPException(
                status_code=404,
                detail=f"Segment detail not found for {segment_id}"
            )

        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting segment detail for {segment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/segments/summary")
async def get_segments_summary(project_id: str):
    """Get summary of all segments with analysis status"""
    try:
        summary = segment_detail_service.get_all_segments_summary()
        return {
            "segments": summary,
            "total_segments": len(summary)
        }
    except Exception as e:
        logger.error(f"Error getting segments summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/atoms/reorder")
async def reorder_atoms_by_time(project_id: str):
    """按时间重新排序所有原子ID"""
    try:
        atoms_file = DATA_DIR / "atoms.jsonl"
        if not atoms_file.exists():
            raise HTTPException(status_code=404, detail="atoms.jsonl file not found")

        # 读取所有原子
        atoms = []
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    atoms.append(json.loads(line))

        # 按start_ms排序
        atoms.sort(key=lambda x: x.get('start_ms', 0))

        # 重新分配ID并添加格式化时间字段
        def ms_to_time_str(ms):
            """Convert milliseconds to HH:MM:SS format"""
            seconds = ms // 1000
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

        reordered_atoms = []
        for i, atom in enumerate(atoms):
            new_atom = atom.copy()
            new_atom['atom_id'] = f"A{i+1:03d}"  # A001, A002, A003...

            # 添加格式化时间字段供前端显示
            start_ms = new_atom.get('start_ms', 0)
            end_ms = new_atom.get('end_ms', 0)
            duration_ms = new_atom.get('duration_ms', end_ms - start_ms)

            new_atom['start_time'] = ms_to_time_str(start_ms)
            new_atom['end_time'] = ms_to_time_str(end_ms)
            new_atom['duration_seconds'] = duration_ms / 1000.0

            reordered_atoms.append(new_atom)

        # 写回文件
        with open(atoms_file, 'w', encoding='utf-8') as f:
            for atom in reordered_atoms:
                f.write(json.dumps(atom, ensure_ascii=False) + '\n')

        # 清空相关分析数据（原子重排后必须重新分析）
        analysis_files_to_clear = [
            "entities.json",
            "topics.json",
            "knowledge_graph.json",
            "segments.pkl",
            "segments_state.json"  # 强制重新生成片段映射
        ]

        cleared_files = []
        for filename in analysis_files_to_clear:
            file_path = DATA_DIR / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                    cleared_files.append(filename)
                    logger.info(f"Cleared analysis file after reorder: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to clear {filename}: {e}")

        # 重新生成 overview.json 用于前端显示
        overview_data = {
            "atoms": reordered_atoms,
            "total_atoms": len(reordered_atoms),
            "total_duration_seconds": max(atom.get('end_ms', 0) for atom in reordered_atoms) // 1000 if reordered_atoms else 0
        }

        # 更新前端数据文件（两个目录都需要更新）
        frontend_paths = [
            Path("D:/code/youtube/atom-viewer/public/data/output_pipeline_v3/overview.json"),
            Path("D:/code/youtube/atom-viewer/public/data/project_001/overview.json")
        ]

        updated_files = []
        for frontend_overview_path in frontend_paths:
            try:
                frontend_overview_path.parent.mkdir(parents=True, exist_ok=True)
                with open(frontend_overview_path, 'w', encoding='utf-8') as f:
                    json.dump(overview_data, f, ensure_ascii=False, indent=2)
                updated_files.append(str(frontend_overview_path))
                logger.info(f"Updated {frontend_overview_path} with reordered atoms")
            except Exception as e:
                logger.warning(f"Failed to update {frontend_overview_path}: {e}")

        logger.info(f"Updated {len(updated_files)} frontend overview files")

        logger.info(f"Successfully reordered {len(reordered_atoms)} atoms by time")
        logger.info(f"Cleared {len(cleared_files)} analysis files: {cleared_files}")

        return {
            "status": "success",
            "message": f"Successfully reordered {len(reordered_atoms)} atoms by time",
            "reordered_atoms": len(reordered_atoms)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering atoms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/atoms/regenerate")
async def regenerate_atoms(project_id: str):
    """重新原子化处理字幕文件"""
    try:
        import subprocess
        import sys

        # 运行原子化处理脚本
        cmd = [sys.executable, "-m", "pipeline.video_processor_v3"]
        result = subprocess.run(cmd,
                              cwd=Path(__file__).parent.parent,
                              capture_output=True,
                              text=True,
                              timeout=300)  # 5分钟超时

        if result.returncode != 0:
            logger.error(f"Atomization failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Atomization failed: {result.stderr}")

        # 读取处理结果
        atoms_file = DATA_DIR / "atoms.jsonl"
        if not atoms_file.exists():
            raise HTTPException(status_code=404, detail="No atoms generated")

        atoms = []
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    atoms.append(json.loads(line))

        # 按时间排序并重新分配ID（使用与reorder相同的逻辑）
        atoms.sort(key=lambda x: x.get('start_ms', 0))

        def ms_to_time_str(ms):
            seconds = ms // 1000
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

        processed_atoms = []
        for i, atom in enumerate(atoms):
            new_atom = atom.copy()
            new_atom['atom_id'] = f"A{i+1:03d}"

            # 添加格式化时间字段
            start_ms = new_atom.get('start_ms', 0)
            end_ms = new_atom.get('end_ms', 0)
            duration_ms = new_atom.get('duration_ms', end_ms - start_ms)

            new_atom['start_time'] = ms_to_time_str(start_ms)
            new_atom['end_time'] = ms_to_time_str(end_ms)
            new_atom['duration_seconds'] = duration_ms / 1000.0

            processed_atoms.append(new_atom)

        # 写回后端文件
        with open(atoms_file, 'w', encoding='utf-8') as f:
            for atom in processed_atoms:
                f.write(json.dumps(atom, ensure_ascii=False) + '\n')

        # 更新前端数据
        overview_data = {
            "atoms": processed_atoms,
            "total_atoms": len(processed_atoms),
            "total_duration_seconds": max(atom.get('end_ms', 0) for atom in processed_atoms) // 1000 if processed_atoms else 0
        }

        frontend_paths = [
            Path("D:/code/youtube/atom-viewer/public/data/output_pipeline_v3/overview.json"),
            Path("D:/code/youtube/atom-viewer/public/data/project_001/overview.json")
        ]

        updated_files = []
        for frontend_overview_path in frontend_paths:
            try:
                frontend_overview_path.parent.mkdir(parents=True, exist_ok=True)
                with open(frontend_overview_path, 'w', encoding='utf-8') as f:
                    json.dump(overview_data, f, ensure_ascii=False, indent=2)
                updated_files.append(str(frontend_overview_path))
                logger.info(f"Updated {frontend_overview_path} with new atoms")
            except Exception as e:
                logger.warning(f"Failed to update {frontend_overview_path}: {e}")

        logger.info(f"Successfully regenerated {len(processed_atoms)} atoms")
        return {
            "status": "success",
            "message": f"Successfully regenerated {len(processed_atoms)} atoms",
            "generated_atoms": len(processed_atoms),
            "updated_files": len(updated_files)
        }
    except subprocess.TimeoutExpired:
        logger.error("Atomization process timed out")
        raise HTTPException(status_code=500, detail="Atomization process timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating atoms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Video Understanding API server...")
    logger.info(f"Data directory: {DATA_DIR}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
