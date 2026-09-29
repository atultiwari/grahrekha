import torch

from grahrekha_ml.losses import LineLoss, soft_cldice, soft_dice, soft_skeleton


def _line_mask(size: int = 64, broken: bool = False) -> torch.Tensor:
    m = torch.zeros(1, 1, size, size)
    m[..., 30:34, 8:56] = 1.0
    if broken:
        m[..., 30:34, 28:36] = 0.0
    return m


def test_soft_skeleton_thins_a_thick_line() -> None:
    skeleton = soft_skeleton(_line_mask(), iterations=5)
    assert skeleton.sum() < _line_mask().sum() * 0.6
    assert skeleton[..., 30:34, 20:44].sum() > 0  # still covers the line


def test_perfect_prediction_scores_one() -> None:
    target = _line_mask()
    assert soft_dice(target, target).item() > 0.99
    assert soft_cldice(target, target).item() > 0.99


def test_cldice_penalises_a_broken_prediction_more_than_dice_does() -> None:
    target = _line_mask()
    broken = _line_mask(broken=True)
    dice_drop = 1 - soft_dice(broken, target).item()
    cldice_drop = 1 - soft_cldice(broken, target).item()
    assert cldice_drop > dice_drop


def test_line_loss_ignores_ignore_pixels_and_is_finite() -> None:
    logits = torch.randn(2, 5, 32, 32, requires_grad=True)
    target = torch.randint(0, 5, (2, 32, 32))
    target[:, :4, :4] = 255
    loss = LineLoss()(logits, target)
    assert torch.isfinite(loss)
    loss.backward()
    assert logits.grad is not None


def test_line_loss_is_lower_for_the_correct_answer() -> None:
    target = torch.zeros(1, 32, 32, dtype=torch.long)
    target[0, 14:18, 4:28] = 2
    good = torch.full((1, 5, 32, 32), -8.0)
    good[:, 0] = 8.0
    good[0, 0, 14:18, 4:28] = -8.0
    good[0, 2, 14:18, 4:28] = 8.0
    bad = torch.zeros(1, 5, 32, 32)
    loss = LineLoss()
    assert loss(good, target) < loss(bad, target)
