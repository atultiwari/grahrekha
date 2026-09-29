import numpy as np

from grahrekha_ml.eval_canonical import score_sample
from grahrekha_ml.labels import HEART, IGNORE


def test_scores_each_line_and_ignores_predictions_on_ignored_creases() -> None:
    label = np.zeros((64, 64), np.uint8)
    label[20, 5:60] = HEART
    label[40, 5:60] = IGNORE  # a minor crease: not our class, not background either
    probs = np.zeros((4, 64, 64), np.float32)
    probs[0, 21, 5:60] = 0.9  # heart, 1 px off: within tolerance
    probs[1, 40, 5:60] = 0.9  # "head" drawn on the ignored crease: no false alarm
    tallies = score_sample(probs, label, tolerance_px=3)
    heart, head = tallies["heart"], tallies["head"]
    assert heart.truth_present and heart.predicted and heart.recall > 0.9
    assert not head.truth_present and not head.predicted
    assert tallies["fate"].predicted is False
