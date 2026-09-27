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
def mock_event():
    ev = MagicMock()
    ev.subject = "Reunião de teste"
    ev.start = None
    ev.end = None
    ev.location = "Sala 1"
    ev.body = "Pauta da reunião."
    ev.object_id = "event-id-456"
    ev.is_all_day = False
    ev.recurrence = None
    ev.attendees = []
    ev.organizer = None
    return ev
