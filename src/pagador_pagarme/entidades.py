# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_pagarme import cadastro

CODIGO_GATEWAY = 12
GATEWAY = 'pagarme'


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
        self.payment_method = 'credit_card'
        self.capture = 'true'
        self.amount = None
        self.card_hash = None
        self.postback_url = None
        self.customer = None
        self.metadata = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        dados_pagamento = pedido.conteudo_json.get(GATEWAY, {})
        if not dados_pagamento:
            raise self.DadosInvalidos(u'O pedido não foi montado corretamente no checkout.')
        self.amount = self.formatador.formata_decimal(pedido.valor_total, em_centavos=True)
        if 'cartao' not in dados_pagamento:
            raise self.DadosInvalidos(u'Os dados do cartão não foram processados corretamente no carrinho')
        if not dados_pagamento['cartao']:
            raise self.DadosInvalidos(u'Os dados do cartão não foram processados corretamente no carrinho')
        self.card_hash = dados_pagamento['cartao']
        parcelas = dados_pagamento.get('parcelas', 1)
        self.installments = parcelas
        url_notificacao = settings.NOTIFICACAO_URL.format(GATEWAY, self.configuracao.loja_id)
        self.postback_url = '{}/notificacao?referencia={}'.format(url_notificacao, pedido.numero)
        cliente_cep = pedido.endereco_cliente.get('cep', '').replace('-', '')
        self.customer = Cliente(
            name=pedido.cliente['nome'],
            document_number=pedido.cliente_documento,
            email=pedido.cliente['email'],
            address=Endereco(
                street=pedido.endereco_cliente['endereco'],
                street_number=pedido.endereco_cliente['numero'],
                complementary=pedido.endereco_cliente['complemento'],
                neighborhood=pedido.endereco_cliente['bairro'],
                zipcode=cliente_cep,
            ),
            phone=Telefone(ddd=pedido.cliente_telefone[0], number=pedido.cliente_telefone[1])
        )
        self.metadata = {
            'pedido_numero': pedido.numero,
            'carrinho': [item.to_dict() for item in pedido.itens]
        }


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):

    def __init__(self, loja_id, codigo_pagamento=None, eh_listagem=False):
        self.campos = ['ativo', 'aplicacao', 'usuario', 'token', 'senha', 'usar_antifraude', 'juros_valor', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'parcelas_sem_juros', 'maximo_parcelas']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento, eh_listagem=eh_listagem)
        self.exige_https = True
        self.url_card_hash = 'https://pagar.me/assets/pagarme-v2.min.js'
        if not self.eh_listagem:
            self.formulario = cadastro.FormularioPagarMe()
