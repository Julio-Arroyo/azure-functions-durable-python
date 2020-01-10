from .orchestrator_test_utils import *
from tests.test_utils.ContextBuilder import ContextBuilder
from azure.durable_functions.models.OrchestratorState import OrchestratorState
from azure.durable_functions.models.RetryOptions import RetryOptions
from azure.durable_functions.models.actions.CallActivityWithRetryAction import CallActivityWithRetryAction


RETRY_OPTIONS = RetryOptions(5000, 3)


def generator_function(context):
    outputs = []

    retry_options = RETRY_OPTIONS
    task1 = yield context.df.call_activity_with_retry("Hello", retry_options, "Tokyo")
    task2 = yield context.df.call_activity_with_retry("Hello",  retry_options, "Seattle")
    task3 = yield context.df.call_activity_with_retry("Hello",  retry_options, "London")

    outputs.append(task1)
    outputs.append(task2)
    outputs.append(task3)

    return outputs


def base_expected_state(output=None) -> OrchestratorState:
    return OrchestratorState(is_done=False, actions=[], output=output)


def add_hello_action(state: OrchestratorState, input_: str):
    retry_options = RETRY_OPTIONS
    action = CallActivityWithRetryAction(function_name='Hello', retry_options=retry_options, input_=input_)
    state.actions.append([action])


def add_hello_completed_events(context_builder: ContextBuilder, id_: int, result: str):
    context_builder.add_task_scheduled_event(name='Hello', id_=id_)
    context_builder.add_orchestrator_completed_event()
    context_builder.add_orchestrator_started_event()
    context_builder.add_task_completed_event(id_=id_, result=result)


def test_initial_orchestration_state():
    context_builder = ContextBuilder('test_simple_function')
    result = get_orchestration_state_result(context_builder, generator_function)
    expected_state = base_expected_state()
    add_hello_action(expected_state, 'Tokyo')
    expected = expected_state.to_json()
    assert_orchestration_state_equals(expected, result)


def test_tokyo_state():
    context_builder = ContextBuilder('test_simple_function')
    add_hello_completed_events(context_builder, 0, 'Hello Tokyo!')
    result = get_orchestration_state_result(context_builder, generator_function)
    expected_state = base_expected_state()
    add_hello_action(expected_state, 'Tokyo')
    add_hello_action(expected_state, 'Seattle')
    expected = expected_state.to_json()
    assert_orchestration_state_equals(expected, result)


def test_tokyo_and_seattle_state():
    context_builder = ContextBuilder('test_simple_function')
    add_hello_completed_events(context_builder, 0, 'Hello Tokyo!')
    add_hello_completed_events(context_builder, 1, 'Hello Seattle!')
    result = get_orchestration_state_result(context_builder, generator_function)
    expected_state = base_expected_state()
    add_hello_action(expected_state, 'Tokyo')
    add_hello_action(expected_state, 'Seattle')
    add_hello_action(expected_state, 'London')
    expected = expected_state.to_json()
    assert_orchestration_state_equals(expected, result)


def test_tokyo_and_seattle_and_london_state():
    context_builder = ContextBuilder('test_simple_function')
    add_hello_completed_events(context_builder, 0, 'Hello Tokyo!')
    add_hello_completed_events(context_builder, 1, 'Hello Seattle!')
    add_hello_completed_events(context_builder, 2, 'Hello London!')
    result = get_orchestration_state_result(context_builder, generator_function)
    expected_state = base_expected_state(['Hello Tokyo!', 'Hello Seattle!', 'Hello London!'])
    add_hello_action(expected_state, 'Tokyo')
    add_hello_action(expected_state, 'Seattle')
    add_hello_action(expected_state, 'London')
    expected_state.is_done = True
    expected = expected_state.to_json()
    assert_orchestration_state_equals(expected, result)
