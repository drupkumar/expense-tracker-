from app import linear_regression


def test_linear_regression_forecasts_increasing_spending():
    slope, intercept = linear_regression([100, 200, 300])
    assert slope == 100
    assert intercept == 100
    assert intercept + slope * 3 == 400


def test_linear_regression_needs_multiple_months():
    assert linear_regression([100]) == (0, 0)
