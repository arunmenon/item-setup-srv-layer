import logging
import json
from sqlalchemy.orm import Session
from utils.dynamic_import import dynamic_import

class HookManager:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def get_hooks_for_task(self, task_name: str):
        """
        Returns a list of (hook_class, parameters_dict) for the given generation task.
        """
        sql = """
        SELECT hook_name, hook_parameters FROM postprocessing_configs
        WHERE generation_task_name = :tname
        ORDER BY id ASC
        """
        rows = self.db_session.execute(sql, {"tname": task_name}).fetchall()
        hooks = []
        for r in rows:
            params = json.loads(r['hook_parameters'])
            hook_cls = dynamic_import(r['hook_name'])
            hooks.append((hook_cls, params))
        return hooks

    def apply_hooks(self, task_name: str, response_dict):
        """
        Apply all hooks in order to the response_dict.
        Hooks can modify response_dict in place or return a new structure.

        response_dict = {task_name: {handler_name: {...}}}

        We'll iterate over each handler response and run hooks.
        """
        hooks = self.get_hooks_for_task(task_name)
        if not hooks:
            return response_dict

        self.logger.debug(f"Applying {len(hooks)} hooks for task '{task_name}'.")

        for handler_name, resp in response_dict[task_name].items():
            if resp.get('error'):
                continue
            content = resp.get('response')
            for (hook_cls, params) in hooks:
                hook_instance = hook_cls(**params)
                # Assume each hook has a method apply(value) -> str or dict
                # If the hook returns string, we update resp['response'].
                # If the hook can raise exception or do other logic handle it:
                try:
                    new_content = hook_instance.apply(content)
                    resp['response'] = new_content
                    content = new_content
                except Exception as e:
                    self.logger.error(f"Hook failed: {e}")
                    resp['error'] = str(e)
                    break

        return response_dict
