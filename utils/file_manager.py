"""
File Manager Utility
Handles organized file uploads for users to Supabase Storage.

All user documents (IDs, business permits, OR/CR, driver licenses, etc.) go
to the public 'Images' bucket so they're reachable from any device — local
filesystem writes don't survive Railway redeploys and aren't visible from
mobile/CP browsers anyway. The keys we generate keep the same folder layout
we used on disk so the database paths stay readable.
"""
import os
import sys
import time
import uuid
from werkzeug.utils import secure_filename

# Make sure we can import database.db_config when this module is loaded as a
# top-level package (utils/...). Same trick the blueprints use.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Document type folders. Same names we used on local disk so existing rows
# in Supabase that point to /static/uploads/<folder>/... are still valid.
DOCUMENT_TYPES = {
    'seller': {
        'id': 'seller_ids',
        'business_permit': 'seller_permits'
    },
    'rider': {
        'orcr': 'rider_orcr',
        'driver_license': 'rider_dl'
    },
    'buyer': {
        'id': 'buyer_ids'
    }
}

# Map common file extensions to MIME types for Supabase content-type metadata.
_CONTENT_TYPE_BY_EXT = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'pdf': 'application/pdf',
}


def _content_type_for(file, filename):
    """Pick a sensible Content-Type, preferring what the browser sent."""
    if getattr(file, 'content_type', None):
        return file.content_type
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return _CONTENT_TYPE_BY_EXT.get(ext, 'application/octet-stream')


def get_user_document_path(user_type, user_id, document_type):
    """Return the storage key prefix and a 'pretty' db path for a doc.

    Kept for backward-compat with callers that just want the path conventions.
    The first value is the storage key prefix inside the Images bucket; the
    second is the legacy `/static/...` form some templates may still expect
    when joining with a filename.
    """
    if user_type not in DOCUMENT_TYPES:
        raise ValueError(f"Invalid user_type: {user_type}")
    if document_type not in DOCUMENT_TYPES[user_type]:
        raise ValueError(
            f"Invalid document_type '{document_type}' for user_type '{user_type}'"
        )

    doc_folder = DOCUMENT_TYPES[user_type][document_type]
    storage_prefix = f"static/uploads/{doc_folder}/user_{user_id}"
    legacy_db_prefix = f"/static/uploads/{doc_folder}/user_{user_id}"
    return storage_prefix, legacy_db_prefix


def save_user_document(file, user_type, user_id, document_type, original_filename=None):
    """Upload a user document to Supabase Storage.

    Returns:
        Tuple of (success, db_path, error_message). On success db_path is the
        public Supabase URL — the same shape used by profile image uploads,
        so templates that already check for `http://` / `https://` keep
        working without changes.
    """
    try:
        if not file or not file.filename:
            return False, None, "No file provided"

        if user_type not in DOCUMENT_TYPES or document_type not in DOCUMENT_TYPES[user_type]:
            return False, None, (
                f"Unsupported document_type '{document_type}' for user_type '{user_type}'"
            )

        from database.db_config import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            return False, None, "Database connection failed"

        # Build a stable, collision-resistant storage key.
        doc_folder = DOCUMENT_TYPES[user_type][document_type]
        filename = original_filename or file.filename
        secure_name = secure_filename(filename)
        timestamp = str(int(time.time() * 1000))
        unique_suffix = uuid.uuid4().hex[:8]
        final_filename = f"{document_type}_{timestamp}_{unique_suffix}_{secure_name}"
        storage_key = f"static/uploads/{doc_folder}/user_{user_id}/{final_filename}"

        # Read the upload body once. Resetting the cursor is important when
        # the same `file` was already inspected (e.g. for size checks).
        try:
            file.seek(0)
        except Exception:
            pass
        file_content = file.read()
        if not file_content:
            return False, None, "Uploaded file is empty"

        content_type = _content_type_for(file, secure_name)

        # Upload to the same public 'Images' bucket the rest of the app uses.
        supabase.storage.from_('Images').upload(
            path=storage_key,
            file=file_content,
            file_options={"content-type": content_type},
        )

        public_url = supabase.storage.from_('Images').get_public_url(storage_key)
        return True, public_url, None

    except Exception as e:
        return False, None, str(e)


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'gif', 'webp'}

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
