def authorized(request, token):
    expected = ("Bearer " + token).encode()
    values = []
    for line in request.split(b"\r\n")[1:]:
        key, separator, value = line.partition(b":")
        if separator and key.strip().lower() == b"authorization":
            values.append(value.strip())
    if len(values) != 1 or len(values[0]) != len(expected):
        return False
    different = 0
    for left, right in zip(values[0], expected):
        different |= left ^ right
    return different == 0


def route(request, token):
    first = request.split(b"\r\n", 1)[0].split()
    if len(first) != 3:
        return 400, None
    if not authorized(request, token):
        return 401, None
    if first[0] != b"GET":
        return 405, None
    if first[1] not in (b"/reading", b"/healthz"):
        return 404, None
    return 200, first[1]
