import re


def detect_agreement(query, collection):

    query_lower = query.lower()

    all_data = collection.get(
        include=["metadatas"]
    )

    pdf_names = set()

    for meta in all_data["metadatas"]:

        pdf_names.add(
            meta["pdf_name"]
        )

    best_match = None
    best_score = 0

    query_words = set(
        re.findall(
            r"\w+",
            query_lower
        )
    )

    for pdf_name in pdf_names:

        pdf_words = set(
            re.findall(
                r"\w+",
                pdf_name.lower()
            )
        )

        score = len(
            query_words.intersection(
                pdf_words
            )
        )

        if score > best_score:

            best_score = score
            best_match = pdf_name

    if best_score >= 2:

        print(
            f"\nAGREEMENT DETECTED: "
            f"{best_match}"
        )

        return best_match

    return None