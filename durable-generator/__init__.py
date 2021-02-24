# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    config = context.get_input()
    result = yield context.call_activity('metadata-generator', config)
    return result

main = df.Orchestrator.create(orchestrator_function)