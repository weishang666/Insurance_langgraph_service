import requests

exception_classes = [
    cls for cls in dir(requests.exceptions)
    if isinstance(getattr(requests.exceptions, cls), type)
    and issubclass(getattr(requests.exceptions, cls), Exception)
]

print("Available exceptions in requests.exceptions:")
for exception in exception_classes:
    print(f"- {exception}")

# Check if RemoteDisconnected is available
if hasattr(requests.exceptions, 'RemoteDisconnected'):
    print("\nRemoteDisconnected is available in requests.exceptions.")
else:
    print("\nRemoteDisconnected is NOT available in requests.exceptions.")
    # Suggest alternative approach
    print("\nAlternative approach for handling connection reset errors:")
    print("You can catch requests.exceptions.ConnectionError and check the underlying cause.")