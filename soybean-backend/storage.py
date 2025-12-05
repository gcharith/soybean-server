#%%
import os
from dotenv import load_dotenv
import boto3
from uuid import uuid4
load_dotenv()

AWS_REGION_NAME = os.getenv("AWS_REGION_NAME","us-east-1")
S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")

if S3_BUCKET is None:
    raise RuntimeError("AWS_S3_BUCKET_NAME is not set in environment")

s3_client = boto3.client("s3", region_name=AWS_REGION_NAME)

def sanitize_class_name(label:str)->str:
    return (
        label.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )
def upload_image_to_s3(
    file_bytes: bytes,
    predicted_class: str,
    extension: str,
    content_type: str | None = None,
) -> str:
    """
    Upload an image to S3 under a folder for the predicted class.

    Returns the public-style URL (will work if the bucket / objects are public),
    or can be treated as a key reference.
    """
    safe_class = sanitize_class_name(predicted_class) or "unknown"
    ext = extension if extension.startswith(".") else f".{extension}"
    key = f"{safe_class}/{uuid4().hex}{ext}"

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=file_bytes,
        **extra_args,
    )

    # Simple URL format (for a public bucket)
    url = f"https://{S3_BUCKET}.s3.{AWS_REGION_NAME}.amazonaws.com/{key}"
    return url