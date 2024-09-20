import asyncio
from itertools import islice

from src.classes.s3 import S3Client
from src.config import settings

s3_client = S3Client(
    key_id=settings.YANDEX_S3_KEY_ID, secret_key=settings.YANDEX_S3_SECRET_KEY, bucket=settings.YANDEX_S3_BUCKET
)


async def print_db_dumps():
    files = await s3_client.get_list_of_files()

    for file in files.get("Contents", []):
        if file["Key"].endswith(".sql"):
            print(file["Key"])  # noqa T201


async def clear_s3_images():
    files = await s3_client.get_list_of_files()

    batch_size = 1000  # delete no more than 1000 files at once
    png_images_to_delete = [obj["Key"] for obj in files.get("Contents", []) if obj["Key"].endswith(".png")]

    for i in range(0, len(png_images_to_delete), batch_size):
        batch = list(islice(png_images_to_delete, i, i + batch_size))
        response = await s3_client.delete_multiple_files(batch)

        deleted = response.get("Deleted", [])
        errors = response.get("Errors", [])

        print(f"Deleted {len(deleted)} files")  # noqa T201
        if errors:
            print(f"Failed to delete {len(errors)} files")  # noqa T201
            for error in errors:
                print(f"Error deleting {error['Key']}: {error['Message']}")  # noqa T201


if __name__ == "__main__":
    asyncio.run(print_db_dumps())
    # asyncio.run(clear_s3_images())
