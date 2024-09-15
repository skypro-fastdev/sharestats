from io import BytesIO

import aioboto3
import aiofiles
from botocore.exceptions import ClientError
from loguru import logger


class S3Client:
    def __init__(self, key_id: str, secret_key: str, bucket: str):
        self.__session = aioboto3.Session(
            aws_access_key_id=key_id, aws_secret_access_key=secret_key, region_name="ru-central1"
        )
        self.__bucket = bucket
        self.url = "https://storage.yandexcloud.net"

    def get_public_url(self, image_name: str) -> str:
        return f"https://{self.__bucket}.storage.yandexcloud.net/{image_name}"

    async def upload_file(self, file_bytes: bytes, name: str):
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            with BytesIO(file_bytes) as file_obj:
                logger.info(f"Uploading {name} to S3")
                await s3.upload_fileobj(
                    file_obj,
                    self.__bucket,
                    name,
                    ExtraArgs={
                        "ACL": "public-read",
                        "ContentType": "image/png",
                    },
                )
            return self.get_public_url(name)

    async def upload_db_backup(self, file_path: str, backup_name: str):
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            try:
                async with aiofiles.open(file_path, "rb") as file_obj:
                    await s3.upload_fileobj(
                        file_obj,
                        self.__bucket,
                        backup_name,
                        ExtraArgs={
                            "ContentType": "application/octet-stream",
                        },
                    )
                logger.info(f"Successfully uploaded {backup_name} to S3")
                return True
            except Exception as e:
                logger.error(f"Failed to upload {backup_name} to S3: {str(e)}")
                return False

    async def check_file_exists(self, name: str) -> bool:
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            try:
                await s3.head_object(Bucket=self.__bucket, Key=name)
                return True
            except ClientError:
                return False

    async def get_list_of_files(self):
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            return await s3.list_objects_v2(Bucket=self.__bucket)

    async def delete_file(self, name: str) -> bool:
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            try:
                await s3.delete_object(Bucket=self.__bucket, Key=name)
                return True
            except Exception as e:
                logger.error(f"Failed to delete file {name}: {str(e)}")
                return False

    async def delete_multiple_files(self, file_names: list[str]) -> dict:
        async with self.__session.client("s3", endpoint_url=self.url) as s3:
            objects = [{"Key": name} for name in file_names]
            try:
                return await s3.delete_objects(Bucket=self.__bucket, Delete={"Objects": objects})
            except Exception as e:
                logger.error(f"Failed to delete multiple files: {str(e)}")
                return {}
