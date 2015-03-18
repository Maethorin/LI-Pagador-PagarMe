# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_pagarme import cadastro

CODIGO_GATEWAY = 12


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class Malote(entidades.Malote):
    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self.installments = None
        self.free_installments = None
        self.payment_method = 'credit_card'
        self.capture = 'false'
        self.amount = None
        self.card_hash = None
        self._passo_atual = PassosDeEnvio.pre
        self._pedido = None
        self._dados = {}

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self._dados = dados
        self._passo_atual = dados['passo']
        self._pedido = pedido
        self.amount = self.formatador.formata_decimal(pedido.valor_total, em_centavos=True)
        if self._passo_atual == PassosDeEnvio.pre:
            self.card_hash = dados['cartao_hash']
        if dados.get('cartao_parcelas_sem_juros', None) == 'true':
            self.free_installments = self._parcelas
            self.remove_atributo_da_serializacao('installments')
        else:
            self.installments = self._parcelas
            self.remove_atributo_da_serializacao('free_installments')
        self.capture = 'false' if self._passo_atual == PassosDeEnvio.pre else 'true'

    @property
    def _anti_fraude(self):
        return None

    @property
    def _parcelas(self):
        return self._dados.get('cartao_parcelas', 1)


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    _campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
    _codigo_gateway = CODIGO_GATEWAY

    def __init__(self, loja_id, codigo_pagamento=None):
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento)
        self.preencher_gateway(self._codigo_gateway, self._campos)
        self.formulario = cadastro.FormularioPagarMe()
        self.url_card_hash = 'https://pagar.me/assets/pagarme-v2.min.js'
