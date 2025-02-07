# managers/hook_manager.py
import logging

class HookManager:
    def __init__(self, db_session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def get_postprocess_hooks(self, task_name: str):
        """
        Retrieves postprocess hook configurations for a given task.
        """
        sql = """
        SELECT hook_type, class_path, parameters, order_index
        FROM post_process_hooks_config
        WHERE generation_task_name = :tname
        ORDER BY order_index ASC
        """
        rows = self.db_session.execute(sql, {"tname": task_name}).fetchall()
        hooks = []
        for r in rows:
            import json
            hooks.append({
                "hook_type": r['hook_type'],
                "class_path": r['class_path'],
                "parameters": json.loads(r['parameters']),
                "order_index": r['order_index']
            })
        return hooks
