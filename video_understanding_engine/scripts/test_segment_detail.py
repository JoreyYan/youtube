#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test SegmentDetailService directly"""

import sys
import os
from pathlib import Path
import json
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.segment_detail_service import SegmentDetailService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_segment_detail():
    """Test SegmentDetailService directly"""
    data_dir = Path(__file__).parent.parent / "data" / "output_pipeline_v3"

    service = SegmentDetailService(data_dir)

    # Test with SEG_001
    segment_id = "SEG_001"
    logger.info(f"Testing segment detail for {segment_id}")

    detail = service.get_segment_detail(segment_id)

    if detail:
        logger.info(f"Successfully retrieved detail for {segment_id}")
        logger.info(f"Keys in detail: {list(detail.keys())}")

        if 'atom_level' in detail:
            logger.info(f"Atom level has {len(detail['atom_level'])} atoms")
        if 'segment_level' in detail:
            logger.info(f"Segment level keys: {list(detail['segment_level'].keys())}")
        if 'narrative_level' in detail:
            logger.info(f"Narrative level keys: {list(detail['narrative_level'].keys())}")

        # Print sample JSON
        print("\nSample output:")
        print(json.dumps(detail, ensure_ascii=False, indent=2)[:500] + "...")

    else:
        logger.error(f"Failed to retrieve detail for {segment_id}")

if __name__ == "__main__":
    test_segment_detail()