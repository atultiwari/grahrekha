from grahrekha_ml.render import render_quickdraw


def test_renders_strokes_to_a_grayscale_image_with_ink() -> None:
    strokes = [[[0, 50, 100], [0, 100, 50]]]  # one stroke: xs, ys
    image = render_quickdraw(strokes, size=64)
    assert image.size == (64, 64)
    assert image.mode == "L"
    pixels = list(image.getdata())
    assert min(pixels) == 0  # black ink on
    assert max(pixels) == 255  # white paper


def test_empty_drawing_is_blank() -> None:
    image = render_quickdraw([], size=32)
    assert set(image.getdata()) == {255}
