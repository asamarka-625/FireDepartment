from web_app.src.admin.department import DepartmentAdmin
from web_app.src.admin.section import SectionAdmin
from web_app.src.admin.machinery import MachineryAdmin
from web_app.src.admin.maintenance import MaintenanceAdmin
from web_app.src.admin.user import UserAdmin
from web_app.src.admin.authentication import BasicAuthBackend
from web_app.src.core import cfg


authentication_backend = BasicAuthBackend(secret_key=cfg.SECRET_REFRESH_KEY)