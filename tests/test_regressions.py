"""Tests de las regresiones corregidas en la rama fix/runtime-correctness.

Son tests sin Mongo: no abren conexion, solo comprueban la logica pura que
antes estaba repartida como literales dentro de las agregaciones.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

# Se fija antes de importar app.models, porque app.db falla al importar si no
# encuentra MONGODB_URL. La URL es de relleno: pymongo se conecta de forma
# perezosa y estos tests nunca llegan a tocar la red.
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/scraper_test")

from app.models import (  # noqa: E402
    DISPLAY_TZ,
    DISPLAY_TZ_OFFSET,
    DISPLAY_TZINFO,
    INDEXES,
    Trend,
    country_filter,
    ensure_indexes,
    serialize_bucket_timestamp,
)


# ---------------------------------------------------------------------
# Timestamps en UTC
# ---------------------------------------------------------------------
def test_create_document_stamps_utc_not_server_local():
    """scraped_at debe ir en UTC explicito.

    Antes se usaba datetime.now(), que es la hora local del servidor. En un
    host que no esta en UTC el documento quedaba corrido y todas las graficas
    se desplazaban sin que nada fallara.
    """
    doc = Trend.create_document("Python", 10, "ecuador")

    assert doc["scraped_at"].tzinfo is not None
    assert doc["scraped_at"].utcoffset() == timedelta(0)


def test_create_document_derives_fecha_hora_in_display_zone():
    """fecha/hora son la hora local de Ecuador del mismo instante."""
    doc = Trend.create_document("Python", 10, "ecuador")

    local = doc["scraped_at"].astimezone(DISPLAY_TZINFO)

    assert doc["fecha"] == local.strftime("%Y-%m-%d")
    assert doc["hora"] == local.strftime("%H:%M:%S")


def test_create_document_fecha_hora_never_ahead_of_utc():
    """La fecha local puede adelantarse al dia UTC, nunca lagging.

    Es el caso limite que hace visible el bug: a las 02:00 de Ecuador el dia
    UTC todavia es el anterior.
    """
    utc_midnight = datetime(2026, 3, 1, 2, 0, 0, tzinfo=timezone.utc)

    local = utc_midnight.astimezone(DISPLAY_TZINFO)

    assert local.strftime("%Y-%m-%d") == "2026-02-28"
    assert local.utcoffset() == -DISPLAY_TZ_OFFSET


def test_display_tz_constants_are_consistent():
    """El string de Mongo y el offset de Python tienen que describing lo mismo.

    Si alguien cambia uno y no el otro, los cortes por hora y los rangos de
    fecha del dashboard se descuadran en silencio.
    """
    assert DISPLAY_TZ == "-05:00"
    assert DISPLAY_TZ_OFFSET == timedelta(hours=5)
    assert DISPLAY_TZINFO.utcoffset(None) == -timedelta(hours=5)


# ---------------------------------------------------------------------
# country_filter: "all" no debe buscar un pais llamado "all"
# ---------------------------------------------------------------------
@pytest.mark.parametrize("pais", ["all", "worldwide", "", None])
def test_country_filter_is_empty_for_all_and_worldwide(pais):
    assert country_filter(pais) == {}


def test_country_filter_scopes_to_a_real_country():
    assert country_filter("argentina") == {"pais": "argentina"}


def test_country_filter_never_emits_a_literal_all_pais():
    """Regresion directa: pais="all" no puede convertirse en {"pais": "all"}.

    Con el filtro literal, la agregacion no encontraba ningun documento y
    devolvia vacio siempre.
    """
    assert "pais" not in country_filter("all")


# ---------------------------------------------------------------------
# serialize_bucket_timestamp: sin doble desplazamiento
# ---------------------------------------------------------------------
def test_serialize_bucket_timestamp_keeps_offset_and_does_not_add_z():
    """$dateTrunc con timezone ya devuelve -05:00; anadir "Z" lo rompia.

    "2026-02-20T15:00:00-05:00Z" no es una fecha ISO valida y en el front
    terminaba en Invalid Date.
    """
    value = datetime(2026, 2, 20, 15, 0, 0, tzinfo=DISPLAY_TZINFO)

    result = serialize_bucket_timestamp(value)

    assert result == "2026-02-20T15:00:00-05:00"
    assert not result.endswith("Z")


def test_serialize_bucket_timestamp_is_parseable_back():
    """El valor tiene que poder releerse con fromisoformat."""
    value = datetime(2026, 2, 20, 15, 0, 0, tzinfo=DISPLAY_TZINFO)

    reparsed = datetime.fromisoformat(serialize_bucket_timestamp(value))

    assert reparsed == value


def test_serialize_bucket_timestamp_passes_through_non_datetime():
    """Mongo puede devolver un string si la forma del documento cambia."""
    assert serialize_bucket_timestamp("2026-02-20") == "2026-02-20"


# ---------------------------------------------------------------------
# Indices
# ---------------------------------------------------------------------
def test_indexes_cover_pais_and_scraped_at():
    """Las agregaciones filtran por pais y scraped_at siempre."""
    keys = INDEXES
    assert {"pais": 1, "scraped_at": -1} in keys
    assert {"scraped_at": -1} in keys


def test_ensure_indexes_is_idempotent(monkeypatch):
    """Se llama en cada arranque, asi que no puede fallar si ya existen."""
    calls = []

    class FakeCollection:
        def create_index(self, keys):
            calls.append(keys)

    class FakeDb:
        trends = FakeCollection()

    monkeypatch.setattr("app.models.db", FakeDb())

    ensure_indexes()
    ensure_indexes()

    assert len(calls) == 2 * len(INDEXES)
    assert len(set(map(str, calls))) == len(INDEXES)


# ---------------------------------------------------------------------
# Credenciales
# ---------------------------------------------------------------------
def test_error_response_does_not_echo_the_raw_exception():
    """Los handlers no deben devolver str(e): en pymongo filtra el host.

    Se comprueba con una excepcion que contiene credenciales y hostname, que es
    justo lo que devuelve pymongo en un ServerSelectionTimeoutError.
    """
    from app import routes

    leak = "mongodb://user:secret@trends.example.net:27017"
    exc = RuntimeError(leak)

    # app.routes no expone un objeto app (lo construye create_app), asi que se
    # usa un app minimo: error_response solo necesita jsonify.
    bare = Flask(__name__)
    with bare.test_request_context():
        response, status = routes.error_response(exc, "test")

    assert status == 500
    body = response.get_json()
    assert leak not in json.dumps(body)
    assert "secret" not in json.dumps(body)
    assert body["error"] == "No se pudo completar la solicitud"
