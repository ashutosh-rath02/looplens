"""Universal capture via OpenTelemetry — no LoopLens code in your agent at all.

This is the "works with any framework" path. Instead of LoopLens's SDK or a
framework adapter, you point any OpenTelemetry exporter at the LoopLens server's
``/v1/traces`` endpoint. Here we use OpenInference's OpenAI auto-instrumentation,
but the same three lines of OTel setup work for OpenInference/OpenLLMetry
instrumentations of LangChain, LlamaIndex, CrewAI, AutoGen, and others — LoopLens
just ingests the spans.

Requires:
    pip install 'looplens[otel]' opentelemetry-sdk \
        opentelemetry-exporter-otlp-proto-http openinference-instrumentation-openai openai
    export OPENAI_API_KEY=sk-...

Run `looplens dev` first, then:
    PYTHONPATH=. python examples/otel_openinference_openai.py
"""

import os

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from openinference.instrumentation.openai import OpenAIInstrumentor

LOOPLENS_OTLP = os.environ.get("LOOPLENS_ENDPOINT", "http://127.0.0.1:8765") + "/v1/traces"


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY to run this example.")

    # The entire integration: send OTel spans to LoopLens, then auto-instrument.
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=LOOPLENS_OTLP)))
    trace.set_tracer_provider(provider)
    OpenAIInstrumentor().instrument(tracer_provider=provider)

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # Wrap the agent's work in a root span so it becomes one LoopLens run.
    tracer = trace.get_tracer("looplens-example")
    with tracer.start_as_current_span("research-agent"):
        for _ in range(3):  # a small loop, so the spans are interesting
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Name one AI agent observability tool."}],
            )
            print("->", resp.choices[0].message.content)

    provider.shutdown()  # flush spans to LoopLens
    print("\nDone. Open the LoopLens dashboard to inspect the OTel-sourced run.")


if __name__ == "__main__":
    main()
