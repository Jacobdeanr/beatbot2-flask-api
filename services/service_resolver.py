from models.service_type import ServiceType
class ServiceResolver:
    def __init__(self, parser, selector):
        self._parser = parser
        self._selector = selector

    def resolve_service(self, user_input) -> ServiceType:
        domain: str | None = self._parser.get_domain(user_input)
        if domain is None:
            return ServiceType.Search
        
        service = self._selector.get_service(domain)
        return service or ServiceType.Unknown
