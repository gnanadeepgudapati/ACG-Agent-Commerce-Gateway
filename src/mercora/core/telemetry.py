import sys

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from mercora.core.config import settings


def configure_tracing(service_name: str = "mercora") -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    processor: SpanProcessor
    if settings.otel_exporter_otlp_endpoint:
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        )
    else:
        # SimpleSpanProcessor exports synchronously, with no background thread -- unlike
        # BatchSpanProcessor, it can't outlive a stream (e.g. pytest's captured stderr)
        # that gets closed after the process that opened it exits.
        # stderr, not stdout: the MCP server speaks its JSON-RPC protocol over stdout,
        # so anything else writing there would corrupt the stream.
        processor = SimpleSpanProcessor(ConsoleSpanExporter(out=sys.stderr))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()


def instrument_app(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(app)
