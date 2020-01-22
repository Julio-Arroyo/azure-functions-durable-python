from typing import List, Any

from ..models.Task import (
    Task)
from ..models.actions.CallActivityAction import CallActivityAction
from ..models.history import HistoryEvent
from .task_utilities import find_task_completed, find_task_failed, \
    find_task_scheduled, set_processed, parse_history_event


def call_activity_task(
        state: List[HistoryEvent],
        name: str,
        input_: Any = None) -> Task:
    """Determine the state of Scheduling an activity for execution.

    :param state: The list of history events to search to determine the current
    state of the activity.
    :param name: The name of the activity function to schedule.
    :param input_:The JSON-serializable input to pass to the activity
    function.
    :return: A Durable Task that completes when the called activity
    function completes or fails.
    """
    new_action = CallActivityAction(name, input_)

    task_scheduled = find_task_scheduled(state, name)
    task_completed = find_task_completed(state, task_scheduled)
    task_failed = find_task_failed(state, task_scheduled)
    set_processed([task_scheduled, task_completed, task_failed])

    if task_completed is not None:
        return Task(
            is_completed=True,
            is_faulted=False,
            action=new_action,
            result=parse_history_event(task_completed),
            timestamp=task_completed["Timestamp"],
            id_=task_completed["TaskScheduledId"])

    if task_failed is not None:
        return Task(
            is_completed=True,
            is_faulted=True,
            action=new_action,
            result=task_failed["Reason"],
            timestamp=task_failed["Timestamp"],
            id_=task_failed["TaskScheduledId"],
            exc=Exception(
                f"{task_failed['Reason']} \n {task_failed['Details']}")
        )

    return Task(is_completed=False, is_faulted=False, action=new_action)