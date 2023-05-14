import json
from functools import partial
from http import HTTPStatus

from flask import Response

from common.debug import wdm_assert, wdm_debug_mask

jdumps = partial(json.dumps, ensure_ascii=False, indent=None, separators=(',', ':'), sort_keys=True)


def json_response(data: dict) -> Response:
    wdm_assert(isinstance(data, dict))
    try:
        resp = jdumps(data)
    except TypeError as e:
        return Response(response=wdm_debug_mask(e), status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='text/plain')
    return Response(response=resp, status=HTTPStatus.OK, mimetype='application/json')


def text_response(text: str, status: int) -> Response:
    return Response(response=text, status=status, mimetype='text/plain')


def http_200_response(payload: str = '') -> Response:
    return text_response(payload, HTTPStatus.OK)


def http_400_response(payload: str = '') -> Response:
    return text_response(payload, HTTPStatus.BAD_REQUEST)


def http_404_response(payload: str = '') -> Response:
    return text_response(payload, HTTPStatus.NOT_FOUND)


def http_500_response(payload: str = '') -> Response:
    return text_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)
