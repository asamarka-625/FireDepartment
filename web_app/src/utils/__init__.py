from web_app.src.utils.work_with_password import get_password_hash, verify_password
from web_app.src.utils.work_with_redis import RedisService
from web_app.src.utils.work_with_xlsx import ReportExelCreator
from web_app.src.utils.sorting import (has_adjacent_uppercase, sort_special_first, sort_machinery, is_special,
                                       machinery_sort_key)
from web_app.src.utils.machinery_rules import machinery_label, is_autotanker, today_msk


redis_service = RedisService()
creator_reports = ReportExelCreator()
