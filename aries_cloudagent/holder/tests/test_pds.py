# TODO

# holder: BaseHolder = await context.inject(BaseHolder)
#     cred_id = await holder.store_credential({}, json.loads(credential), {})
#     LOG("Credential Stored cred id %s", cred_id)
#     cred = await holder.get_credential(cred_id)
#     LOG("Credential retrieved %s", cred)

#     await holder.delete_credential(cred_id)
#     LOG("Credential Deleted", cred)
#     try:
#         cred = await holder.get_credential(cred_id)
#     except HolderError:
#         LOG("DELETING WORKS")