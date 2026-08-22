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
            
            # mock output: class 2 (genuine/real face), high probability
            # MiniFASNetV2 3-class mapping: 0=spoof_print, 1=spoof_video, 2=real
            mock_session.run.return_value = [[np.array([-10.0, -10.0, 10.0])]]
            
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

def test_check_liveness_active_challenge_mismatch():
    image_array_1 = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
    image_array_2 = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
    
    with patch('face_recognition.face_landmarks') as mock_landmarks:
        # Mock slightly different landmarks to pass the generic movement check, but fail the specific challenge
        landmarks1 = {
            'nose_tip': [(0, 0), (0, 0), (10, 10), (0, 0), (0, 0)],
            'chin': [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (10, 20)],
            'top_lip': [(5, 5), (0, 0), (0, 0), (5, 6), (0, 0), (0, 0), (10, 5)],
            'bottom_lip': [(5, 5), (0, 0), (0, 0), (5, 7), (0, 0), (0, 0), (10, 5)],
            'left_eye': [(5, 5)],
            'left_eyebrow': [(0, 0), (0, 0), (5, 3)]
        }
        landmarks2 = {
            'nose_tip': [(0, 0), (0, 0), (10, 11), (0, 0), (0, 0)], # slight movement to pass generic check
            'chin': [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (10, 20)],
            'top_lip': [(5, 5), (0, 0), (0, 0), (5, 6), (0, 0), (0, 0), (10, 5)], # mouth didn't change
            'bottom_lip': [(5, 5), (0, 0), (0, 0), (5, 7), (0, 0), (0, 0), (10, 5)],
            'left_eye': [(5, 5)],
            'left_eyebrow': [(0, 0), (0, 0), (5, 3)]
        }
        mock_landmarks.side_effect = [[landmarks1], [landmarks2]]
        
        # Test "smile" challenge failure
        is_live, reason = check_liveness(image_array_1, image_array_2, challenge="smile")
        assert is_live is False
        assert "الابتسامة" in reason
