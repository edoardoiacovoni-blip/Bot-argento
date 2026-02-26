"""
Flying Wheel Engine
Esegue in sequenza i 18 controlli e restituisce il risultato complessivo.
"""
import logging

from src.flying_wheel.checks import (
    check_01, check_02, check_03, check_04, check_05,
    check_06, check_07, check_08, check_09, check_10,
    check_11, check_12, check_13, check_14, check_15,
    check_16, check_17, check_18,
)

logger = logging.getLogger(__name__)

CHECKS = [
    check_01, check_02, check_03, check_04, check_05,
    check_06, check_07, check_08, check_09, check_10,
    check_11, check_12, check_13, check_14, check_15,
    check_16, check_17, check_18,
]


def run(ctx: dict) -> bool:
    """
    Esegue tutti i 18 controlli Flying Wheel.

    :param ctx: dizionario di contesto (dati di mercato, configurazione, ecc.)
    :return: True se tutti i check passano, False altrimenti.
    """
    logger.info("FLYING WHEEL ENGINE: TAKEOFF")
    all_passed = True

    for i, check_fn in enumerate(CHECKS, start=1):
        try:
            passed, motivo = check_fn(ctx)
        except Exception as exc:
            passed = False
            motivo = f"Eccezione non gestita: {exc}"

        status = "PASS" if passed else "FAIL"
        logger.info("  [%02d/%d] %s — %s", i, len(CHECKS), status, motivo)

        if not passed:
            all_passed = False

    if all_passed:
        logger.info("FLYING WHEEL ENGINE: TUTTI I CHECK SUPERATI ✅")
    else:
        logger.warning("FLYING WHEEL ENGINE: UNO O PIÙ CHECK FALLITI ❌")

    return all_passed
