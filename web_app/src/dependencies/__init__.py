from web_app.src.dependencies.depends_auth import (authenticate_user, create_refresh_token, create_csrf_token,
                                                   create_access_token, get_current_user_by_access_token,
                                                   get_data_by_refresh_token, verify_csrf_token,
                                                   get_current_user_by_refresh_token, oauth2_scheme)
from web_app.src.dependencies.depends_connection import get_connection_info