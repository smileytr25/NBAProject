from typing import Protocol 
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv 
from hoophub.utils.constants import DATABASE_NAME, PAGE_CACHE_COLLECTION
import gzip 
import boto3 
import hashlib 
from botocore.exceptions import ClientError 

load_dotenv() 

class CacheBackend(Protocol):
    def get(self, url: str) -> str | None: ... 
    def save(self, url: str, html: str) -> None: ...
    def delete(self, url: str) -> None: ...

class MongoCacheBackend:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
        self.database = self.client[DATABASE_NAME]
        self.collection = self._initialize_collection()

    def _initialize_collection(self):
        if PAGE_CACHE_COLLECTION not in self.database.list_collection_names():
            self.database.create_collection(PAGE_CACHE_COLLECTION)

        collection = self.database[PAGE_CACHE_COLLECTION]
        collection.create_index("url", unique=True)

        return collection 

    def _compress(self, html: str) -> bytes:
        return gzip.compress(html.encode("utf-8"))

    def _decompress(self, data: bytes):
        return gzip.decompress(data).decode("utf-8")
    
    def get(self, url: str) -> str | None:
        document = self.collection.find_one(
            {"url": url},
            {"_id": 0, "html": 1}
        )

        if document is None:
            return None 

        return self._decompress(document["html"])

    def save(self, url: str, html: str) -> None:
        self.collection.update_one(
            {"url": url},
            {
                "$set": {
                    "url" : url,
                    "html": self._compress(html)
                }
            },
            upsert=True
        )

    def delete(self, url: str) -> None:
        self.collection.delete_one({"url": url})

class R2CacheBackend:
    def __init__(self):
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        self.client = boto3.client(
            "s3",
            endpoint_url = os.getenv("R2_ENDPOINT_URL"),
            aws_access_key_id = os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto"
        )

    def _key(self, url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"pages/{digest}.html.gz"

    def _compress(self, html: str) -> bytes:
        return gzip.compress(html.encode("utf-8"))

    def _decompress(self, data: bytes) -> str:
        return gzip.decompress(data).decode("utf-8")

    def get(self, url: str) -> str | None:
        try:
            response = self.client.get_object(
                Bucket = self.bucket_name,
                Key = self._key(url)
            )
        except ClientError as error:
            code = error.response["Error"]["Code"]

            if code in {"NoSuchKey", "404"}:
                return None 

            raise 

        compressed_html = response["Body"].read()
        return self._decompress(compressed_html)

    def save(self, url: str, html: str) -> None:
        compressed_html = self._compress(html)

        self.client.put_object(
            Bucket = self.bucket_name,
            Key = self._key(url),
            Body = compressed_html,
            ContentType = "text/html",
            ContentEncoding = "gzip",
            Metadata = {
                "source-url": url,
            },
        )

    def delete(self, url: str) -> None:
        self.client.delete_object(
            Bucket = self.bucket_name,
            Key = self._key(url),
        )

class Cache:
    def __init__(self, backend : CacheBackend):
        self._backend = backend

    def get(self, url: str) -> str | None:
        return self._backend.get(url)

    def save(self, url: str, html: str) -> None:
        return self._backend.save(url, html)

    def delete(self, url: str) -> None:
        self._backend.delete(url)



