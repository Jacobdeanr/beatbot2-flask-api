from __future__ import annotations

import asyncio
import logging

from models.service_type import ServiceType
from services.url_parser import UrlParser
from services.service_selector import ServiceSelector
from services.service_resolver import ServiceResolver
from services.service_processor import ServiceProcessor
from services.service_playback import PlaybackQueue
from services.spotify_expansion_helper import SpotifyExpansionHelper
from services.spotify.spotify_service import SpotifyService


def _setup_logging() -> None:
    logging.getLogger("spotipy").setLevel(logging.CRITICAL)

async def sleep_or_stop(delay_s: float, stop_event: asyncio.Event) -> None:
    """
    Sleep for delay_s, but wake up immediately if stop_event is set.
    """
    stop_task = asyncio.create_task(stop_event.wait())
    sleep_task = asyncio.create_task(asyncio.sleep(delay_s))

    done, pending = await asyncio.wait(
        {stop_task, sleep_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Clean up whichever task did not finish
    for t in pending:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

async def mock_playback_loop(
    queue: PlaybackQueue,
    *,
    delay_s: float = 0.1,
    stop_event: asyncio.Event,
) -> None:
    """
    Async "player" loop.

    Runs until stop_event is set:
    1) Ask the queue for the next playable YouTube item
    2) If empty, sleep briefly so we do not burn CPU
    3) If found, "play" it (print placeholder) and then wait delay_s
    """
    while not stop_event.is_set():
        yt = queue.next_youtube()

        if yt is None:
            await asyncio.sleep(0.05)
            continue

        # Placeholder for actual playback
        print("Now playing:", yt.title, yt.watch_url)
        #await asyncio.sleep(delay_s)
        await sleep_or_stop(delay_s, stop_event)


async def producer_loop(
    *,
    resolver: ServiceResolver,
    service_processor: ServiceProcessor,
    queue: PlaybackQueue,
    stop_event: asyncio.Event,
) -> None:
    """
    Async producer loop.

    input() and resolve_query() are likely blocking, so we run them in a thread
    using asyncio.to_thread to keep the event loop responsive.
    """
    while not stop_event.is_set():
        user_input = await asyncio.to_thread(
            input,
            "Search for a track. Enter 'quit' to exit: ",
        )
        user_input = user_input.strip()

        if user_input.lower() == "quit":
            print("Exiting...")
            stop_event.set()
            return

        service: ServiceType = resolver.resolve_service(user_input)

        # resolve_query is likely blocking (Spotify calls, network, etc.)
        results = await asyncio.to_thread(
            service_processor.resolve_query,
            service,
            user_input,
        )

        if results is None:
            handle_empty_response()
            continue

        queue.enqueue(results)
        print("Enqueued.")


def build_app() -> tuple[ServiceResolver, ServiceProcessor, PlaybackQueue]:
    """
    Pure setup. No threads, no async needed.
    """
    _setup_logging()

    parser = UrlParser()
    selector = ServiceSelector()
    spotify = SpotifyService()

    resolver = ServiceResolver(parser=parser, selector=selector)
    service_processor = ServiceProcessor(url_parser=parser, spotify=spotify)

    expander = SpotifyExpansionHelper(spotify)
    queue = PlaybackQueue(expander)

    return resolver, service_processor, queue


def handle_empty_response() -> None:
    print("Results returned Empty")


async def main_async() -> None:
    resolver, service_processor, queue = build_app()

    stop_event = asyncio.Event()

    # Run consumer and producer concurrently in the same event loop
    consumer_task = asyncio.create_task(
        mock_playback_loop(queue, delay_s=0.0, stop_event=stop_event),
        name="consumer_loop",
    )
    producer_task = asyncio.create_task(
        producer_loop(
            resolver=resolver,
            service_processor=service_processor,
            queue=queue,
            stop_event=stop_event,
        ),
        name="producer_loop",
    )

    try:
        # Wait until the producer finishes (it sets stop_event on quit).
        await producer_task
    finally:
        # Ensure we stop the consumer too
        stop_event.set()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    print("Program finished.")


if __name__ == "__main__":
    asyncio.run(main_async())
