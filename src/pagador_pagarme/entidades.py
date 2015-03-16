# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_pagarme import cadastro

CODIGO_GATEWAY = 12


class PassosDeEnvio(object):
    pre = 'pre'
    fulfill = 'fulfill'


class TipoDeCartao(object):
    credito = 'credit'
    debito = 'debit'


class TipoEndereco(object):
    cliente = 1
    entrega = 2
    pagamento = 3


class Malote(entidades.Malote):

    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self._passo_atual = PassosDeEnvio.pre
        self._pedido = None
        self._dados = {}

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self._dados = dados
        self._passo_atual = dados['passo']
        self._pedido = pedido
        pedido_pagamento = entidades.PedidoPagamento(self.configuracao.loja_id, pedido.numero, self.configuracao.meio_pagamento.codigo)
        pedido_pagamento.preencher_do_banco()
        if self._passo_atual == PassosDeEnvio.pre:
            pass
        if self._passo_atual == PassosDeEnvio.fulfill:
            pass

    @property
    def _anti_fraude(self):
        return None

    @property
    def _tem_parcelas(self):
        return None

    @property
    def _items(self):
        return []


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    _campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
    _codigo_gateway = CODIGO_GATEWAY

    def __init__(self, loja_id, codigo_pagamento=None):
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento)
        self.preencher_gateway(self._codigo_gateway, self._campos)
        self.formulario = cadastro.FormularioPagarMe()
        self.url_card_hash = ''
