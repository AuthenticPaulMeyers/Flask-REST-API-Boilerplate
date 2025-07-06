# upload images to the static folder
import os
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Load Supabase connection variables
SUPABASE_URL=os.getenv('SUPABASE_URL')
SUPABASE_KEY=os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# upload image function
def upload_image_to_supabase(file):

    bucket_name = 'images'
    folder_in_bucket = 'avatars'

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{extension}"

        file_path_in_bucket = f"{folder_in_bucket}/{filename}"
        file_bytes = file.read()
        res = supabase.storage.from_(bucket_name).upload(
            file_path_in_bucket,
            file_bytes,
            {'content-type': file.content_type}
        )

        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{res.fullPath}"

        return image_url
    else:
        return None


