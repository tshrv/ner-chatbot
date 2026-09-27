import json

from gliner import GLiNER
from loguru import logger


def ner(text: str, labels: list[str]):
    model = GLiNER.from_pretrained("knowledgator/gliner-multitask-large-v0.5")
    entities = model.predict_entities(text, labels)
    # {'start': 41, 'end': 51, 'text': 'Paul Allen', 'label': 'founder', 'score': 0.9928334951400757}
    for entity in entities:
        logger.info(f"{entity['text']} => {entity['label']}")
    return entities


def main():
    uid = "1790425565"
    logger.info(f"Processing uid {uid}")
    out_file_path = f"/home/tushar/ner-chatbot/data/responses/ner/{uid}.json"
    content_file_path = f"/home/tushar/ner-chatbot/data/responses/extraction/{uid}.json"
    labels = [
        "founder",
        "computer",
        "software",
        "position",
        "date",
        "person",
        "country",
        "situation",
    ]
    all_entities = []
    with open(content_file_path, "r") as f:
        data = json.load(f)
        ln_results = len(data["results"])
        logger.info(f"Content contains {ln_results} result(s)")
        for i, result in enumerate(data["results"]):
            logger.info(f"Processing {i + 1}/{ln_results} result")
            content = result["content"]
            entities = ner(content, labels)
            all_entities.extend(entities)
    logger.info("Processing complete")
    with open(out_file_path, "w") as f:
        json.dump(all_entities, f)
        logger.info(f"NER response written to {out_file_path}")


if __name__ == "__main__":
    main()
