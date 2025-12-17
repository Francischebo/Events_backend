import boto3
import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def allowed_file(filename):
    """Checks if a file's extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def upload_photo_to_cloud(file, folder_name=""):
    """
    Uploads a file to a cloud storage bucket (e.g., AWS S3).
    Returns the public URL of the uploaded file.
    """
    s3_bucket = current_app.config.get('CLOUD_STORAGE_BUCKET')
    if not s3_bucket:
        raise ValueError("CLOUD_STORAGE_BUCKET is not configured.")

    # Secure the filename and add a unique prefix
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}-{filename}"
    
    # Prepend folder name if provided
    s3_key = os.path.join(folder_name, unique_filename) if folder_name else unique_filename

    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
        region_name=current_app.config.get('AWS_REGION')
    )

    try:
        s3.upload_fileobj(
            file,
            s3_bucket,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read'
            }
        )
    except Exception as e:
        current_app.logger.error(f"Failed to upload to S3: {e}")
        return None

    # Construct the public URL
    return f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
