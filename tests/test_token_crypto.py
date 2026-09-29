from unittest.mock import patch

import pytest


def test_windows_adapter_encrypts_and_decrypts_round_trip():
    """Tracer bullet: contrato real da lib (medido no dev-10 desta
    sessão) — protect(str) -> bytes, unprotect(bytes) -> str, sem
    encode/decode extra da nossa parte. O mecanismo do SO é mockado na
    fronteira (_criar_agente_dpapi); a prova contra DPAPI real é
    validação de campo, não este teste."""
    agente_fake = type(
        "AgenteFake",
        (),
        {
            "protect": lambda self, texto: b"CIFRADO:" + texto.encode("utf-8"),
            "unprotect": lambda self, blob: blob.removeprefix(b"CIFRADO:").decode("utf-8"),
        },
    )()

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=agente_fake):
        from scriba.token_crypto import AdaptadorWindowsDPAPI

        adaptador = AdaptadorWindowsDPAPI()
        cifrado = adaptador.encrypt('{"access_token": "abc"}')

        assert isinstance(cifrado, str)
        assert cifrado != '{"access_token": "abc"}'

        decifrado = adaptador.decrypt(cifrado)
        assert decifrado == '{"access_token": "abc"}'


def test_windows_adapter_calls_protect_with_the_string_directly_not_bytes():
    """Trava contra o bug real medido no dev-10: protect() recebe str
    (não bytes) — chamar com .encode() por cima estoura AttributeError
    em Windows de verdade, e um mock ingênuo não pegaria isso sem esta
    asserção sobre o argumento recebido."""
    from unittest.mock import MagicMock

    agente_mock = MagicMock()
    agente_mock.protect.return_value = b"bytes-cifrados-fake"

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=agente_mock):
        from scriba.token_crypto import AdaptadorWindowsDPAPI

        AdaptadorWindowsDPAPI().encrypt('{"access_token": "abc"}')

    agente_mock.protect.assert_called_once_with('{"access_token": "abc"}')


def test_windows_adapter_raises_formato_antigo_for_plaintext_json():
    from scriba.token_crypto import AdaptadorWindowsDPAPI, TokenFormatoAntigoError

    with patch("scriba.token_crypto._criar_agente_dpapi"):
        adaptador = AdaptadorWindowsDPAPI()

        with pytest.raises(TokenFormatoAntigoError):
            adaptador.decrypt('{"access_token": "token-antigo-em-claro"}')


def test_windows_adapter_raises_cofre_indisponivel_when_dpapi_fails():
    import base64
    from unittest.mock import MagicMock

    from scriba.token_crypto import AdaptadorWindowsDPAPI, CofreIndisponivelError

    agente_mock = MagicMock()
    agente_mock.unprotect.side_effect = OSError("DPAPI recusou o blob")

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=agente_mock):
        adaptador = AdaptadorWindowsDPAPI()
        cifrado_valido = base64.b64encode(b"blob-qualquer").decode("ascii")

        with pytest.raises(CofreIndisponivelError):
            adaptador.decrypt(cifrado_valido)
