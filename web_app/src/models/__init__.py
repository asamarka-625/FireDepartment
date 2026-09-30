from web_app.src.models.base import Base
from web_app.src.models.department import Department, Section
from web_app.src.models.machinery import (Machinery, Maintenance, StatusMaintenance, STATUS_MAINTENANCE_MAP,
                                          REVERSE_STATUS_MAINTENANCE_MAP, RELOCATABLE_STATUSES, MachineryKind,
                                          MACHINERY_KIND_MAP, Relocation)
from web_app.src.models.report import Report
from web_app.src.models.user import User
