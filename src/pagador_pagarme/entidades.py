# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_pagarme import cadastro

CODIGO_GATEWAY = 12


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class Cliente(entidades.BaseParaPropriedade):
    _atributos = ['name', 'document_number', 'email', 'address', 'phone']


class Endereco(entidades.BaseParaPropriedade):
    _atributos = ['street', 'neighborhood', 'zipcode', 'street_number', 'complementary']


class Telefone(entidades.BaseParaPropriedade):
    _atributos = ['ddd', 'number']


class Malote(entidades.Malote):
    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self.installments = None
        self.free_installments = None
        self.payment_method = 'credit_card'
        self.capture = 'false'
        self.amount = None
        self.card_hash = None
        self.customer = None
        self.metadata = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self.amount = self.formatador.formata_decimal(pedido.valor_total, em_centavos=True)
        self.card_hash = dados['cartao_hash']
        parcelas = dados.get('cartao_parcelas', 1)
        if dados.get('cartao_parcelas_sem_juros', None) == 'true':
            self.free_installments = parcelas
            self.remove_atributo_da_serializacao('installments')
        else:
            self.installments = parcelas
            self.remove_atributo_da_serializacao('free_installments')
        self.customer = Cliente(
            name=pedido.cliente['nome'],
            document_number=pedido.cliente_documento,
            email=pedido.cliente['email'],
            address=Endereco(
                street=pedido.endereco_cliente['endereco'],
                street_number=pedido.endereco_cliente['numero'],
                complementary=pedido.endereco_cliente['complemento'],
                neighborhood=pedido.endereco_cliente['bairro'],
                zipcode=pedido.endereco_cliente['cep'],
            ),
            phone=Telefone(ddd=pedido.cliente_telefone[0], number=pedido.cliente_telefone[1])
        )
        self.metadata = {
            'pedido_numero': pedido.numero,
            'carrinho': [item.to_dict() for item in pedido.itens]
        }


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):

    def __init__(self, loja_id, codigo_pagamento=None):
        self.campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento)
        self.formulario = cadastro.FormularioPagarMe()
        self.url_card_hash = 'https://pagar.me/assets/pagarme-v2.min.js'
