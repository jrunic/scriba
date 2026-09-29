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


class _OSErrorComExitStatus(OSError):
    def __init__(self, exit_status):
        super().__init__()
        self.exit_status = exit_status


def test_macos_adapter_writes_to_keychain_and_returns_marker():
    from unittest.mock import MagicMock

    keychain_mock = MagicMock()

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        from scriba.token_crypto import AdaptadorMacOSKeychain

        adaptador = AdaptadorMacOSKeychain(servico="scriba-teste-servico")
        marcador = adaptador.encrypt('{"access_token": "abc"}')

    keychain_mock.set_generic_password.assert_called_once_with(
        "scriba-teste-servico", "token", '{"access_token": "abc"}'
    )
    assert marcador  # marcador não vazio, mas nunca o segredo
    assert "access_token" not in marcador


def test_macos_adapter_reads_from_keychain_ignoring_file_content():
    from unittest.mock import MagicMock

    keychain_mock = MagicMock()
    keychain_mock.get_generic_password.return_value = '{"access_token": "abc"}'

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        from scriba.token_crypto import AdaptadorMacOSKeychain

        adaptador = AdaptadorMacOSKeychain(servico="scriba-teste-servico")
        resultado = adaptador.decrypt("qualquer-marcador-ou-json-antigo-ignorado")

    assert resultado == '{"access_token": "abc"}'
    keychain_mock.get_generic_password.assert_called_once_with("scriba-teste-servico", "token")


def test_macos_adapter_returns_empty_string_when_keychain_item_not_found():
    """Achado medido nesta sessão (round-trip real contra o Keychain do
    macOS, fora deste teste): get_generic_password levanta um OSError
    (KeychainError na lib real) com .exit_status == -25300 quando o
    item não existe — não devolve None. Sem capturar isso, ler um token
    antigo/inexistente em macOS estouraria exceção não tratada."""
    from unittest.mock import MagicMock

    keychain_mock = MagicMock()
    keychain_mock.get_generic_password.side_effect = _OSErrorComExitStatus(-25300)

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        from scriba.token_crypto import AdaptadorMacOSKeychain

        adaptador = AdaptadorMacOSKeychain(servico="scriba-teste-servico")

        assert adaptador.decrypt("marcador-ou-json-antigo") == ""


def test_macos_adapter_raises_cofre_indisponivel_for_other_keychain_errors():
    from unittest.mock import MagicMock

    from scriba.token_crypto import AdaptadorMacOSKeychain, CofreIndisponivelError

    keychain_mock = MagicMock()
    keychain_mock.get_generic_password.side_effect = _OSErrorComExitStatus(-128)  # ACCESS_DENIED

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        adaptador = AdaptadorMacOSKeychain(servico="scriba-teste-servico")

        with pytest.raises(CofreIndisponivelError):
            adaptador.decrypt("marcador")


def test_criar_adaptador_returns_windows_adapter_on_win32(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    with patch("scriba.token_crypto._criar_agente_dpapi"):
        from scriba.token_crypto import AdaptadorWindowsDPAPI, criar_adaptador_criptografia

        adaptador = criar_adaptador_criptografia(servico="scriba-estado-fake")

    assert isinstance(adaptador, AdaptadorWindowsDPAPI)


def test_criar_adaptador_returns_macos_adapter_on_darwin(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    with patch("scriba.token_crypto._criar_keychain"):
        from scriba.token_crypto import AdaptadorMacOSKeychain, criar_adaptador_criptografia

        adaptador = criar_adaptador_criptografia(servico="scriba-estado-fake")

    assert isinstance(adaptador, AdaptadorMacOSKeychain)


def test_criar_adaptador_returns_none_on_linux(monkeypatch):
    """Linux fica fora de escopo desta fase — a fábrica devolve None, e
    quem chama não atribui cryptography_manager nenhum, preservando o
    comportamento da Fase 1 (só permissão de arquivo)."""
    monkeypatch.setattr("sys.platform", "linux")
    from scriba.token_crypto import criar_adaptador_criptografia

    assert criar_adaptador_criptografia(servico="scriba-estado-fake") is None


def test_nome_servico_keychain_e_derivado_do_diretorio_de_estado():
    """Nome de serviço num único lugar — auth.py e auth_cmd.py
    consomem esta função, não escrevem o f-string cada um por sua
    conta (achado dev-10: duas cópias divergiriam em silêncio)."""
    from scriba.token_crypto import nome_servico_keychain

    assert nome_servico_keychain("/home/user/.local/state/scriba") == (
        "scriba:/home/user/.local/state/scriba"
    )
