import os
from functools import lru_cache

from azure.cosmos import CosmosClient


@lru_cache(maxsize=1)
def _get_container():
    endpoint = os.environ["COSMOS_DB_ENDPOINT"]
    key = os.environ["COSMOS_DB_KEY"]
    database_id = os.environ["COSMOS_DB_DATABASE_ID"]
    container_id = os.environ["COSMOS_DB_MEAL_CONTAINER_ID"]

    client = CosmosClient(endpoint, credential=key)
    database = client.get_database_client(database_id)
    container = database.get_container_client(container_id)
    return container


def save_meal_log(document: dict) -> None:
    container = _get_container()
    container.upsert_item(document)
