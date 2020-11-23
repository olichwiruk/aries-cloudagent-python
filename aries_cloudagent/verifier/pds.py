"""Base Verifier class."""

from .base import BaseVerifier
from aries_cloudagent.aathcf.credentials import (
    PresentationRequestSchema,
    PresentationSchema,
    validate_schema,
)
from ..aathcf.credentials import verify_proof
import logging


class PDSVerifier(BaseVerifier):
    """PDS class for verifier."""

    def __init__(self, wallet):
        self.logger = logging.getLogger(__name__)
        self.wallet: InjectionContext = wallet

    async def verify_presentation(
        self,
        presentation_request,
        presentation,
        schemas={},
        credential_definitions={},
        rev_reg_defs={},
        rev_reg_entries={},
    ):
        """
        Verify a presentation.

        Args:
            presentation_request: Presentation request data
            presentation: Presentation data
            schemas: Schema data
            credential_definitions: credential definition data
            rev_reg_defs: revocation registry definitions
            rev_reg_entries: revocation registry entries
        """
        self.logger.info(
            f"""verify_presentation input
        presentation_request {presentation_request}
        presentation         {presentation}"""
        )
        errors1 = validate_schema(
            PresentationRequestSchema, presentation_request, self.logger.error
        )
        errors2 = validate_schema(PresentationSchema, presentation, self.logger.error)
        if errors1 or errors2:
            self.logger.warning(
                f"""validate_schema errors: 
                presentation_request: {errors1} 
                presentation:         {errors2}"""
            )
            return False

        proofVerified = await verify_proof(self.wallet, presentation)
        if proofVerified == False:
            self.logger.warning("verify_proof presentation proof: %s", proofVerified)
            return False

        for subcredential in presentation.get("verifiableCredential"):
            subProofVerified = await verify_proof(self.wallet, subcredential)
            if subProofVerified == False:
                self.logger.warning("verify_proof subproof: %s", subProofVerified)
                return False

        return True
