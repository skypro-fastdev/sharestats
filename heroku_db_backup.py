import asyncio
import os
from datetime import datetime, timedelta

from loguru import logger

from src.classes.s3 import S3Client
from src.config import settings

s3_client = S3Client(
    key_id=settings.YANDEX_S3_KEY_ID, secret_key=settings.YANDEX_S3_SECRET_KEY, bucket=settings.YANDEX_S3_BUCKET
)


async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {stderr.decode().strip()}")

    return stdout.decode().strip()


async def create_and_upload_backup():
    try:
        # Создаем резервную копию
        logger.info("Creating database backup")
        await run_command("heroku pg:backups:capture --app sharing-stats")

        # Скачиваем резервную копию
        logger.info("Downloading backup")
        await run_command("heroku pg:backups:download --app sharing-stats")

        # Проверяем, что файл существует
        if not os.path.exists("latest.dump"):
            raise FileNotFoundError("Backup file 'latest.dump' not found")

        # Формируем имя файла резервной копии для S3
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_backup_filename = f"{current_time}_sharing-stats.dump"

        # Загружаем файл в S3
        logger.info(f"Uploading {s3_backup_filename} to S3")
        upload_success = await s3_client.upload_db_backup("latest.dump", s3_backup_filename)

        # Удаляем локальный файл
        os.remove("latest.dump")

        if upload_success:
            logger.info("Backup process completed successfully")
        else:
            logger.error("Failed to upload backup to S3")

    except RuntimeError as e:
        logger.error(f"Error executing command: {str(e)}")
    except FileNotFoundError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during backup process: {str(e)}")


async def cleanup_old_backups(days_to_keep=10):
    try:
        logger.info(f"Starting cleanup of backups older than {days_to_keep} days")
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Получаем список всех бэкапов
        s3_files = await s3_client.get_list_of_files()

        files_to_delete = []
        for obj in s3_files.get("Contents", []):
            key = obj["Key"]
            if key.startswith("db/backup/") and key.endswith("_sharing-stats.dump"):
                logger.info(f"Checking backup file: {key}")
                # Извлекаем дату из имени файла
                file_date_str = key.split("/")[-1].split("_")[0]
                file_date = datetime.strptime(file_date_str, "%Y%m%d")

                if file_date < cutoff_date:
                    files_to_delete.append(key)

        if files_to_delete:
            logger.info(f"Deleting {len(files_to_delete)} old backups")
            delete_result = await s3_client.delete_multiple_files(files_to_delete)
            if delete_result:
                logger.info("Old backups deleted successfully")
            else:
                logger.error("Failed to delete some old backups")
        else:
            logger.info("No old backups to delete")

    except Exception as e:
        logger.error(f"Error during cleanup of old backups: {str(e)}")


async def main():
    await create_and_upload_backup()
    await cleanup_old_backups()


if __name__ == "__main__":
    asyncio.run(main())
