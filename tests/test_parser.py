from parser import infer_category, parse_receipt_text


def test_parser_extracts_phonepe_amount_and_category():
    result = parse_receipt_text("PhonePe UPI payment successful\nPaid to Swiggy\nAmount Paid: Rs. 425.00\n12/08/2025")
    assert result["amount"] == 425
    assert result["payment_method"] == "UPI"
    assert result["category"] == "Food"
    assert 0 <= result["confidence"] <= 1


def test_parser_handles_more_upi_apps():
    result = parse_receipt_text("BHIM UPI sent to Instamart\nDebited: 1,250.00")
    assert result["payment_method"] == "UPI"
    assert result["category"] == "Groceries"


def test_parser_empty_text_is_safe():
    result = parse_receipt_text("")
    assert result["amount"] == 0
    assert infer_category("") == "Other"
