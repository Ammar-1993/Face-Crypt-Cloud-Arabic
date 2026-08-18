import pytest
import numpy as np
from utils.face_utils import find_best_match

def test_find_best_match():
    # Mock some 128D encodings
    encoding1 = np.array([0.1] * 128)
    encoding2 = np.array([0.5] * 128)
    encoding3 = np.array([0.9] * 128)
    
    known_list = [encoding1, encoding2, encoding3]
    
    # An unknown encoding close to encoding2
    unknown_encoding = np.array([0.51] * 128)
    
    # distance to encoding2 will be very small, well within 0.6 tolerance.
    match_idx = find_best_match(known_list, unknown_encoding, tolerance=0.6)
    assert match_idx == 1
    
    # An unknown encoding far from all
    unknown_far = np.array([5.0] * 128)
    no_match_idx = find_best_match(known_list, unknown_far, tolerance=0.6)
    assert no_match_idx is None
    
    # Empty list
    assert find_best_match([], unknown_encoding) is None

from unittest.mock import patch, MagicMock
from utils.face_utils import check_liveness

def test_check_liveness_genuine():
    image_array = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
    
    with patch('utils.face_utils.fas_session') as mock_session:
        with patch('cv2.Laplacian') as mock_lap:
            mock_lap.return_value.var.return_value = 100.0
            
            # mock output: class 1 (genuine), high probability
            mock_session.run.return_value = [[np.array([-10.0, 10.0, -10.0])]]
            
            is_live, reason = check_liveness(image_array)
            assert is_live is True
            assert reason == "نجاح"

def test_check_liveness_spoof_detected():
    image_array = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
    
    with patch('utils.face_utils.fas_session') as mock_session:
        with patch('cv2.Laplacian') as mock_lap:
            mock_lap.return_value.var.return_value = 100.0
            
            # mock output: class 0 (spoof), high probability
            mock_session.run.return_value = [[np.array([10.0, -10.0, -10.0])]]
            
            is_live, reason = check_liveness(image_array)
            assert is_live is False
            assert "احتيال" in reason
