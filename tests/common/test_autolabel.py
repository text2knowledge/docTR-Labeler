from labeler.automation import auto_annotator


def test_autolabeler(mock_payslip):
    res = auto_annotator.predict(mock_payslip)
    assert isinstance(res, dict)
    assert "polygons" in res and "texts" in res
    assert len(res["polygons"]) == len(res["texts"]) > 0

    polygon = res["polygons"][0]
    text = res["texts"][0]

    str_pred = auto_annotator.predict_label(mock_payslip, polygon)
    assert isinstance(str_pred, str)
    assert str_pred == text

    img_shape = (1000, 2000)

    # straight boxes (bounding boxes)
    geom = [(0.1, 0.2), (0.8, 0.9)]
    result = auto_annotator._to_absolute(geom, img_shape)
    expected = [[200, 200], [1600, 200], [1600, 900], [200, 900]]
    assert result == expected

    # polygon
    geom = [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6), (0.7, 0.8)]
    result = auto_annotator._to_absolute(geom, img_shape)
    expected = [[200, 200], [600, 400], [1000, 600], [1400, 800]]
    assert result == expected
