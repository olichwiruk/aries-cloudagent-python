"""Base Verifier class."""

from .base import BaseVerifier
from aries_cloudagent.aathcf.credentials import (
    PresentationRequestSchema,
    PresentationSchema,
)
from ..holder.pds import validate_schema
from ..aathcf.credentials import verify_proof
import logging


class PDSVerifier(BaseVerifier):
    """PDS class for verifier."""

    def __init__(self, wallet):
        self.log = logging.getLogger(__name__).info
        self.wallet: InjectionContext = wallet

    async def verify_presentation(
        self,
        presentation_request,
        presentation,
        schemas,
        credential_definitions,
        rev_reg_defs,
        rev_reg_entries,
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
        self.log(
            f"""verify_presentation input
        presentation_request {presentation_request}
        presentation         {presentation}"""
        )
        errors1 = validate_schema(PresentationRequestSchema, presentation_request)
        errors2 = validate_schema(PresentationSchema, presentation)
        if errors1 != {} or errors2 != {}:
            self.log(
                f"""validate_schema errors: 
                presentation_request: {errors1} 
                presentation:         {errors2}"""
            )
            return False

        result = await verify_proof(self.wallet, presentation)

        return result
