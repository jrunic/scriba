from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.is_authenticated = True
    return account


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.subject = "Assunto de teste"
    msg.sender = "remetente@example.com"
    msg.to = ["destinatario@example.com"]
    msg.cc = []
    msg.body = "Corpo em texto simples."
    msg.is_read = False
    msg.importance = "normal"
    msg.has_attachments = False
    msg.object_id = "msg-id-123"
    msg.received = None
    return msg


@pytest.fixture
def mock_calendar():
    cal = MagicMock()
    cal.name = "Calendário"
    cal.calendar_id = "cal-id-default"
    return cal


@pytest.fixture
def mock_calendar_secondary():
    cal = MagicMock()
    cal.name = "Trabalho"
    cal.calendar_id = "cal-id-trabalho"
    return cal


@pytest.fixture
def mock_event():
    ev = MagicMock()
    ev.subject = "Reunião de teste"
    ev.start = None
    ev.end = None
    ev.location = {
        "displayName": "Sala 1",
        "locationType": "default",
        "uniqueId": "Sala 1",
        "uniqueIdType": "private",
    }
    ev.body = "Pauta da reunião."
    ev.object_id = "event-id-456"
    ev.is_all_day = False
    ev.recurrence = None
    ev.attendees = []
    ev.organizer = None
    return ev


@pytest.fixture(autouse=True)
def _sem_adaptador_de_criptografia_por_padrao(monkeypatch):
    """Todo teste, por padrão, vê cryptography_manager=None (o
    comportamento da Fase 1) — nenhum teste toca o Keychain/DPAPI real
    sem pedir explicitamente. Um teste que precisa do adaptador de
    verdade (mockado na fronteira do SO) sobrescreve com
    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", ...)
    dentro do próprio corpo — o monkeypatch é compartilhado por task e
    função de teste, então a sobrescrita local vence até o teardown."""
    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", lambda servico: None)
