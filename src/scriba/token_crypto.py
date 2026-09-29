"""Adaptadores de criptografia do arquivo de token, por sistema
operacional — achado F1 da auditoria de segurança externa (29/09/2026),
Fase 2 (jd-task #1077). Cada adaptador expõe encrypt(str)/decrypt(str),
o Protocol que BaseTokenBackend.cryptography_manager (lib O365) espera.
ADR local: docs/decisoes/20260929-cofre-do-so-para-token-via-msal-extensions.md.

Nenhum módulo de plataforma (`msal_extensions.windows`/`msal_extensions.osx`)
é importado no topo deste arquivo — os dois falham ao importar fora da
própria plataforma (medido na revisão dev-10 do plano: `ctypes.windll`
ausente fora do Windows; `ctypes.CDLL` do Security.framework ausente
fora do macOS). Cada um entra por uma função de carga preguiçosa,
chamada só dentro do `__init__` do adaptador correspondente — e são
essas funções, não as classes da lib, que os testes mockam.
"""

import base64
import binascii


class TokenFormatoAntigoError(Exception):
    """Levantada quando o conteúdo do arquivo não foi protegido por este
    adaptador — token de antes desta fase, em texto puro. Tratada como
    "não autenticado", não como erro do sistema."""


class CofreIndisponivelError(Exception):
    """Levantada quando o cofre do sistema operacional falha de verdade
    (indisponível, negado, corrompido) — distinta de formato antigo.
    Nunca vira "não autenticado" silencioso."""


def _criar_agente_dpapi():
    """Carga preguiçosa — msal_extensions.windows só é importável em
    Windows. Ponto que os testes mockam (não a classe da lib direto)."""
    from msal_extensions.windows import WindowsDataProtectionAgent

    return WindowsDataProtectionAgent()


class AdaptadorWindowsDPAPI:
    """Windows: delega para WindowsDataProtectionAgent.protect()/
    unprotect(). Contrato real da lib (medido, não presumido):
    protect(str) -> bytes (codifica por dentro); unprotect(bytes) -> str
    (decodifica por dentro) — sem encode/decode extra deste adaptador. O
    backend de arquivo grava/lê em modo texto — o adaptador embrulha o
    resultado de protect() em base64 para virar string gravável, e
    decodifica o base64 antes de chamar unprotect(). A validade do
    base64 é o discriminante entre TokenFormatoAntigoError (JSON antigo,
    não é base64 válido) e CofreIndisponivelError (DPAPI real falhando)."""

    def __init__(self) -> None:
        self._agente = _criar_agente_dpapi()

    def encrypt(self, data: str) -> str:
        protegido = self._agente.protect(data)
        return base64.b64encode(protegido).decode("ascii")

    def decrypt(self, data: str) -> str:
        try:
            bruto = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise TokenFormatoAntigoError(
                "arquivo de token não está no formato protegido"
            ) from exc
        try:
            return self._agente.unprotect(bruto)
        except OSError as exc:
            raise CofreIndisponivelError(f"DPAPI falhou: {exc}") from exc


_KEYCHAIN_ITEM_NOT_FOUND = -25300  # msal_extensions.osx.KeychainError.ITEM_NOT_FOUND, medido nesta sessão


def _criar_keychain():
    """Carga preguiçosa — msal_extensions.osx só é importável em macOS.
    Ponto que os testes mockam (não a classe da lib direto)."""
    from msal_extensions.osx import Keychain

    return Keychain()


class AdaptadorMacOSKeychain:
    """macOS: Keychain.set_generic_password()/get_generic_password() são
    chave-valor, não cifrar/decifrar de string — encrypt() grava o
    conteúdo inteiro como senha de um item do Keychain e devolve um
    marcador fixo (nunca o segredo) para o arquivo; decrypt() ignora o
    parâmetro recebido e consulta o Keychain direto. Medido nesta
    sessão: get_generic_password() levanta um OSError (KeychainError na
    lib real, que é subclasse de OSError) com .exit_status == -25300
    quando o item não existe — capturado aqui via OSError genérico e o
    atributo .exit_status, sem importar a classe KeychainError (evita
    precisar carregar msal_extensions.osx só para o except funcionar,
    e deixa o adaptador testável com qualquer OSError equivalente).
    `Keychain()` é instanciada fora de um `with` deliberadamente — medido
    nesta sessão que funciona sem ele (o Security framework cai no
    keychain default do usuário quando a referência interna da lib fica
    nula); não "corrigir" para `with` sem medir de novo, porque isso
    mudaria o escopo de busca do Keychain."""

    _MARCADOR = "scriba:protegido-no-keychain"
    _CONTA = "token"

    def __init__(self, servico: str) -> None:
        self._servico = servico
        self._keychain = _criar_keychain()

    def encrypt(self, data: str) -> str:
        self._keychain.set_generic_password(self._servico, self._CONTA, data)
        return self._MARCADOR

    def decrypt(self, data: str) -> str:
        try:
            return self._keychain.get_generic_password(self._servico, self._CONTA)
        except OSError as exc:
            if getattr(exc, "exit_status", None) == _KEYCHAIN_ITEM_NOT_FOUND:
                return ""
            raise CofreIndisponivelError(f"Keychain falhou: {exc}") from exc
