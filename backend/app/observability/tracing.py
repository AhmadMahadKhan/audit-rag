# ===== app/observability/tracing.py =====
"""OpenTelemetry setup — instruments FastAPI automatically; individual
services add spans via `tracer.start_as_current_span(...)` where useful."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from app.core.config import settings

def setup_tracing(app):
    resource = Resource.create({"service.name": settings.app_name, "deployment.environment": settings.ENVIROMENT})
    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_ENDPOINT:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)))

    trace.set_tracer_provider(provider)

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer(settings.app_name)