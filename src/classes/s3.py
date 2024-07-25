import boto3


class S3Client:
    def __init__(self, key_id: str, secret_key: str, bucket: str):
        self.__session = boto3.Session(
            aws_access_key_id=key_id, aws_secret_access_key=secret_key, region_name="ru-central1"
        )
        self.__client = self.__session.client("s3", endpoint_url="https://storage.yandexcloud.net")
        self.__bucket = bucket

    def upload_file(self, file_path: str, image_name: str):
        self.__client.upload_file(file_path, self.__bucket, image_name)

    def make_image_public(self, image_name):
        self.__client.put_object_acl(ACL="public-read", Bucket=self.__bucket, Key=image_name)

    def get_public_url(self, image_name: str) -> str:
        return f"https://{self.__bucket}.storage.yandexcloud.net/{image_name}"

    def get_list_of_files(self):
        return self.__client.list_images(Bucket=self.__bucket)
