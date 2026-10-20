import os
import uuid
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_image(file_storage, upload_folder, allowed_extensions):
    """
    Saves an uploaded image to disk with a unique filename to avoid collisions.
    Returns the relative path (e.g. 'products/abc123.jpg') to store in the DB,
    or None if no valid file was provided.
    """
    if not file_storage or file_storage.filename == '':
        return None

    if not allowed_file(file_storage.filename, allowed_extensions):
        return None

    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'
    safe_name = secure_filename(unique_name)

    filepath = os.path.join(upload_folder, safe_name)
    file_storage.save(filepath)

    # Return path relative to the 'images/' folder, matching how
    # image_url is used elsewhere (e.g. 'products/abc123.jpg')
    folder_name = os.path.basename(upload_folder)
    return f'{folder_name}/{safe_name}'