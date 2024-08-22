from asteval import Interpreter
from loguru import logger


def safe_eval_condition(condition: str, stats: dict) -> bool:
    """Safely evaluate condition with student's stats."""
    aeval = Interpreter(
        usersyms=stats,
        use_numpy=False,
        minimal=True,
    )
    try:
        result = aeval(condition)
        logger.info(f"Condition: {condition}, result: {result}")
        if aeval.error:
            raise ValueError(f"Error while evaluating condition: {aeval.error}")
        return bool(result)
    except Exception as e:
        raise ValueError(f"Failed to evaluate condition: {str(e)}") from e
