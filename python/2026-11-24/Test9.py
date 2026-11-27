raw_scores = ["80" , "abc" , "60" , "-1"  , "101"]
scores , errors = [] , []

for raw in raw_scores:
    try:
        score = int(raw)
        if not 0 <= score <= 100:
            raise ValueError("range")
        scores.append(score)
    except ValueError:
        errors.append(raw)

passed = [score for score in scores if score >= 60]
print(passed, errors)

