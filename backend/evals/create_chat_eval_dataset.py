import json
import os
from pathlib import Path
import sys

from langsmith import Client
from langsmith.utils import LangSmithNotFoundError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


DATASET_NAME = os.getenv("LANGSMITH_CHAT_DATASET", "skn25-chat-eval")
EXAMPLES_PATH = Path(__file__).with_name("chat_eval_examples.json")


def load_examples():
    with EXAMPLES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_or_create_dataset(client: Client, dataset_name: str):
    try:
        return client.read_dataset(dataset_name=dataset_name)
    except LangSmithNotFoundError:
        return client.create_dataset(
            dataset_name=dataset_name,
            description="SKN25 chat RAG evaluation dataset",
        )


def main():
    client = Client()
    examples = load_examples()
    dataset = get_or_create_dataset(client, DATASET_NAME)

    existing_example_ids = list(client.list_examples(dataset_id=dataset.id, limit=1))
    if existing_example_ids:
        print(f"DATASET_EXISTS {dataset.name}")
        print(f"DATASET_ID {dataset.id}")
        print("SKIP_CREATE_EXAMPLES true")
        return

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print(f"DATASET_READY {dataset.name}")
    print(f"DATASET_ID {dataset.id}")
    print(f"EXAMPLE_COUNT {len(examples)}")


if __name__ == "__main__":
    main()
