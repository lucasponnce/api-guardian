def classify_alert_type(row):
    if row["different_endpoints"] == 1:
        return "bruteforce"
    elif row["different_endpoints"] >= row["total_requests"] * 0.8:
        return "scraping"
    else:
        return "endpoint_fuzzing"