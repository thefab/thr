#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of thr library released under the MIT license.
# See the LICENSE file for more information.

from functools import partial
import tornado
import tornadis
import toro

from thr.redis2http.limits import Limits
from thr.utils import unserialize_request_message, serialize_http_response


request_queue = toro.Queue()
redis_request_pool = tornadis.ClientPool()
redis_hash_pool = tornadis.ClientPool()


@tornado.gen.coroutine
def get_busy_workers(hash):
    with (yield redis_hash_pool.connected_client()) as redis:
        nb_workers = yield redis.call('GET', hash)
    raise tornado.gen.Return(int(nb_workers))


@tornado.gen.coroutine
def request_redis_handler(queue):
    # Needs to be rewritten : there is several redis keys to check,
    # and it must be done in an intelligent way
    # (i.e. depending on how many workers are currently free, etc)
    with (yield redis_request_pool.connected_client()) as redis:
        request = yield redis.call('BRPOP', queue, 5)
        if request:
            yield request_queue.put(request)


@tornado.gen.coroutine
def finalize_request(response_key, hashes, response):
    """
    Callback to upload the http response on redis,
    and update the workers counters for each hash
    """
    if hashes:
        pipeline = tornadis.Pipeline()
        for hash in hashes:
            pipeline.stack_call('DECR', hash)
        with (yield redis_hash_pool.connected_client()) as redis:
            yield redis.call(pipeline)
    with (yield redis_request_pool.connected_client()) as redis:
        yield redis.call('LPUSH', response_key,
                         serialize_http_response(response.result()))


@tornado.gen.coroutine
def process_request(request, hashes, body_link=None):
    """
    Update the workers counters for each hash and send the request to a worker
    """
    async_client = tornado.httpclient.AsyncHTTPClient()
    if body_link:
        body = async_client.fetch(body_link)
        # TODO : body uploaded on redis ?
    if hashes:
        pipeline = tornadis.Pipeline()
        for hash in hashes:
            pipeline.stack_call('INCR', hash)
        with (yield redis_hash_pool.connected_client()) as redis:
            yield redis.call(pipeline)
    if body_link:
        request.body = yield body
    response = yield async_client.fetch(request)
    raise tornado.gen.Return(response)


@tornado.gen.coroutine
def request_toro_handler():
    """
    Get a request for the toro queue, check the limits for each hash,
    and process the request if there is a free worker
    """
    origin_queue, serialized_request = yield request_queue.get()
    # we can avoid premature deserialization if the hash functions
    # take the serialized request as parameter ?
    request, body_link, extra_dict = \
        unserialize_request_message(serialized_request,
                                    force_host="localhost:8082")  # fix

    hashes = yield Limits.check(request)
    if hashes is None:
        # reupload the request to the bus
        with (yield redis_request_pool.connected_client()) as redis:
            # We still have the serialized request, might as well reuse it
            yield redis.call('LPUSH', origin_queue, serialized_request)
    else:
        tornado.ioloop.IOLoop.instance().add_future(
            process_request(request, hashes, body_link),
            partial(finalize_request, extra_dict["response_key"], hashes))
