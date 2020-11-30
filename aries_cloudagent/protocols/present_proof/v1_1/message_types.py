"""Message types to register."""

PROTOCOL_URI = "https://didcomm.org/present-proof/1.1"
PROTOCOL_PACKAGE = "aries_cloudagent.protocols.present_proof.v1_1"

REQUEST_PROOF = f"{PROTOCOL_URI}/request-proof"
PRESENT_PROOF = f"{PROTOCOL_URI}/present-proof"

MESSAGE_TYPES = {
    REQUEST_PROOF: (f"{PROTOCOL_PACKAGE}.messages.request_proof.RequestProof"),
    PRESENT_PROOF: (f"{PROTOCOL_PACKAGE}.messages.present_proof.PresentProof"),
}
