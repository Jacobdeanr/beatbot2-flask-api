from models.service_type import ServiceType
from services.url_parser import UrlParser
from services.service_selector import ServiceSelector
from services.service_resolver import ServiceResolver
from services.service_processor import ServiceProcessor
from services.spotify.spotify_service import SpotifyService

class QueryParser:
    def __init__(self, resolver: ServiceResolver, service_processor: ServiceProcessor):
        self._resolver = resolver
        self._sp = service_processor

    def parse_query(self, query:str):
        service: ServiceType = self._resolver.resolve_service(query)
        return self._sp.resolve_query(service, query)
    
    def describe_items(self, obj: object) -> list[str] | None:
        desc = self._sp.describe(obj)
        if desc is None:
            return None
        return [desc] if isinstance(desc, str) else list(desc)
    
    def parse_to_payload(self, query: str, *, limit: int | None = None) -> dict:
        raw = query
        query = query.strip()

        if not query:
            return {"ok": False, "error": "empty_input"}

        service_type = self._resolver.resolve_service(query)
        obj = self._sp.resolve_query(service_type, query)
        if obj is None:
            return {"ok": False, "error": "unsupported"}

        items_full = self.describe_items(obj)
        if items_full is None:
            return {"ok": False, "error": "unsupported"}

        if limit is not None and limit > 0:
            items = items_full[:limit]
            truncated = len(items_full) > len(items)
        else:
            items = items_full
            truncated = False

        service, kind = self._sp.classify_input(obj)
        item_kind = self._sp.item_kind_for_obj(obj)

        return {
            "ok": True,
            "input": {
                "raw": raw,
                "normalized": query,
                "service": service,
                "kind": kind,
            },
            "items": [{"kind": item_kind, "value": s} for s in items],
            "count": len(items),
            "total": len(items_full),
            "truncated": truncated,
        }
    
    def resolve_item(self, *, kind: str, value: str) -> dict | None:
        kind = kind.strip()
        value = value.strip()

        if kind == "youtube_url":
            yt = self._sp.resolve_youtube_video(value)
            if yt is None:
                return None
            return self._sp.youtube_video_payload(yt)

        if kind == "search":
            yt = self._sp.resolve_youtube_search_first(value)
            if yt is None:
                return None
            return self._sp.youtube_video_payload(yt)

        raise ValueError(f"Unsupported item kind: {kind}")
    
    
def build_parser() -> QueryParser:
    parser = UrlParser()
    selector = ServiceSelector()
    spotify = SpotifyService()

    resolver = ServiceResolver(parser=parser, selector=selector)
    service_processor = ServiceProcessor(url_parser=parser, spotify=spotify)

    query_parser = QueryParser(resolver, service_processor)
    return query_parser